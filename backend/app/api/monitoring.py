"""
API эндпоинты для мониторинга системы и управления бэкапами
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..core.database import get_db
from ..models.user import User
from ..services.auth_service import AuthService
from ..services.db_monitoring_service import db_monitoring_service
# from ..services.backup_service import backup_service  # Temporarily disabled - missing croniter
from ..services.vector_store_service import vector_store_service

router = APIRouter()
auth_service = AuthService()


def get_current_admin(current_user: User = Depends(auth_service.get_current_active_user)) -> User:
    """Проверка прав администратора"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Требуются права администратора")
    return current_user


@router.get("/health")
async def health_check():
    """Проверка здоровья системы (доступно всем)"""
    db_health = db_monitoring_service.get_health_check()
    
    # Проверяем статус AI моделей - используем унифицированные сервисы
    from ..services.unified_llm_service import unified_llm_service
    from ..services.embeddings_service import embeddings_service
    from ..services.rag_service import rag_service
    
    ai_models_status = "ready" if unified_llm_service.is_model_loaded() else "loading"
    embeddings_status = "ready" if embeddings_service.is_ready() else "loading"
    rag_status = "ready" if rag_service.is_ready() else "loading"
    
    # Определяем общий статус
    overall_status = "healthy"
    if db_health["status"] != "healthy":
        overall_status = "unhealthy"
    elif ai_models_status == "loading" or embeddings_status == "loading" or rag_status == "loading":
        overall_status = "loading"
    
    return {
        "status": overall_status,
        "timestamp": db_health["timestamp"],
        "database": {
            "status": db_health["status"],
            "response_time_ms": db_health.get("response_time_ms", 0),
            "type": db_health.get("database_type", "unknown")
        },
        "services": {
            "vector_store": "ready" if vector_store_service.is_ready() else "not_ready",
            "ai_models": ai_models_status,
            "embeddings": embeddings_status,
            "rag": rag_status
        },
        "ai_models": {
            "unified_llm_vistral": {
                "loaded": unified_llm_service.is_model_loaded(),
                "type": "Vistral-24B-Instruct"
            },
            "embeddings": {
                "ready": embeddings_service.is_ready(),
                "model_name": embeddings_service.model_name if hasattr(embeddings_service, 'model_name') else "unknown"
            }
        }
    }


@router.get("/metrics")
async def get_database_metrics(current_admin: User = Depends(get_current_admin)):
    """Получить детальные метрики базы данных (только для админов)"""
    metrics = db_monitoring_service.get_database_metrics()
    return metrics


@router.get("/metrics/summary")
async def get_metrics_summary(
    hours: int = 24,
    current_admin: User = Depends(get_current_admin)
):
    """Получить сводку метрик за период (только для админов)"""
    summary = db_monitoring_service.get_metrics_summary(hours)
    return summary


@router.get("/backup/status")
async def get_backup_status(current_admin: User = Depends(get_current_admin)):
    """Получить статус системы резервного копирования"""
    status = backup_service.get_backup_status()
    return status


@router.post("/backup/create")
async def create_backup(
    background_tasks: BackgroundTasks,
    current_admin: User = Depends(get_current_admin)
):
    """Создать резервную копию вручную"""
    try:
        # Запускаем бэкап в фоновом режиме
        background_tasks.add_task(backup_service.create_backup)
        
        return {
            "status": "started",
            "message": "Резервное копирование запущено в фоновом режиме",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бэкапа: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка запуска резервного копирования: {e}")


@router.get("/backup/list")
async def list_backups(current_admin: User = Depends(get_current_admin)):
    """Получить список всех резервных копий"""
    status = backup_service.get_backup_status()
    
    if status["status"] == "error":
        raise HTTPException(status_code=500, detail=status["error"])
    
    return {
        "backups": status.get("backups", []),
        "total_count": status.get("backups_count", 0),
        "total_size_mb": round(status.get("total_size", 0) / (1024 * 1024), 2),
        "backup_dir": status.get("backup_dir", ""),
        "settings": status.get("settings", {})
    }


@router.post("/backup/restore/{backup_name}")
async def restore_backup(
    backup_name: str,
    background_tasks: BackgroundTasks,
    current_admin: User = Depends(get_current_admin)
):
    """Восстановить данные из резервной копии"""
    try:
        backup_path = os.path.join(backup_service.backup_dir, backup_name)
        
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=404, detail="Резервная копия не найдена")
        
        # Запускаем восстановление в фоновом режиме
        background_tasks.add_task(backup_service.restore_backup, backup_path)
        
        return {
            "status": "started",
            "message": f"Восстановление из {backup_name} запущено в фоновом режиме",
            "backup_name": backup_name,
            "timestamp": datetime.now().isoformat(),
            "warning": "Сервис может потребовать перезапуска после восстановления"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка восстановления: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка восстановления: {e}")


@router.get("/database/info")
async def get_database_info(current_admin: User = Depends(get_current_admin)):
    """Получить информацию о базе данных"""
    try:
        info = {
            "database_url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL,
            "database_type": "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql",
            "environment": settings.ENVIRONMENT,
            "debug_mode": settings.DEBUG
        }
        
        # Добавляем метрики
        metrics = db_monitoring_service.get_database_metrics()
        info.update({
            "current_metrics": metrics,
            "vector_store": {
                "type": "chromadb",
                "status": "ready" if vector_store_service.is_ready() else "not_ready",
                "collection_name": vector_store_service.collection_name if hasattr(vector_store_service, 'collection_name') else "unknown"
            }
        })
        
        return info
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения информации о БД: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения информации: {e}")


@router.post("/database/optimize")
async def optimize_database(current_admin: User = Depends(get_current_admin)):
    """Оптимизация базы данных"""
    try:
        with SessionLocal() as db:
            if settings.DATABASE_URL.startswith("sqlite"):
                # SQLite оптимизация
                db.execute(text("VACUUM"))
                db.execute(text("ANALYZE"))
                db.commit()
                
                return {
                    "status": "completed",
                    "operations": ["VACUUM", "ANALYZE"],
                    "database_type": "sqlite",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # PostgreSQL оптимизация
                db.execute(text("VACUUM ANALYZE"))
                db.commit()
                
                return {
                    "status": "completed",
                    "operations": ["VACUUM ANALYZE"],
                    "database_type": "postgresql",
                    "timestamp": datetime.now().isoformat()
                }
                
    except Exception as e:
        logger.error(f"❌ Ошибка оптимизации БД: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка оптимизации: {e}")


@router.get("/vector-store/info")
async def get_vector_store_info(current_admin: User = Depends(get_current_admin)):
    """Получить информацию о векторной базе данных"""
    try:
        if not vector_store_service.is_ready():
            return {
                "status": "not_ready",
                "message": "Векторная база данных не инициализирована"
            }
        
        # Получаем статистику из ChromaDB
        collection = vector_store_service.collection
        
        # Подсчитываем документы
        all_results = collection.get(include=['metadatas'])
        
        # Группируем по document_id
        unique_docs = set()
        for meta in all_results['metadatas']:
            doc_id = meta.get('document_id', 'unknown')
            unique_docs.add(doc_id)
        
        return {
            "status": "ready",
            "type": "chromadb",
            "collection_name": vector_store_service.collection_name,
            "total_chunks": len(all_results['metadatas']),
            "unique_documents": len(unique_docs),
            "db_path": vector_store_service.db_path
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения информации о векторной БД: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения информации: {e}")
