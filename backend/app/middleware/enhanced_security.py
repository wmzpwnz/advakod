"""
Улучшенный middleware для безопасности
"""
import re
import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..core.enhanced_logging import security_logger, SecurityEvent, LogLevel


class XSSProtectionMiddleware(BaseHTTPMiddleware):
    """Middleware для защиты от XSS атак"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)
        
        # Паттерны для обнаружения XSS
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'<style[^>]*>.*?</style>',
            r'expression\s*\(',
            r'url\s*\(',
            r'@import',
            r'<[^>]*script[^>]*>',
            r'<[^>]*on\w+[^>]*>',
        ]
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.xss_patterns]
    
    async def dispatch(self, request: Request, call_next):
        """Обработка запроса"""
        try:
            # Проверяем URL на XSS
            if self._detect_xss(str(request.url)):
                await self._log_xss_attempt(request, "URL")
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid request", "message": "Suspicious content detected"}
                )
            
            # Проверяем заголовки на XSS
            for header_name, header_value in request.headers.items():
                if self._detect_xss(header_value):
                    await self._log_xss_attempt(request, f"Header: {header_name}")
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid request", "message": "Suspicious content detected"}
                    )
            
            # Выполняем запрос
            response = await call_next(request)
            
            # Добавляем заголовки безопасности
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            
            return response
            
        except Exception as e:
            self.logger.error(f"XSS protection error: {e}")
            return await call_next(request)
    
    def _detect_xss(self, content: str) -> bool:
        """Обнаруживает XSS атаки в контенте"""
        try:
            for pattern in self.compiled_patterns:
                if pattern.search(content):
                    return True
            return False
        except Exception:
            return False
    
    async def _log_xss_attempt(self, request: Request, location: str):
        """Логирует попытку XSS атаки"""
        security_logger.log_security_event(
            event=SecurityEvent.XSS_ATTEMPT,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent"),
            details={
                "location": location,
                "url": str(request.url),
                "method": request.method
            },
            severity=LogLevel.WARNING
        )


class SQLInjectionProtectionMiddleware(BaseHTTPMiddleware):
    """Middleware для защиты от SQL инъекций"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)
        
        # Паттерны для обнаружения SQL инъекций
        self.sql_patterns = [
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+set',
            r'alter\s+table',
            r'create\s+table',
            r'exec\s*\(',
            r'execute\s*\(',
            r'sp_',
            r'xp_',
            r'--',
            r'/\*.*\*/',
            r';\s*drop',
            r';\s*delete',
            r';\s*insert',
            r';\s*update',
            r';\s*alter',
            r';\s*create',
            r';\s*exec',
            r';\s*execute',
            r';\s*sp_',
            r';\s*xp_',
            r';\s*--',
            r';\s*/\*',
            r';\s*union',
            r';\s*drop',
            r';\s*delete',
            r';\s*insert',
            r';\s*update',
            r';\s*alter',
            r';\s*create',
            r';\s*exec',
            r';\s*execute',
            r';\s*sp_',
            r';\s*xp_',
            r';\s*--',
            r';\s*/\*',
            r';\s*union',
        ]
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.sql_patterns]
    
    async def dispatch(self, request: Request, call_next):
        """Обработка запроса"""
        try:
            # Проверяем URL на SQL инъекции
            if self._detect_sql_injection(str(request.url)):
                await self._log_sql_injection_attempt(request, "URL")
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid request", "message": "Suspicious content detected"}
                )
            
            # Проверяем query параметры
            for param_name, param_value in request.query_params.items():
                if self._detect_sql_injection(param_value):
                    await self._log_sql_injection_attempt(request, f"Query param: {param_name}")
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid request", "message": "Suspicious content detected"}
                    )
            
            # Выполняем запрос
            response = await call_next(request)
            return response
            
        except Exception as e:
            self.logger.error(f"SQL injection protection error: {e}")
            return await call_next(request)
    
    def _detect_sql_injection(self, content: str) -> bool:
        """Обнаруживает SQL инъекции в контенте"""
        try:
            for pattern in self.compiled_patterns:
                if pattern.search(content):
                    return True
            return False
        except Exception:
            return False
    
    async def _log_sql_injection_attempt(self, request: Request, location: str):
        """Логирует попытку SQL инъекции"""
        security_logger.log_security_event(
            event=SecurityEvent.SQL_INJECTION_ATTEMPT,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent"),
            details={
                "location": location,
                "url": str(request.url),
                "method": request.method
            },
            severity=LogLevel.WARNING
        )


class EnhancedSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Улучшенный middleware для заголовков безопасности"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)
    
    async def dispatch(self, request: Request, call_next):
        """Обработка запроса"""
        try:
            response = await call_next(request)
            
            # Добавляем заголовки безопасности
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' ws: wss:; "
                "frame-ancestors 'none';"
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Security headers error: {e}")
            return await call_next(request)


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Middleware для валидации входных данных"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)
        
        # Максимальные размеры
        self.max_content_length = 10 * 1024 * 1024  # 10MB
        self.max_query_length = 2048
        self.max_header_length = 8192
    
    async def dispatch(self, request: Request, call_next):
        """Обработка запроса"""
        try:
            # Проверяем размер контента
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_content_length:
                return JSONResponse(
                    status_code=413,
                    content={"error": "Payload too large", "message": "Request body too large"}
                )
            
            # Проверяем длину URL
            if len(str(request.url)) > self.max_query_length:
                return JSONResponse(
                    status_code=414,
                    content={"error": "URI too long", "message": "Request URI too long"}
                )
            
            # Проверяем заголовки
            for header_name, header_value in request.headers.items():
                if len(header_value) > self.max_header_length:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Bad request", "message": "Header too long"}
                    )
            
            # Выполняем запрос
            response = await call_next(request)
            return response
            
        except Exception as e:
            self.logger.error(f"Input validation error: {e}")
            return await call_next(request)
