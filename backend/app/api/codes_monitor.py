"""
API endpoints для мониторинга процесса скачивания и интеграции кодексов
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import logging
from datetime import datetime

from ..services.codes_monitor import codes_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/codes/monitor", tags=["codes-monitor"])

@router.get("/status")
async def get_monitoring_status() -> Dict[str, Any]:
    """Возвращает текущий статус мониторинга"""
    try:
        status = await codes_monitor.check_system_status()
        return {
            "success": True,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения статуса мониторинга: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_monitoring_stats() -> Dict[str, Any]:
    """Возвращает статистику мониторинга"""
    try:
        stats = codes_monitor.get_monitoring_stats()
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения статистики мониторинга: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start")
async def start_monitoring(background_tasks: BackgroundTasks, check_interval: int = 60) -> Dict[str, Any]:
    """Запускает мониторинг в фоновом режиме"""
    try:
        if check_interval < 10 or check_interval > 3600:
            raise HTTPException(
                status_code=400, 
                detail="Интервал проверки должен быть от 10 до 3600 секунд"
            )
        
        # Запускаем мониторинг в фоновом режиме
        background_tasks.add_task(codes_monitor.start_monitoring, check_interval)
        
        return {
            "success": True,
            "message": f"Мониторинг запущен с интервалом {check_interval} секунд",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка запуска мониторинга: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_alerts() -> Dict[str, Any]:
    """Возвращает список алертов"""
    try:
        alerts = codes_monitor.monitor_stats.get("alerts", [])
        
        return {
            "success": True,
            "alerts": alerts,
            "total_alerts": len(alerts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения алертов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def get_health_check() -> Dict[str, Any]:
    """Проверка здоровья системы"""
    try:
        # Быстрая проверка основных компонентов
        health_status = {
            "codes_downloader": "ok",
            "codes_integration": "ok", 
            "monitoring": "ok",
            "timestamp": datetime.now().isoformat()
        }
        
        # Проверяем доступность основных сервисов
        try:
            downloader_status = codes_monitor.codes_downloader.get_status()
            if not downloader_status:
                health_status["codes_downloader"] = "error"
        except:
            health_status["codes_downloader"] = "error"
        
        try:
            integration_status = codes_monitor.codes_integration.get_integration_status()
            if not integration_status:
                health_status["codes_integration"] = "error"
        except:
            health_status["codes_integration"] = "error"
        
        # Определяем общий статус
        overall_status = "healthy"
        if any(status == "error" for status in health_status.values() if isinstance(status, str)):
            overall_status = "unhealthy"
        
        return {
            "success": True,
            "overall_status": overall_status,
            "health_status": health_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка проверки здоровья системы: {e}")
        raise HTTPException(status_code=500, detail=str(e))
