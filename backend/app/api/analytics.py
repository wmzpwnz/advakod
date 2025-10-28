"""
API для мониторинга и аналитики
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any, List
import time
import logging

from ..core.analytics_engine import analytics_engine
from ..core.performance_optimizer import performance_monitor
from ..services.unified_llm_service import unified_llm_service
from ..services.enhanced_rag_service import enhanced_rag_service
from ..services.auth_service import auth_service
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/performance")
async def get_performance_metrics(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получает метрики производительности"""
    try:
        performance_metrics = analytics_engine.get_performance_metrics()
        
        # Добавляем дополнительные метрики
        llm_metrics = unified_llm_service.get_metrics()
        additional_metrics = {
            "unified_llm_stats": {
                "requests_per_minute": llm_metrics.requests_per_minute,
                "average_response_time": llm_metrics.average_response_time,
                "p95_response_time": llm_metrics.p95_response_time,
                "error_rate": llm_metrics.error_rate,
                "total_requests": llm_metrics.total_requests,
                "successful_requests": llm_metrics.successful_requests,
                "failed_requests": llm_metrics.failed_requests
            },
            "rag_stats": enhanced_rag_service.get_stats() if hasattr(enhanced_rag_service, 'get_stats') else {},
            "performance_monitor": performance_monitor.get_all_metrics()
        }
        
        return {
            "performance": performance_metrics.__dict__,
            "additional_metrics": additional_metrics,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")


@router.get("/quality")
async def get_quality_metrics(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получает метрики качества"""
    try:
        quality_metrics = analytics_engine.get_quality_metrics()
        
        return {
            "quality": quality_metrics.__dict__,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error getting quality metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get quality metrics")


@router.get("/legal-fields")
async def get_legal_field_analytics(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получает аналитику по отраслям права"""
    try:
        legal_field_analytics = analytics_engine.get_legal_field_analytics()
        
        return {
            "legal_fields": legal_field_analytics,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error getting legal field analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get legal field analytics")


@router.get("/complexity")
async def get_complexity_analytics(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получает аналитику по сложности запросов"""
    try:
        complexity_analytics = analytics_engine.get_complexity_analytics()
        
        return {
            "complexity": complexity_analytics,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error getting complexity analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get complexity analytics")


@router.get("/user/{user_id}")
async def get_user_analytics(
    user_id: str,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получает аналитику пользователя"""
    try:
        # Проверяем права доступа
        if not current_user.is_admin and current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        user_analytics = analytics_engine.get_user_analytics(user_id)
        
        return {
            "user_analytics": user_analytics,
            "timestamp": time.time()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user analytics")


@router.get("/system-health")
async def get_system_health(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получает состояние системы"""
    try:
        system_health = analytics_engine.get_system_health()
        
        return system_health
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system health")


@router.get("/alerts")
async def get_alerts(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получает алерты системы"""
    try:
        alerts = analytics_engine.get_alerts(limit)
        
        return {
            "alerts": alerts,
            "total": len(alerts),
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alerts")


@router.delete("/alerts")
async def clear_alerts(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Очищает алерты"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        analytics_engine.clear_alerts()
        
        return {
            "message": "Alerts cleared successfully",
            "timestamp": time.time()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear alerts")


@router.get("/export")
async def export_analytics(
    format: str = Query("json", pattern="^(json|csv)$"),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Экспортирует аналитику"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        exported_data = analytics_engine.export_analytics(format)
        
        return {
            "data": exported_data,
            "format": format,
            "timestamp": time.time()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to export analytics")


@router.post("/reset")
async def reset_analytics(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Сбрасывает аналитику"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        analytics_engine.reset_statistics()
        
        return {
            "message": "Analytics reset successfully",
            "timestamp": time.time()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset analytics")


@router.get("/dashboard")
async def get_dashboard_data(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получает данные для дашборда"""
    try:
        # Собираем все данные для дашборда
        performance = analytics_engine.get_performance_metrics()
        quality = analytics_engine.get_quality_metrics()
        legal_fields = analytics_engine.get_legal_field_analytics()
        complexity = analytics_engine.get_complexity_analytics()
        system_health = analytics_engine.get_system_health()
        alerts = analytics_engine.get_alerts(10)  # Последние 10 алертов
        
        return {
            "performance": performance.__dict__,
            "quality": quality.__dict__,
            "legal_fields": legal_fields,
            "complexity": complexity,
            "system_health": system_health,
            "recent_alerts": alerts,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")