from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import asyncio
import time
import sys
import os
import json
from typing import Dict, Any

from app.core.config import settings
from app.core.database import init_db
from app.api import api_router
from app.api.websocket import router as websocket_router
from app.api.lora_training import router as lora_training_router
from app.api.analytics import router as analytics_router
# from app.api.advanced_analytics import router as advanced_analytics_router  # Temporarily disabled - missing pandas
from app.api.enhanced_chat import router as enhanced_chat_router
from app.core.cache import cache_service
from app.core.enhanced_logging import get_logger, SecurityEvent, LogLevel
from app.core.enhanced_rate_limiter import enhanced_rate_limiter
# Новые унифицированные сервисы
from app.services.unified_llm_service import unified_llm_service
from app.services.unified_rag_service import unified_rag_service
from app.services.service_manager import service_manager
from app.services.unified_monitoring_service import unified_monitoring_service

# Legacy сервисы (для совместимости) - будут удалены в следующих версиях
from app.services.embeddings_service import embeddings_service
from app.services.enhanced_embeddings_service import enhanced_embeddings_service
from app.services.vector_store_service import vector_store_service

# Импорты для performance optimizer и rate limiter
from app.core.advanced_performance_optimizer import performance_optimizer
from app.middleware.ml_rate_limit import MLRateLimiter

# Prometheus метрики
try:
    from app.core.prometheus_metrics import PrometheusMetrics
except ImportError:
    # Fallback для случаев когда prometheus_metrics недоступен
    class PrometheusMetrics:
        def __init__(self):
            pass
        def record_http_request(self, *args, **kwargs):
            pass
        def record_ai_inference(self, *args, **kwargs):
            pass
        def record_error(self, *args, **kwargs):
            pass

# Настройка улучшенного логирования
logger = get_logger(__name__)

# Инициализация Prometheus метрик
try:
    prometheus_metrics = PrometheusMetrics()
except:
    # Fallback для случаев когда prometheus_metrics недоступен
    class MockPrometheusMetrics:
        def record_http_request(self, *args, **kwargs):
            pass
        def record_ai_inference(self, *args, **kwargs):
            pass
        def record_error(self, *args, **kwargs):
            pass
    prometheus_metrics = MockPrometheusMetrics()

# Lifespan context manager для инициализации
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info("🚀 Starting АДВАКОД - ИИ-Юрист для РФ")
    
    # Инициализация базы данных
    try:
        init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.log_error(e, {"service": "database"})
        logger.error(f"Database initialization failed: {e}")
    
    try:
        await cache_service.initialize()
        logger.info("✅ Cache service initialized")
    except Exception as e:
        logger.log_error(e, {"service": "cache"})
    
    # Новая унифицированная система управления сервисами
    app.state.service_manager = service_manager
    app.state.unified_services = {
        "llm": unified_llm_service,
        "rag": unified_rag_service,
        "monitoring": unified_monitoring_service
    }
    
    # Инициализируем унифицированную систему AI-сервисов
    logger.info("🚀 Initializing unified AI services system...")
    
    try:
        # Инициализируем ServiceManager - он управляет всеми AI-сервисами
        success = await service_manager.initialize_services()
        
        if success:
            logger.info("✅ Unified AI services initialized successfully")
            
            # Получаем статус сервисов для app.state
            system_health = service_manager.get_service_status()
            app.state.system_health = system_health
            
            # Инициализируем систему мониторинга
            await unified_monitoring_service.initialize()
            logger.info("✅ Monitoring system initialized")
            
            # Инициализируем админ-панель метрики коллектор
            # await admin_metrics_collector.start() # УДАЛЕНО - не определен
            logger.info("✅ Admin panel metrics collector initialization skipped")
            
            # Инициализируем систему алертов
            from app.services.alert_service import alert_evaluation_service
            await alert_evaluation_service.start()
            logger.info("✅ Alert evaluation service started")
            
        else:
            logger.error("❌ Failed to initialize some AI services")
            
    except Exception as e:
        logger.error(f"❌ Critical error during AI services initialization: {e}")
    
    # Инициализируем оптимизаторы производительности (legacy)
    try:
        logger.info("🚀 Initializing performance optimizers...")
        await performance_optimizer.start_background_optimizations()
        logger.info("✅ Performance optimizers initialized")
    except Exception as e:
        logger.error(f"Performance optimizer initialization failed: {e}")
    
    # Инициализируем cleanup task для rate limiter (legacy)
    try:
        # Rate limiter cleanup - используем существующий ml_rate_limiter
        ml_rate_limiter_instance = MLRateLimiter()
        await ml_rate_limiter_instance.initialize_cleanup()
        logger.info("✅ Rate limiter cleanup task initialized")
    except Exception as e:
        logger.error(f"Rate limiter cleanup initialization failed: {e}")
    
    # Принудительная инициализация legacy сервисов для совместимости
    try:
        logger.info("🚀 Initializing legacy services for compatibility...")
        
        # Инициализируем embeddings
        from app.services.embeddings_service import embeddings_service
        embeddings_service.load_model()
        logger.info("✅ Embeddings service initialized")
        
        # Инициализируем vector store
        from app.services.vector_store_service import vector_store_service
        vector_store_service.initialize()
        logger.info("✅ Vector store service initialized")
        
        # Инициализируем unified LLM
        await unified_llm_service.ensure_model_loaded_async()
        logger.info("✅ Unified LLM service initialized")
        
        # Проверяем RAG
        from app.services.rag_service import rag_service
        rag_ready = rag_service.is_ready()
        logger.info(f"✅ RAG service ready: {rag_ready}")
        
    except Exception as e:
        logger.error(f"❌ Legacy services initialization failed: {e}")
    
    # КРИТИЧЕСКАЯ ИНИЦИАЛИЗАЦИЯ МОДЕЛИ - БЕЗ ПЕРЕЗАПУСКА
    try:
        logger.info("🚀 Critical model initialization...")
        
        # Проверяем, загружена ли модель
        if not unified_llm_service.is_model_loaded():
            logger.warning("⚠️ Model not loaded, attempting initialization...")
            await unified_llm_service.initialize()
            
            # Проверяем результат
            if unified_llm_service.is_model_loaded():
                logger.info("✅ Model successfully loaded")
            else:
                logger.error("❌ Model failed to load - service will work in degraded mode")
                # НЕ ПЕРЕЗАПУСКАЕМ - работаем без модели
        else:
            logger.info("✅ Model already loaded and ready")
            
    except Exception as e:
        logger.error(f"❌ Critical model initialization failed: {e}")
        logger.warning("⚠️ Service will continue without model - manual initialization required")
        # НЕ ПЕРЕЗАПУСКАЕМ - работаем в degraded режиме
    
    logger.info("🚀 Server started with unified AI services architecture.")
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down server...")
    
    # Graceful shutdown унифицированных AI-сервисов
    try:
        await service_manager.shutdown_services()
        logger.info("✅ Unified AI services shutdown completed")
    except Exception as e:
        logger.log_error(e, {"service": "service_manager", "phase": "shutdown"})
    
    # Остановка системы мониторинга
    try:
        await unified_monitoring_service.graceful_shutdown()
        logger.info("✅ Monitoring system stopped")
    except Exception as e:
        logger.log_error(e, {"service": "monitoring", "phase": "shutdown"})
    
    # Остановка админ-панель метрики коллектора
    try:
        # await admin_metrics_collector.stop()  # УДАЛЕНО - не определен
        logger.info("✅ Admin panel metrics collector cleanup skipped")
    except Exception as e:
        logger.log_error(e, {"service": "admin_metrics_collector", "phase": "shutdown"})
    
    # Остановка системы алертов
    try:
        # from app.services.alert_service import alert_evaluation_service  # УДАЛЕНО
        # await alert_evaluation_service.stop()  # УДАЛЕНО - не определен
        logger.info("✅ Alert evaluation service cleanup skipped")
    except Exception as e:
        logger.log_error(e, {"service": "alert_evaluation", "phase": "shutdown"})
    
    # Остановка оптимизаторов производительности (legacy)
    try:
        await performance_optimizer.stop_background_optimizations()
        logger.info("✅ Performance optimizers stopped")
    except Exception as e:
        logger.log_error(e, {"service": "performance_optimizer", "phase": "shutdown"})
    
    try:
        await cache_service.close()
        logger.info("✅ Cache service closed")
    except Exception as e:
        logger.log_error(e, {"service": "cache", "phase": "shutdown"})
    
    # Очистка rate limiter (legacy)
    try:
        enhanced_rate_limiter.cleanup_old_entries()
        logger.info("✅ Rate limiter cleaned up")
    except Exception as e:
        logger.log_error(e, {"service": "rate_limiter", "phase": "shutdown"})
    
    logger.info("✅ Server shutdown completed")

# Создание FastAPI приложения
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="ИИ-Юрист для РФ - ваш персональный AI-правовед 24/7",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Middleware для логирования запросов и метрик
@app.middleware("http")
async def log_requests_and_metrics(request: Request, call_next):
    """Middleware для логирования всех запросов и сбора метрик"""
    start_time = time.time()
    
    # Получаем информацию о клиенте
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Выполняем запрос
    response = await call_next(request)
    
    # Вычисляем время выполнения
    duration = time.time() - start_time
    
    # Логируем запрос
    logger.log_api_request(
        method=request.method,
        path=str(request.url.path),
        status_code=response.status_code,
        response_time=duration,
        ip_address=client_ip
    )
    
    # Записываем метрики Prometheus (если доступен)
    if prometheus_metrics:
        prometheus_metrics.record_http_request(
            method=request.method,
            endpoint=str(request.url.path),
            status_code=response.status_code,
            duration=duration
        )
    
    return response

# Middleware для rate limiting
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Middleware для rate limiting"""
    client_ip = request.client.host if request.client else "unknown"
    path = str(request.url.path)
    
    # Проверяем rate limit
    if not enhanced_rate_limiter.is_allowed(
        ip_address=client_ip,
        endpoint=path
    ):
        # Логируем превышение лимита
        logger.log_security_event(
            event=SecurityEvent.RATE_LIMIT_EXCEEDED,
            ip_address=client_ip,
            details={"path": path},
            severity=LogLevel.WARNING
        )
        
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": enhanced_rate_limiter.get_reset_time(client_ip, path)
            }
        )
    
    response = await call_next(request)
    
    # Добавляем заголовки rate limiting
    remaining = enhanced_rate_limiter.get_remaining_requests(client_ip, path)
    reset_time = enhanced_rate_limiter.get_reset_time(client_ip, path)
    
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(int(time.time() + reset_time))
    
    return response

# Middleware для безопасности и rate limiting
from app.middleware.security_headers import (
    SecurityHeadersMiddleware, 
    InputValidationMiddleware
)
from app.middleware.readiness import ReadinessMiddleware
from app.middleware.ml_rate_limit import MLRateLimitMiddleware, MLRateLimiter
from app.middleware.admin_panel_monitoring import AdminPanelMonitoringMiddleware, admin_metrics_collector

# Initialize rate limiter
ml_rate_limiter = MLRateLimiter()

app.add_middleware(AdminPanelMonitoringMiddleware)
app.add_middleware(MLRateLimitMiddleware, rate_limiter=ml_rate_limiter)
app.add_middleware(ReadinessMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(InputValidationMiddleware)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройка доверенных хостов
# В Docker networking разрешаем все внутренние хосты через wildcard
allowed_hosts = ["*"]
if settings.ENVIRONMENT == "production":
    # В продакшене используем конкретные домены
    production_hosts = os.getenv("TRUSTED_HOSTS", "advacodex.com,www.advacodex.com,*.advacodex.com").split(",")
    allowed_hosts = [host.strip() for host in production_hosts if host.strip()]

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=allowed_hosts
)

# Подключение роутеров
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(websocket_router, prefix="/ws", tags=["websocket"])
app.include_router(lora_training_router, prefix="/api/v1", tags=["lora-training"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["analytics"])
# app.include_router(advanced_analytics_router, tags=["advanced-analytics"])  # Temporarily disabled
app.include_router(enhanced_chat_router, prefix="/api/v1/chat", tags=["enhanced-chat"])

# Backup system router - temporarily disabled
# from app.api.backup import router as backup_router
# app.include_router(backup_router, prefix="/api/v1", tags=["backup"])

# Alert management router
from app.api.alerts import router as alerts_router
app.include_router(alerts_router, prefix="/api/v1/alerts", tags=["alerts"])

# Admin WebSocket router (временно отключен)
# from app.api.admin_websocket import router as admin_websocket_router
# app.include_router(admin_websocket_router, prefix="/ws", tags=["admin-websocket"])

# Admin Notifications router (временно отключен)
# from app.api.admin_notifications import router as admin_notifications_router
# app.include_router(admin_notifications_router, prefix="/api/v1/admin", tags=["admin-notifications"])

# Глобальный обработчик ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик исключений"""
    logger.log_error(exc, {
        "path": str(request.url.path),
        "method": request.method,
        "client_ip": request.client.host if request.client else "unknown"
    })
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": id(request)
        }
    )

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "Добро пожаловать в ИИ-Юрист для РФ!",
        "version": settings.VERSION,
        "docs": "/docs",
        "api": settings.API_V1_STR,
        "health": "/health",
        "ready": "/ready"
    }

@app.get("/health")
async def health():
    """Liveness probe - проверка что сервер работает"""
    return {
        "status": "healthy",
        "service": "ai-lawyer-backend",
        "version": settings.VERSION,
        "timestamp": time.time()
    }

@app.get("/ready")
async def readiness():
    """Readiness probe - проверка готовности унифицированных AI-сервисов"""
    
    # Получаем статус от ServiceManager
    system_health = service_manager.get_service_status()
    
    # Получаем статус мониторинга
    monitoring_health = await unified_monitoring_service.health_check()
    
    # Формируем ответ
    status = {
        "ready": system_health.status.value in ["healthy", "degraded"],
        "system_status": system_health.status.value,
        "services": {
            "total": system_health.total_services,
            "healthy": system_health.healthy_services,
            "degraded": system_health.degraded_services,
            "unhealthy": system_health.unhealthy_services
        },
        "monitoring": {
            "status": monitoring_health["status"],
            "metrics_count": monitoring_health.get("metrics_count", 0),
            "active_alerts": monitoring_health.get("active_alerts", 0)
        },
        "uptime": system_health.uptime,
        "last_check": system_health.last_check.isoformat()
    }
    
    # Возвращаем 503 если система не готова
    status_code = 200 if status["ready"] else 503
    
    from fastapi import Response
    return Response(
        content=json.dumps(status, ensure_ascii=False, indent=2),
        media_type="application/json",
        status_code=status_code
    )

@app.get("/ready/{endpoint_path:path}")
async def check_endpoint_readiness(endpoint_path: str):
    """Проверка готовности конкретного endpoint'а"""
    from app.middleware.readiness import ReadinessChecker
    
    # Добавляем префикс API если нет
    if not endpoint_path.startswith("/"):
        endpoint_path = "/" + endpoint_path
    if not endpoint_path.startswith("/api/"):
        endpoint_path = "/api/v1/" + endpoint_path.lstrip("/")
    
    status = ReadinessChecker.check_endpoint_readiness(app, endpoint_path)
    
    status_code = 200 if status["ready"] else 503
    
    from fastapi import Response
    return Response(
        content=json.dumps(status, ensure_ascii=False, indent=2),
        media_type="application/json",
        status_code=status_code
    )

@app.get("/metrics")
async def get_prometheus_metrics():
    """Prometheus метрики в формате exposition"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi import Response
    
    # Получаем метрики от унифицированной системы мониторинга
    unified_metrics = unified_monitoring_service.get_prometheus_metrics()
    
    # Получаем legacy метрики
    legacy_metrics = generate_latest()
    
    # Объединяем метрики
    combined_metrics = unified_metrics + "\n" + legacy_metrics.decode('utf-8')
    
    return Response(
        content=combined_metrics,
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/metrics/json")
async def get_metrics_json():
    """Метрики в JSON формате от унифицированной системы"""
    try:
        # Получаем данные дашборда от системы мониторинга
        dashboard_data = unified_monitoring_service.get_dashboard_data()
        
        # Получаем статистику ServiceManager
        service_manager_stats = service_manager.get_stats()
        
        # Получаем метрики унифицированных сервисов
        unified_service_stats = {}
        
        if unified_llm_service.is_model_loaded():
            unified_service_stats["unified_llm"] = unified_llm_service.get_metrics().__dict__
        
        if unified_rag_service.is_ready():
            unified_service_stats["unified_rag"] = unified_rag_service.get_metrics().__dict__
        
        # Legacy метрики (для совместимости)
        legacy_stats = {}
        try:
            # Проверяем доступность performance_monitor
            if 'performance_monitor' in globals():
                legacy_stats["performance_monitor"] = performance_monitor.get_all_metrics()
            legacy_stats["performance_optimizer"] = performance_optimizer.get_performance_summary()
        except Exception as e:
            logger.warning(f"Failed to get legacy metrics: {e}")
        
        return {
            "unified_services": unified_service_stats,
            "service_manager": service_manager_stats,
            "monitoring_dashboard": dashboard_data,
            "legacy_metrics": legacy_stats,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error getting unified metrics: {e}")
        return {
            "error": "Failed to get metrics",
            "timestamp": time.time()
        }

@app.get("/rate-limit/stats/{user_id}")
async def get_user_rate_limit_stats(user_id: str):
    """Получить статистику rate limiting для пользователя"""
    try:
        ml_rate_limiter_instance = MLRateLimiter()
        stats = ml_rate_limiter_instance.get_user_stats(user_id)
        return {
            "success": True,
            "stats": stats,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error getting user rate limit stats: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": time.time()
        }

if __name__ == "__main__":
    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=settings.DEBUG,
            log_level="info"
        )
    except ImportError:
        logger.error("uvicorn не установлен. Установите его: pip install uvicorn")
        sys.exit(1)