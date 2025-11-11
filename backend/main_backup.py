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
    prometheus_metrics = PrometheusMetrics()

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
            
            logger.info(f"📊 System health: {system_health}")
        else:
            logger.error("❌ Failed to initialize unified AI services")
            app.state.system_health = {"status": "error", "services": {}}
    
    except Exception as e:
        logger.log_error(e, {"service": "unified_ai_services"})
        logger.error(f"Unified AI services initialization failed: {e}")
        app.state.system_health = {"status": "error", "services": {}}
    
    # Инициализируем legacy сервисы для совместимости
    try:
        await embeddings_service.initialize()
        logger.info("✅ Legacy embeddings service initialized")
    except Exception as e:
        logger.log_error(e, {"service": "legacy_embeddings"})
    
    try:
        await enhanced_embeddings_service.initialize()
        logger.info("✅ Enhanced embeddings service initialized")
    except Exception as e:
        logger.log_error(e, {"service": "enhanced_embeddings"})
    
    try:
        await vector_store_service.initialize()
        logger.info("✅ Vector store service initialized")
    except Exception as e:
        logger.log_error(e, {"service": "vector_store"})
    
    # Инициализируем performance optimizer
    try:
        await performance_optimizer.initialize()
        logger.info("✅ Performance optimizer initialized")
    except Exception as e:
        logger.log_error(e, {"service": "performance_optimizer"})
    
    # Инициализируем rate limiter
    try:
        await enhanced_rate_limiter.initialize()
        logger.info("✅ Enhanced rate limiter initialized")
    except Exception as e:
        logger.log_error(e, {"service": "rate_limiter"})
    
    logger.info("🎉 All services initialized successfully!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down application...")
    
    try:
        await service_manager.shutdown_services()
        logger.info("✅ Unified AI services shutdown completed")
    except Exception as e:
        logger.log_error(e, {"service": "unified_ai_shutdown"})
    
    try:
        await cache_service.shutdown()
        logger.info("✅ Cache service shutdown completed")
    except Exception as e:
        logger.log_error(e, {"service": "cache_shutdown"})

# Настройка логирования
logging.basicConfig(
    level=logging.INFO if settings.ENVIRONMENT == "production" else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = get_logger(__name__)

# Создание приложения FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-powered legal assistant for Russian Federation",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware для безопасности
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["advacodex.com", "www.advacodex.com", "*.advacodex.com"]
    )

# Подключение API роутеров
app.include_router(api_router, prefix="/api/v1")
app.include_router(websocket_router, prefix="/ws")
app.include_router(lora_training_router, prefix="/api/v1/lora")
app.include_router(analytics_router, prefix="/api/v1/analytics")
app.include_router(enhanced_chat_router, prefix="/api/v1/chat")

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Получаем статус системы
        system_health = getattr(app.state, 'system_health', {"status": "unknown"})
        
        return {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "environment": settings.ENVIRONMENT,
            "version": settings.VERSION,
            "system_health": system_health,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )

@app.get("/api/v1/info")
async def api_info():
    """Информация о API"""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "api_version": "v1",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "features": {
            "ai_chat": True,
            "document_analysis": True,
            "legal_consultation": True,
            "rag_system": True,
            "vector_search": True,
            "admin_panel": True,
            "analytics": True,
            "monitoring": True
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if settings.ENVIRONMENT == "production" else "debug"
    )
