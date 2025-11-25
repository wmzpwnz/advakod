"""
Продвинутый rate limiting middleware
"""

import time
import asyncio
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class AdvancedRateLimiter:
    """Продвинутый rate limiter с поддержкой различных стратегий"""
    
    def __init__(self):
        # Хранилище для отслеживания запросов
        self.requests: Dict[str, list] = {}
        self.blocked_ips: Dict[str, float] = {}
        
        # Настройки rate limiting
        self.windows = {
            "login": {"limit": 5, "window": 300},      # 5 попыток за 5 минут
            "admin": {"limit": 3, "window": 300},      # 3 попытки за 5 минут
            "api": {"limit": 100, "window": 60},       # 100 запросов за минуту
            "chat": {"limit": 20, "window": 60},       # 20 сообщений за минуту
            "upload": {"limit": 10, "window": 300},   # 10 загрузок за 5 минут
        }
        
        # Настройки блокировки
        self.max_failed_attempts = 10
        self.block_duration = 3600  # 1 час
    
    def _get_client_ip(self, request: Request) -> str:
        """Получение IP адреса клиента"""
        # Проверяем заголовки прокси
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _get_rate_limit_key(self, request: Request, endpoint_type: str) -> str:
        """Генерация ключа для rate limiting"""
        client_ip = self._get_client_ip(request)
        return f"{endpoint_type}:{client_ip}"
    
    def _is_ip_blocked(self, client_ip: str) -> bool:
        """Проверка, заблокирован ли IP"""
        if client_ip in self.blocked_ips:
            if time.time() < self.blocked_ips[client_ip]:
                return True
            else:
                # Время блокировки истекло
                del self.blocked_ips[client_ip]
        return False
    
    def _block_ip(self, client_ip: str):
        """Блокировка IP адреса"""
        self.blocked_ips[client_ip] = time.time() + self.block_duration
        logger.warning(f"IP {client_ip} blocked for {self.block_duration} seconds")
    
    def _cleanup_old_requests(self, key: str, window: int):
        """Очистка старых запросов"""
        current_time = time.time()
        if key in self.requests:
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if current_time - req_time < window
            ]
    
    def check_rate_limit(self, request: Request, endpoint_type: str) -> bool:
        """Проверка rate limit"""
        client_ip = self._get_client_ip(request)
        
        # Проверяем, заблокирован ли IP
        if self._is_ip_blocked(client_ip):
            return False
        
        # Получаем настройки для типа эндпоинта
        if endpoint_type not in self.windows:
            return True
        
        config = self.windows[endpoint_type]
        key = self._get_rate_limit_key(request, endpoint_type)
        
        # Очищаем старые запросы
        self._cleanup_old_requests(key, config["window"])
        
        # Инициализируем список запросов если нужно
        if key not in self.requests:
            self.requests[key] = []
        
        # Проверяем лимит
        if len(self.requests[key]) >= config["limit"]:
            # Превышен лимит - блокируем IP если это критический эндпоинт
            if endpoint_type in ["login", "admin"]:
                self._block_ip(client_ip)
            return False
        
        # Добавляем текущий запрос
        self.requests[key].append(time.time())
        return True
    
    def get_rate_limit_headers(self, request: Request, endpoint_type: str) -> Dict[str, str]:
        """Получение заголовков rate limit"""
        if endpoint_type not in self.windows:
            return {}
        
        config = self.windows[endpoint_type]
        key = self._get_rate_limit_key(request, endpoint_type)
        
        # Очищаем старые запросы
        self._cleanup_old_requests(key, config["window"])
        
        remaining = max(0, config["limit"] - len(self.requests.get(key, [])))
        reset_time = int(time.time() + config["window"])
        
        return {
            "X-RateLimit-Limit": str(config["limit"]),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
            "X-RateLimit-Window": str(config["window"])
        }


# Глобальный экземпляр
rate_limiter = AdvancedRateLimiter()


def rate_limit_middleware(endpoint_type: str = "api"):
    """Декоратор для rate limiting"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Находим request в аргументах
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # Если request не найден, пропускаем проверку
                return await func(*args, **kwargs)
            
            # Проверяем rate limit
            if not rate_limiter.check_rate_limit(request, endpoint_type):
                client_ip = rate_limiter._get_client_ip(request)
                
                # Логируем превышение лимита
                logger.warning(f"Rate limit exceeded for {endpoint_type} from IP {client_ip}")
                
                # Возвращаем ошибку
                headers = rate_limiter.get_rate_limit_headers(request, endpoint_type)
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": f"Rate limit exceeded for {endpoint_type}",
                        "retry_after": self.windows.get(endpoint_type, {}).get("window", 60)
                    },
                    headers=headers
                )
            
            # Добавляем заголовки rate limit
            response = await func(*args, **kwargs)
            if hasattr(response, 'headers'):
                headers = rate_limiter.get_rate_limit_headers(request, endpoint_type)
                for key, value in headers.items():
                    response.headers[key] = value
            
            return response
        
        return wrapper
    return decorator


def check_rate_limit(request: Request, endpoint_type: str = "api") -> bool:
    """Проверка rate limit для использования в эндпоинтах"""
    return rate_limiter.check_rate_limit(request, endpoint_type)


def get_rate_limit_headers(request: Request, endpoint_type: str = "api") -> Dict[str, str]:
    """Получение заголовков rate limit"""
    return rate_limiter.get_rate_limit_headers(request, endpoint_type)
