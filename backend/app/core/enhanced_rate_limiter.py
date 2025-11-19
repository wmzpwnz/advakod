"""
Улучшенный rate limiter с поддержкой различных стратегий
"""
import time
import asyncio
import logging
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, deque
from ..core.enhanced_logging import security_logger, SecurityEvent, LogLevel


class RateLimitStrategy(Enum):
    """Стратегии rate limiting"""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class RateLimitConfig:
    """Конфигурация rate limiting"""
    max_requests: int
    window_seconds: int
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    burst_limit: Optional[int] = None
    penalty_seconds: int = 60


class RateLimitEntry:
    """Запись rate limiting"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests = deque()
        self.tokens = config.max_requests
        self.last_refill = time.time()
        self.penalty_until = 0
        self.violation_count = 0
    
    def is_penalized(self) -> bool:
        """Проверяет, находится ли клиент под штрафом"""
        return time.time() < self.penalty_until
    
    def add_penalty(self):
        """Добавляет штраф за превышение лимита"""
        self.penalty_until = time.time() + self.config.penalty_seconds
        self.violation_count += 1
    
    def is_allowed(self) -> bool:
        """Проверяет, разрешен ли запрос"""
        current_time = time.time()
        
        # Проверяем штраф
        if self.is_penalized():
            return False
        
        # Очищаем старые запросы
        if self.config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            while self.requests and self.requests[0] <= current_time - self.config.window_seconds:
                self.requests.popleft()
        
        # Проверяем лимит
        if self.config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            if len(self.requests) >= self.config.max_requests:
                self.add_penalty()
                return False
            self.requests.append(current_time)
            return True
        
        elif self.config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            # Пополняем токены
            time_passed = current_time - self.last_refill
            tokens_to_add = time_passed * (self.config.max_requests / self.config.window_seconds)
            self.tokens = min(self.config.max_requests, self.tokens + tokens_to_add)
            self.last_refill = current_time
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            else:
                self.add_penalty()
                return False
        
        return True


class EnhancedRateLimiter:
    """Улучшенный rate limiter"""
    
    def __init__(self):
        self.entries: Dict[str, RateLimitEntry] = {}
        self.global_limits: Dict[str, RateLimitConfig] = {}
        self.endpoint_limits: Dict[str, RateLimitConfig] = {}
        self.user_limits: Dict[int, RateLimitConfig] = {}
        self.logger = logging.getLogger(__name__)
        
        # Настройка глобальных лимитов
        self._setup_default_limits()
    
    def _setup_default_limits(self):
        """Настройка лимитов по умолчанию"""
        # Глобальные лимиты
        self.global_limits = {
            "default": RateLimitConfig(100, 60),  # 100 запросов в минуту
            "strict": RateLimitConfig(20, 60),    # 20 запросов в минуту
            "admin": RateLimitConfig(200, 60),    # 200 запросов в минуту для админов
        }
        
        # Лимиты для эндпоинтов
        self.endpoint_limits = {
            "/api/v1/auth/login": RateLimitConfig(5, 60),      # 5 попыток входа в минуту
            "/api/v1/auth/register": RateLimitConfig(3, 300),  # 3 регистрации в 5 минут
            "/api/v1/chat/message": RateLimitConfig(30, 60),   # 30 сообщений в минуту
            "/api/v1/admin": RateLimitConfig(50, 60),          # 50 админских запросов в минуту
            "/api/v1/rag": RateLimitConfig(20, 60),            # 20 RAG запросов в минуту
        }
        
        # Лимиты для пользователей
        self.user_limits = {
            "free": RateLimitConfig(50, 60),      # 50 запросов в минуту для бесплатных
            "premium": RateLimitConfig(200, 60),  # 200 запросов в минуту для премиум
            "admin": RateLimitConfig(500, 60),    # 500 запросов в минуту для админов
        }
    
    def _get_client_key(self, ip_address: str, user_id: Optional[int] = None) -> str:
        """Получает ключ клиента"""
        if user_id:
            return f"user:{user_id}"
        return f"ip:{ip_address}"
    
    def _get_rate_limit_config(
        self,
        endpoint: str,
        user_type: str = "free",
        is_admin: bool = False
    ) -> RateLimitConfig:
        """Получает конфигурацию rate limiting"""
        # Проверяем лимиты для эндпоинта
        if endpoint in self.endpoint_limits:
            return self.endpoint_limits[endpoint]
        
        # Проверяем лимиты для типа пользователя
        if is_admin:
            return self.user_limits.get("admin", self.global_limits["admin"])
        
        if user_type in self.user_limits:
            return self.user_limits[user_type]
        
        # Возвращаем глобальный лимит
        return self.global_limits["default"]
    
    def is_allowed(
        self,
        ip_address: str,
        endpoint: str,
        user_id: Optional[int] = None,
        user_type: str = "free",
        is_admin: bool = False
    ) -> bool:
        """
        Проверяет, разрешен ли запрос
        
        Args:
            ip_address: IP адрес клиента
            endpoint: Эндпоинт
            user_id: ID пользователя
            user_type: Тип пользователя
            is_admin: Является ли админом
            
        Returns:
            True если запрос разрешен
        """
        try:
            client_key = self._get_client_key(ip_address, user_id)
            config = self._get_rate_limit_config(endpoint, user_type, is_admin)
            
            # Получаем или создаем запись
            if client_key not in self.entries:
                self.entries[client_key] = RateLimitEntry(config)
            
            entry = self.entries[client_key]
            
            # Проверяем разрешение
            if entry.is_allowed():
                return True
            else:
                # Логируем превышение лимита
                security_logger.log_security_event(
                    event=SecurityEvent.RATE_LIMIT_EXCEEDED,
                    user_id=user_id,
                    ip_address=ip_address,
                    details={
                        "endpoint": endpoint,
                        "user_type": user_type,
                        "is_admin": is_admin,
                        "violation_count": entry.violation_count,
                        "penalty_until": entry.penalty_until
                    },
                    severity=LogLevel.WARNING
                )
                return False
                
        except Exception as e:
            self.logger.error(f"Rate limiting error: {e}")
            return True  # В случае ошибки разрешаем запрос
    
    def get_remaining_requests(
        self,
        ip_address: str,
        endpoint: str,
        user_id: Optional[int] = None,
        user_type: str = "free",
        is_admin: bool = False
    ) -> int:
        """
        Получает количество оставшихся запросов
        
        Args:
            ip_address: IP адрес клиента
            endpoint: Эндпоинт
            user_id: ID пользователя
            user_type: Тип пользователя
            is_admin: Является ли админом
            
        Returns:
            Количество оставшихся запросов
        """
        try:
            client_key = self._get_client_key(ip_address, user_id)
            config = self._get_rate_limit_config(endpoint, user_type, is_admin)
            
            if client_key not in self.entries:
                return config.max_requests
            
            entry = self.entries[client_key]
            
            if entry.is_penalized():
                return 0
            
            if config.strategy == RateLimitStrategy.SLIDING_WINDOW:
                return max(0, config.max_requests - len(entry.requests))
            elif config.strategy == RateLimitStrategy.TOKEN_BUCKET:
                return max(0, int(entry.tokens))
            
            return config.max_requests
            
        except Exception as e:
            self.logger.error(f"Error getting remaining requests: {e}")
            return 0
    
    def get_reset_time(
        self,
        ip_address: str,
        endpoint: str,
        user_id: Optional[int] = None,
        user_type: str = "free",
        is_admin: bool = False
    ) -> float:
        """
        Получает время сброса лимита
        
        Args:
            ip_address: IP адрес клиента
            endpoint: Эндпоинт
            user_id: ID пользователя
            user_type: Тип пользователя
            is_admin: Является ли админом
            
        Returns:
            Время сброса лимита в секундах
        """
        try:
            client_key = self._get_client_key(ip_address, user_id)
            config = self._get_rate_limit_config(endpoint, user_type, is_admin)
            
            if client_key not in self.entries:
                return 0
            
            entry = self.entries[client_key]
            
            if entry.is_penalized():
                return entry.penalty_until - time.time()
            
            if config.strategy == RateLimitStrategy.SLIDING_WINDOW:
                if entry.requests:
                    return entry.requests[0] + config.window_seconds - time.time()
                return 0
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Error getting reset time: {e}")
            return 0
    
    def cleanup_old_entries(self, max_age_seconds: int = 3600):
        """Очищает старые записи"""
        try:
            current_time = time.time()
            keys_to_remove = []
            
            for key, entry in self.entries.items():
                if (current_time - entry.last_refill > max_age_seconds and 
                    not entry.is_penalized()):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.entries[key]
                
            self.logger.info(f"Cleaned up {len(keys_to_remove)} old rate limit entries")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old entries: {e}")
    
    def reset_penalty(self, ip_address: str, user_id: Optional[int] = None):
        """Сбрасывает штраф для клиента"""
        try:
            client_key = self._get_client_key(ip_address, user_id)
            if client_key in self.entries:
                self.entries[client_key].penalty_until = 0
                self.entries[client_key].violation_count = 0
                self.logger.info(f"Reset penalty for {client_key}")
                
        except Exception as e:
            self.logger.error(f"Error resetting penalty: {e}")


# Глобальный экземпляр rate limiter
enhanced_rate_limiter = EnhancedRateLimiter()
