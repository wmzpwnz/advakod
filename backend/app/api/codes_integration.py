"""
API endpoints для интеграции кодексов с RAG системой
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import logging
from datetime import datetime

from ..services.codes_rag_integration import codes_rag_integration

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/codes/integration", tags=["codes-integration"])

@router.get("/status")
async def get_integration_status() -> Dict[str, Any]:
    """Возвращает статус интеграции кодексов"""
    try:
        status = codes_rag_integration.get_integration_status()
        return {
            "success": True,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения статуса интеграции: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/integrate")
async def start_codes_integration(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Запускает интеграцию всех кодексов с RAG системой"""
    try:
        # Запускаем интеграцию в фоновом режиме
        background_tasks.add_task(codes_rag_integration.integrate_all_codes)
        
        return {
            "success": True,
            "message": "Интеграция кодексов с RAG системой запущена в фоновом режиме",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка запуска интеграции кодексов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_in_codes(query: str, limit: int = 10) -> Dict[str, Any]:
    """Ищет в интегрированных кодексах"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Запрос не может быть пустым")
        
        if limit <= 0 or limit > 50:
            raise HTTPException(status_code=400, detail="Лимит должен быть от 1 до 50")
        
        result = await codes_rag_integration.search_in_codes(query, limit)
        
        return {
            "success": True,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка поиска в кодексах: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_integration_stats() -> Dict[str, Any]:
    """Возвращает статистику интеграции"""
    try:
        stats = codes_rag_integration.integration_stats
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения статистики интеграции: {e}")
        raise HTTPException(status_code=500, detail=str(e))
