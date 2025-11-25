import time
import asyncio
from typing import Dict, Optional, Tuple
from functools import wraps
import inspect
from dataclasses import dataclass
from collections import defaultdict, deque
import logging
from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


@dataclass
class RateLimit:
    """Конфигурация ограничения скорости"""
    requests: int  # Количество запросов
    window: int    # Окно времени в секундах
    burst: int     # Максимальный burst (дополнительные запросы)


class RateLimiter:
    """Система ограничения скорости запросов"""
    
    def __init__(self):
        # Хранилище для отслеживания запросов по IP
        self.ip_requests: Dict[str, deque] = defaultdict(deque)
        # Хранилище для отслеживания запросов по пользователю
        self.user_requests: Dict[int, deque] = defaultdict(deque)
        # Конфигурации лимитов (увеличены для разработки)
        self.limits = {
            "default": RateLimit(requests=1000, window=3600, burst=100),  # 1000 req/hour
            "auth": RateLimit(requests=100, window=3600, burst=20),       # 100 auth req/hour
            "chat": RateLimit(requests=500, window=3600, burst=50),       # 500 chat req/hour
            "api": RateLimit(requests=10000, window=3600, burst=500),     # 10000 API req/hour
        }
        # Блокированные IP
        self.blocked_ips: Dict[str, float] = {}
        # Блокированные пользователи
        self.blocked_users: Dict[int, float] = {}
        
    def _cleanup_old_requests(self, requests_queue: deque, window: int):
        """Очистка старых запросов из очереди"""
        current_time = time.time()
        while requests_queue and requests_queue[0] < current_time - window:
            requests_queue.popleft()
    
    def _is_rate_limited(
        self, 
        requests_queue: deque, 
        limit: RateLimit
    ) -> Tuple[bool, int, int]:
        """
        Проверка превышения лимита
        
        Returns:
            (is_limited, remaining_requests, reset_time)
        """
        current_time = time.time()
        
        # Очищаем старые запросы
        self._cleanup_old_requests(requests_queue, limit.window)
        
        # Проверяем лимит
        if len(requests_queue) >= limit.requests:
            # Проверяем burst
            if len(requests_queue) >= limit.requests + limit.burst:
                return True, 0, int(requests_queue[0] + limit.window)
            else:
                # В режиме burst - разрешаем, но с предупреждением
                pass
        
        # Добавляем текущий запрос
        requests_queue.append(current_time)
        
        # Вычисляем оставшиеся запросы
        remaining = max(0, limit.requests - len(requests_queue))
        reset_time = int(current_time + limit.window)
        
        return False, remaining, reset_time
    
    def check_rate_limit(
        self, 
        identifier: str, 
        limit_type: str = "default",
        is_user: bool = False
    ) -> Tuple[bool, int, int]:
        """
        Проверка ограничения скорости
        
        Args:
            identifier: IP адрес или ID пользователя
            limit_type: Тип лимита (default, auth, chat, api)
            is_user: True если это ID пользователя, False если IP
            
        Returns:
            (is_limited, remaining_requests, reset_time)
        """
        limit = self.limits.get(limit_type, self.limits["default"])
        
        if is_user:
            user_id = int(identifier)
            # Проверяем блокировку пользователя
            if user_id in self.blocked_users:
                if time.time() < self.blocked_users[user_id]:
                    return True, 0, int(self.blocked_users[user_id])
                else:
                    del self.blocked_users[user_id]
            
            requests_queue = self.user_requests[user_id]
        else:
            # Проверяем блокировку IP
            if identifier in self.blocked_ips:
                if time.time() < self.blocked_ips[identifier]:
                    return True, 0, int(self.blocked_ips[identifier])
                else:
                    del self.blocked_ips[identifier]
            
            requests_queue = self.ip_requests[identifier]
        
        is_limited, remaining, reset_time = self._is_rate_limited(requests_queue, limit)
        
        # Если превышен лимит + burst, блокируем на час
        if is_limited and len(requests_queue) > limit.requests + limit.burst:
            block_until = time.time() + 3600  # Блокировка на час
            if is_user:
                self.blocked_users[int(identifier)] = block_until
            else:
                self.blocked_ips[identifier] = block_until
            
            logger.warning(f"Rate limit exceeded for {'user' if is_user else 'IP'} {identifier}")
        
        return is_limited, remaining, reset_time
    
    def get_rate_limit_info(
        self, 
        identifier: str, 
        limit_type: str = "default",
        is_user: bool = False
    ) -> Dict[str, any]:
        """Получение информации о текущих лимитах"""
        limit = self.limits.get(limit_type, self.limits["default"])
        
        if is_user:
            requests_queue = self.user_requests.get(int(identifier), deque())
        else:
            requests_queue = self.ip_requests.get(identifier, deque())
        
        self._cleanup_old_requests(requests_queue, limit.window)
        
        return {
            "limit": limit.requests,
            "remaining": max(0, limit.requests - len(requests_queue)),
            "reset_time": int(time.time() + limit.window),
            "window": limit.window,
            "burst": limit.burst
        }
    
    def reset_rate_limit(self, identifier: str, is_user: bool = False):
        """Сброс лимитов для идентификатора"""
        if is_user:
            user_id = int(identifier)
            if user_id in self.user_requests:
                del self.user_requests[user_id]
            if user_id in self.blocked_users:
                del self.blocked_users[user_id]
        else:
            if identifier in self.ip_requests:
                del self.ip_requests[identifier]
            if identifier in self.blocked_ips:
                del self.blocked_ips[identifier]
    
    def update_limit_config(self, limit_type: str, requests: int, window: int, burst: int):
        """Обновление конфигурации лимитов"""
        self.limits[limit_type] = RateLimit(requests=requests, window=window, burst=burst)
        logger.info(f"Updated rate limit config for {limit_type}: {requests} requests per {window}s")


# Глобальный экземпляр rate limiter
rate_limiter = RateLimiter()


def rate_limit_middleware(limit_type: str = "default"):
    """Middleware для ограничения скорости запросов"""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # Получаем IP адрес
            client_ip = request.client.host if request.client else "unknown"
            
            # Проверяем лимит по IP
            is_limited, remaining, reset_time = rate_limiter.check_rate_limit(
                client_ip, limit_type, is_user=False
            )
            
            if is_limited:
                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Rate limit exceeded",
                        "limit_type": limit_type,
                        "reset_time": reset_time
                    },
                    headers={
                        "X-RateLimit-Limit": str(rate_limiter.limits[limit_type].requests),
                        "X-RateLimit-Remaining": str(remaining),
                        "X-RateLimit-Reset": str(reset_time),
                        "Retry-After": str(reset_time - int(time.time()))
                    }
                )
                return response
            
            # Добавляем заголовки с информацией о лимитах
            response = await func(request, *args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers["X-RateLimit-Limit"] = str(rate_limiter.limits[limit_type].requests)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Reset"] = str(reset_time)
            
            return response
        return wrapper
    return decorator


def user_rate_limit(limit_type: str = "default"):
    """Декоратор для ограничения скорости по пользователю"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Ищем current_user в аргументах
            current_user = None
            for arg in args:
                if hasattr(arg, 'id'):  # Предполагаем, что это User объект
                    current_user = arg
                    break
            
            if current_user:
                user_id = str(current_user.id)
                is_limited, remaining, reset_time = rate_limiter.check_rate_limit(
                    user_id, limit_type, is_user=True
                )
                
                if is_limited:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "message": "User rate limit exceeded",
                            "limit_type": limit_type,
                            "reset_time": reset_time
                        }
                    )
            
            return await func(*args, **kwargs)
        # Важно: сохраняем оригинальную сигнатуру для корректной работы FastAPI
        wrapper.__signature__ = inspect.signature(func)
        return wrapper
    return decorator
