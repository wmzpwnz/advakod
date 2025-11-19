"""
Readiness Middleware - предотвращает обработку запросов к неготовым сервисам
Исправляет M-04: добавляет readiness gating для критических endpoint'ов
"""

import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from typing import Dict, Any, List, Set
import time

logger = logging.getLogger(__name__)


class ReadinessMiddleware(BaseHTTPMiddleware):
    """Middleware для проверки готовности сервисов перед обработкой запросов"""
    
    def __init__(self, app, excluded_paths: Set[str] = None):
        super().__init__(app)
        
        # Исключенные пути (не требуют готовности сервисов)
        self.excluded_paths = excluded_paths or {
            "/",
            "/health",
            "/ready", 
            "/metrics",
            "/docs",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register"
        }
        
        # Критические endpoints, требующие готовности сервисов
        self.critical_endpoints = {
            # Временно отключено для тестирования
            # "/api/v1/chat": ["unified_rag", "unified_llm"],
            # "/api/v1/rag": ["unified_rag"],
            # "/api/v1/generate": ["unified_llm"],
            # "/api/v1/search": ["unified_rag"],
            # "/api/v1/documents": ["unified_rag"]
        }
    
    async def dispatch(self, request: Request, call_next):
        """Проверяет готовность сервисов перед обработкой запроса"""
        
        # Проверяем, нужна ли проверка готовности для этого пути
        path = request.url.path
        
        # Исключаем системные endpoints
        if self._is_excluded_path(path):
            return await call_next(request)
        
        # Определяем требуемые сервисы для endpoint'а
        required_services = self._get_required_services(path)
        
        if required_services:
            # Проверяем готовность сервисов
            readiness_check = self._check_service_readiness(request.app, required_services)
            
            if not readiness_check["ready"]:
                logger.warning(f"Request to {path} blocked - services not ready: {readiness_check['not_ready']}")
                
                return JSONResponse(
                    status_code=503,  # Service Unavailable
                    content={
                        "error": "service_unavailable",
                        "message": "Required services are not ready. Please try again later.",
                        "details": {
                            "path": path,
                            "required_services": required_services,
                            "not_ready_services": readiness_check["not_ready"],
                            "estimated_ready_time": readiness_check.get("estimated_ready_time"),
                            "retry_after": 30  # seconds
                        },
                        "timestamp": time.time()
                    },
                    headers={
                        "Retry-After": "30",  # HTTP стандарт для 503 ответов
                        "X-Service-Status": "unavailable"
                    }
                )
        
        # Сервисы готовы, продолжаем обработку
        response = await call_next(request)
        
        # Добавляем заголовки о статусе сервисов
        if hasattr(request.app.state, "ready"):
            ready_count = sum(request.app.state.ready.values())
            total_count = len(request.app.state.ready)
            response.headers["X-Services-Ready"] = f"{ready_count}/{total_count}"
        
        return response
    
    def _is_excluded_path(self, path: str) -> bool:
        """Проверяет, исключен ли путь из проверки готовности"""
        # Точное совпадение
        if path in self.excluded_paths:
            return True
        
        # Проверяем префиксы для статических файлов и документации
        excluded_prefixes = ["/static/", "/favicon", "/robots.txt"]
        for prefix in excluded_prefixes:
            if path.startswith(prefix):
                return True
        
        return False
    
    def _get_required_services(self, path: str) -> List[str]:
        """Определяет требуемые сервисы для endpoint'а"""
        required_services = []
        
        # Проверяем критические endpoints
        for endpoint_pattern, services in self.critical_endpoints.items():
            if path.startswith(endpoint_pattern):
                required_services.extend(services)
                break
        
        # Удаляем дубликаты
        return list(set(required_services))
    
    def _check_service_readiness(self, app, required_services: List[str]) -> Dict[str, Any]:
        """Проверяет готовность требуемых сервисов"""
        if not hasattr(app.state, "ready"):
            return {
                "ready": False,
                "not_ready": required_services,
                "reason": "app_state_not_initialized"
            }
        
        ready_services = app.state.ready
        not_ready = []
        
        for service in required_services:
            if service not in ready_services or not ready_services[service]:
                not_ready.append(service)
        
        result = {
            "ready": len(not_ready) == 0,
            "not_ready": not_ready,
            "ready_services": [s for s in required_services if s in ready_services and ready_services[s]]
        }
        
        # Добавляем оценку времени готовности
        if not_ready and hasattr(app.state, "models"):
            result["estimated_ready_time"] = self._estimate_ready_time(app.state.models, not_ready)
        
        return result
    
    def _estimate_ready_time(self, models_state: Dict[str, Any], not_ready_services: List[str]) -> int:
        """Оценивает время до готовности сервисов в секундах"""
        max_estimate = 0
        
        for service in not_ready_services:
            if service in models_state:
                model_info = models_state[service]
                
                if model_info.get("error"):
                    # Если есть ошибка, предполагаем длительное время восстановления
                    max_estimate = max(max_estimate, 300)  # 5 минут
                elif model_info.get("ts"):
                    # Если недавно начали загрузку, оцениваем оставшееся время
                    elapsed = time.time() - model_info["ts"]
                    if elapsed < 60:  # Загрузка менее минуты
                        estimated_remaining = max(30, 120 - elapsed)  # 30-120 сек
                        max_estimate = max(max_estimate, estimated_remaining)
                    else:
                        max_estimate = max(max_estimate, 60)  # 1 минута
                else:
                    # Неизвестное состояние
                    max_estimate = max(max_estimate, 60)
        
        return int(max_estimate) if max_estimate > 0 else 30


class ReadinessChecker:
    """Утилитарный класс для проверки готовности сервисов"""
    
    @staticmethod
    def get_service_status(app) -> Dict[str, Any]:
        """Получает детальный статус всех сервисов"""
        if not hasattr(app.state, "ready") or not hasattr(app.state, "models"):
            return {
                "status": "unknown",
                "ready": False,
                "services": {},
                "errors": ["App state not initialized"]
            }
        
        ready_state = app.state.ready
        models_state = app.state.models
        
        services = {}
        errors = []
        
        for service_name in ready_state:
            service_info = {
                "ready": ready_state.get(service_name, False),
                "loaded": False,
                "error": None,
                "load_time": None
            }
            
            if service_name in models_state:
                model_info = models_state[service_name]
                service_info.update({
                    "loaded": model_info.get("loaded", False),
                    "error": model_info.get("error"),
                    "load_time": model_info.get("ts")
                })
                
                if model_info.get("error"):
                    errors.append(f"{service_name}: {model_info['error']}")
            
            services[service_name] = service_info
        
        ready_count = sum(ready_state.values())
        total_count = len(ready_state)
        
        overall_status = "ready" if ready_count == total_count else "partial" if ready_count > 0 else "not_ready"
        
        return {
            "status": overall_status,
            "ready": ready_count == total_count,
            "ready_count": ready_count,
            "total_count": total_count,
            "services": services,
            "errors": errors,
            "timestamp": time.time()
        }
    
    @staticmethod
    def check_endpoint_readiness(app, endpoint_path: str) -> Dict[str, Any]:
        """Проверяет готовность конкретного endpoint'а"""
        middleware = ReadinessMiddleware(app)
        required_services = middleware._get_required_services(endpoint_path)
        
        if not required_services:
            return {
                "ready": True,
                "endpoint": endpoint_path,
                "required_services": [],
                "message": "No service dependencies"
            }
        
        readiness_check = middleware._check_service_readiness(app, required_services)
        
        return {
            "ready": readiness_check["ready"],
            "endpoint": endpoint_path,
            "required_services": required_services,
            "not_ready_services": readiness_check.get("not_ready", []),
            "estimated_ready_time": readiness_check.get("estimated_ready_time"),
            "message": "Ready" if readiness_check["ready"] else "Service dependencies not ready"
        }