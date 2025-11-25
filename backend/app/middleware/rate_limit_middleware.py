from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time
import logging
from typing import Dict, List
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class SimpleRateLimiter:
    """Простой rate limiter в памяти для разработки"""
    
    def __init__(self):
        # Хранилище запросов: {client_ip: [(timestamp, endpoint), ...]}
        self.requests: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Лимиты для разных эндпоинтов (requests per minute)
        self.limits = {
            "/api/v1/auth/login": 10,      # 10 попыток входа в минуту
            "/api/v1/auth/login-email": 10,
            "/api/v1/auth/register": 10,   # 10 регистраций в минуту (для разработки)
            "/api/v1/chat/message": 20,   # 20 сообщений в минуту
            "/api/v1/chat/message/stream": 20,
            "/api/v1/admin/": 30,         # 30 админ запросов в минуту
            "default": 60                 # 60 запросов в минуту по умолчанию
        }
    
    def get_client_ip(self, request: Request) -> str:
        """Получаем IP клиента"""
        # Проверяем заголовки прокси
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
            
        # Fallback на client host
        return request.client.host if request.client else "unknown"
    
    def get_limit_for_endpoint(self, path: str) -> int:
        """Получаем лимит для эндпоинта"""
        # Точное совпадение
        if path in self.limits:
            return self.limits[path]
        
        # Проверяем префиксы (для админки)
        for endpoint_prefix, limit in self.limits.items():
            if endpoint_prefix.endswith("/") and path.startswith(endpoint_prefix):
                return limit
        
        return self.limits["default"]
    
    def is_rate_limited(self, request: Request) -> bool:
        """Проверяем, превышен ли лимит"""
        client_ip = self.get_client_ip(request)
        path = request.url.path
        current_time = time.time()
        
        # Получаем лимит для данного эндпоинта
        limit = self.get_limit_for_endpoint(path)
        
        # Очищаем старые записи (старше 1 минуты)
        client_requests = self.requests[client_ip]
        while client_requests and current_time - client_requests[0][0] > 60:
            client_requests.popleft()
        
        # Подсчитываем запросы к данному эндпоинту за последнюю минуту
        endpoint_requests = sum(1 for timestamp, endpoint in client_requests 
                              if endpoint == path and current_time - timestamp <= 60)
        
        # Проверяем лимит
        if endpoint_requests >= limit:
            logger.warning(f"Rate limit exceeded for {client_ip} on {path}: {endpoint_requests}/{limit}")
            return True
        
        # Добавляем текущий запрос
        client_requests.append((current_time, path))
        return False


# Глобальный экземпляр rate limiter
rate_limiter = SimpleRateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    """Middleware для проверки rate limiting"""
    
    # Пропускаем статические файлы и некритичные эндпоинты
    if (request.url.path.startswith("/static/") or 
        request.url.path.startswith("/docs") or
        request.url.path.startswith("/redoc") or
        request.url.path == "/"):
        return await call_next(request)
    
    # Проверяем rate limit
    if rate_limiter.is_rate_limited(request):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Слишком много запросов. Попробуйте позже.",
                "error_code": "RATE_LIMIT_EXCEEDED",
                "retry_after": 60
            },
            headers={"Retry-After": "60"}
        )
    
    # Продолжаем обработку запроса
    response = await call_next(request)
    return response