"""
Middleware для безопасности - заголовки, XSS защита, CSRF
"""

import re
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware для добавления заголовков безопасности"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Заголовки безопасности
        security_headers = {
            # Защита от XSS
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' ws: wss:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
            
            # Strict Transport Security (только для HTTPS)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            
            # Permissions Policy
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "speaker=()"
            ),
            
            # Дополнительные заголовки
            "X-Permitted-Cross-Domain-Policies": "none",
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin"
        }
        
        # Добавляем заголовки
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response


class XSSProtectionMiddleware(BaseHTTPMiddleware):
    """Middleware для защиты от XSS атак"""
    
    def __init__(self, app):
        super().__init__(app)
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
            r'vbscript:',
            r'data:text/html',
            r'data:application/javascript'
        ]
        
        # Компилируем регулярные выражения
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in self.xss_patterns]
    
    def detect_xss(self, content: str) -> bool:
        """Обнаружение XSS атак в контенте"""
        if not content:
            return False
        
        for pattern in self.compiled_patterns:
            if pattern.search(content):
                return True
        
        return False
    
    def sanitize_content(self, content: str) -> str:
        """Очистка контента от потенциально опасных элементов"""
        if not content:
            return content
        
        # Удаляем HTML теги
        content = re.sub(r'<[^>]+>', '', content)
        
        # Удаляем JavaScript события
        content = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)
        
        # Удаляем javascript: и data: URL
        content = re.sub(r'javascript:', '', content, flags=re.IGNORECASE)
        content = re.sub(r'data:text/html', '', content, flags=re.IGNORECASE)
        content = re.sub(r'data:application/javascript', '', content, flags=re.IGNORECASE)
        
        # Удаляем vbscript:
        content = re.sub(r'vbscript:', '', content, flags=re.IGNORECASE)
        
        return content
    
    def is_exempt_path(self, path: str) -> bool:
        """Проверяет, освобожден ли путь от XSS проверки"""
        exempt_paths = [
            "/api/v1/simple/chat",  # Простой чат
            "/api/v1/chat",         # Основной чат
            "/api/v1/rag",          # RAG запросы
            "/docs",                # Документация
            "/openapi.json"         # OpenAPI схема
        ]
        return any(path.startswith(exempt) for exempt in exempt_paths)
    
    async def dispatch(self, request: Request, call_next):
        # Пропускаем освобожденные пути
        if self.is_exempt_path(request.url.path):
            response = await call_next(request)
            return response
        
        # Проверяем POST/PUT/PATCH запросы на XSS
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Получаем тело запроса
                body = await request.body()
                if body:
                    content = body.decode('utf-8', errors='ignore')
                    
                    # Проверяем на XSS
                    if self.detect_xss(content):
                        logger.warning(f"XSS attack detected from IP {request.client.host}")
                        return JSONResponse(
                            status_code=400,
                            content={"detail": "Potentially malicious content detected"}
                        )
                    
                    # Очищаем контент
                    sanitized_content = self.sanitize_content(content)
                    if sanitized_content != content:
                        logger.info(f"Content sanitized for IP {request.client.host}")
            
            except Exception as e:
                logger.error(f"Error in XSS protection: {e}")
        
        response = await call_next(request)
        return response


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """Middleware для защиты от CSRF атак"""
    
    def __init__(self, app):
        super().__init__(app)
        self.exempt_paths = [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/docs",
            "/openapi.json"
        ]
    
    def is_exempt_path(self, path: str) -> bool:
        """Проверка, освобожден ли путь от CSRF проверки"""
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return True
        return False
    
    def generate_csrf_token(self) -> str:
        """Генерация CSRF токена"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def verify_csrf_token(self, request: Request) -> bool:
        """Проверка CSRF токена"""
        # Получаем токен из заголовка
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            return False
        
        # Получаем токен из сессии (в реальном приложении)
        # Здесь упрощенная проверка
        session_token = request.cookies.get("csrf_token")
        if not session_token:
            return False
        
        return csrf_token == session_token
    
    async def dispatch(self, request: Request, call_next):
        # Проверяем только POST/PUT/PATCH/DELETE запросы
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            # Пропускаем освобожденные пути
            if self.is_exempt_path(request.url.path):
                response = await call_next(request)
                return response
            
            # Проверяем CSRF токен
            if not self.verify_csrf_token(request):
                logger.warning(f"CSRF attack detected from IP {request.client.host}")
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF token validation failed"}
                )
        
        response = await call_next(request)
        
        # Добавляем CSRF токен в куки для новых сессий
        if not request.cookies.get("csrf_token"):
            csrf_token = self.generate_csrf_token()
            response.set_cookie(
                "csrf_token",
                csrf_token,
                httponly=True,
                secure=True,
                samesite="strict",
                max_age=3600
            )
        
        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Middleware для валидации входных данных"""
    
    def __init__(self, app):
        super().__init__(app)
        # Максимальные размеры
        self.max_content_length = 10 * 1024 * 1024  # 10MB
        self.max_header_size = 8192  # 8KB
        self.max_url_length = 2048  # 2KB
    
    async def dispatch(self, request: Request, call_next):
        # Проверяем размер заголовков
        total_header_size = sum(len(k) + len(v) for k, v in request.headers.items())
        if total_header_size > self.max_header_size:
            logger.warning(f"Oversized headers from IP {request.client.host}")
            return JSONResponse(
                status_code=400,
                content={"detail": "Request headers too large"}
            )
        
        # Проверяем длину URL
        if len(str(request.url)) > self.max_url_length:
            logger.warning(f"Oversized URL from IP {request.client.host}")
            return JSONResponse(
                status_code=400,
                content={"detail": "Request URL too long"}
            )
        
        # Проверяем размер тела запроса
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_content_length:
                logger.warning(f"Oversized request body from IP {request.client.host}")
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request body too large"}
                )
        
        response = await call_next(request)
        return response
