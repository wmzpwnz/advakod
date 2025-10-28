import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.monitoring import monitoring_service

logger = logging.getLogger(__name__)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware для автоматического мониторинга HTTP запросов"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Получаем информацию о запросе
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Логируем начало запроса
        logger.info(f"Request started: {request.method} {request.url.path} from {client_ip}")
        
        try:
            # Выполняем запрос
            response = await call_next(request)
            
            # Вычисляем время выполнения
            duration = time.time() - start_time
            
            # Отслеживаем метрики
            monitoring_service.track_request(request, response, duration)
            
            # Логируем успешное завершение
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"status={response.status_code} duration={duration:.3f}s"
            )
            
            return response
            
        except Exception as e:
            # Вычисляем время до ошибки
            duration = time.time() - start_time
            
            # Захватываем исключение в Sentry
            monitoring_service.capture_exception(
                e, 
                context={
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "duration": duration
                }
            )
            
            # Логируем ошибку
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"error={str(e)} duration={duration:.3f}s"
            )
            
            raise
