from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from ..core.database import get_db
from ..models.user import User
from ..services.auth_service import AuthService
from ..services.unified_llm_service import unified_llm_service

logger = logging.getLogger(__name__)

router = APIRouter()
auth_service = AuthService()


@router.get("/stats", response_model=Dict[str, Any])
async def get_llm_stats(
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получение статистики работы унифицированной LLM модели (Vistral)"""
    try:
        metrics = unified_llm_service.get_metrics()
        model_loaded = unified_llm_service.is_model_loaded()
        
        return {
            "model_loaded": model_loaded,
            "metrics": {
                "requests_per_minute": metrics.requests_per_minute,
                "average_response_time": metrics.average_response_time,
                "p95_response_time": metrics.p95_response_time,
                "error_rate": metrics.error_rate,
                "queue_length": metrics.queue_length,
                "concurrent_requests": metrics.concurrent_requests,
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "memory_usage_mb": metrics.memory_usage_mb,
                "cpu_usage_percent": metrics.cpu_usage_percent
            },
            "config": {
                "max_concurrency": unified_llm_service._max_concurrency,
                "inference_timeout": unified_llm_service._inference_timeout,
                "queue_size": unified_llm_service._queue_size
            }
        }
    except Exception as e:
        logger.error(f"Ошибка получения статистики LLM: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статистики")


@router.post("/preload")
async def preload_llm_model(
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Предзагрузка унифицированной LLM модели (Vistral)"""
    try:
        await unified_llm_service.ensure_model_loaded_async()
        return {"message": "Унифицированная LLM модель (Vistral) предзагружена успешно"}
    except Exception as e:
        logger.error(f"Ошибка предзагрузки LLM модели: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка предзагрузки: {str(e)}")


@router.get("/health")
async def llm_health_check(
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Проверка здоровья унифицированного LLM сервиса"""
    try:
        health = await unified_llm_service.health_check()
        metrics = unified_llm_service.get_metrics()
        
        return {
            "status": health.status,
            "model_loaded": unified_llm_service.is_model_loaded(),
            "last_check": health.last_check.isoformat(),
            "response_time": health.response_time,
            "error_rate": health.error_rate,
            "memory_usage_mb": health.memory_usage,
            "cpu_usage_percent": health.cpu_usage,
            "queue_length": health.queue_length,
            "active_requests": health.active_requests,
            "metrics": {
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "success_rate": (
                    metrics.successful_requests / max(metrics.total_requests, 1) * 100
                ),
                "average_response_time": metrics.average_response_time,
                "p95_response_time": metrics.p95_response_time
            }
        }
    except Exception as e:
        logger.error(f"Ошибка проверки здоровья LLM: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
