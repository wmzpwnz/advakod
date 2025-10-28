"""
API endpoints для работы с кодексами
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List
import logging

from ..services.codes_downloader import CodesDownloader
from ..services.codes_rag_integration import CodesRAGIntegration
from ..services.codes_monitor import CodesMonitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/codes", tags=["codes"])

# Инициализация сервисов
downloader = CodesDownloader()
rag_integration = CodesRAGIntegration()
monitor = CodesMonitor()

@router.get("/list")
async def get_codes_list():
    """Получает список доступных кодексов"""
    try:
        return {
            "codexes": list(downloader.codexes.keys()),
            "total_count": len(downloader.codexes)
        }
    except Exception as e:
        logger.error(f"Ошибка получения списка кодексов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/download")
async def start_codes_download(background_tasks: BackgroundTasks):
    """Запускает скачивание кодексов в фоновом режиме"""
    try:
        background_tasks.add_task(downloader.download_all_codexes)
        return {"message": "Скачивание кодексов запущено в фоновом режиме"}
    except Exception as e:
        logger.error(f"Ошибка запуска скачивания: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_codes_status():
    """Получает статус скачанных кодексов"""
    try:
        status = downloader.get_status()
        return status
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/integrate")
async def start_codes_integration(background_tasks: BackgroundTasks):
    """Запускает интеграцию кодексов с RAG системой"""
    try:
        background_tasks.add_task(rag_integration.integrate_all_codexes)
        return {"message": "Интеграция кодексов запущена в фоновом режиме"}
    except Exception as e:
        logger.error(f"Ошибка запуска интеграции: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/integration-status")
async def get_integration_status():
    """Получает статус интеграции кодексов"""
    try:
        status = rag_integration.get_integration_status()
        return status
    except Exception as e:
        logger.error(f"Ошибка получения статуса интеграции: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/monitor")
async def get_system_monitor():
    """Получает общий статус системы кодексов"""
    try:
        status = monitor.get_system_status()
        return status
    except Exception as e:
        logger.error(f"Ошибка получения статуса мониторинга: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_system_alerts():
    """Получает алерты системы"""
    try:
        alerts = monitor.check_system_alerts()
        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        logger.error(f"Ошибка получения алертов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/download")
async def get_download_history(days: int = 7):
    """Получает историю скачиваний"""
    try:
        history = monitor.get_download_history(days)
        return {"history": history, "days": days}
    except Exception as e:
        logger.error(f"Ошибка получения истории скачиваний: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/integration")
async def get_integration_history(days: int = 7):
    """Получает историю интеграций"""
    try:
        history = monitor.get_integration_history(days)
        return {"history": history, "days": days}
    except Exception as e:
        logger.error(f"Ошибка получения истории интеграций: {e}")
        raise HTTPException(status_code=500, detail=str(e))


