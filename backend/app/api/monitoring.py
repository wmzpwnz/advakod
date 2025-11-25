"""
API эндпоинты для мониторинга системы и управления бэкапами
"""

import logging
import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any

from ..core.database import get_db, SessionLocal
from ..core.config import settings
from ..models.user import User
from ..services.auth_service import AuthService
from ..services.db_monitoring_service import db_monitoring_service
from ..services.backup_monitoring_service import backup_monitoring_service
from ..services.unified_monitoring_service import unified_monitoring_service
from ..services.service_manager import service_manager
from ..services.vector_store_service import vector_store_service

logger = logging.getLogger(__name__)
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
    try:
        # Получаем статус от всех систем мониторинга
        db_health = db_monitoring_service.get_health_check()
        unified_health = await unified_monitoring_service.health_check()
        system_health = service_manager.get_service_status()
        
        # Проверяем статус кэша
        from ..core.cache import cache_service
        cache_health = await cache_service.health_check()
        
        # Проверяем статус AI моделей - используем унифицированные сервисы
        from ..services.unified_llm_service import unified_llm_service
        from ..services.unified_rag_service import unified_rag_service
        
        try:
            from ..services.embeddings_service import embeddings_service
            embeddings_status = "ready" if embeddings_service.is_ready() else "loading"
        except Exception:
            embeddings_status = "unknown"
        
        ai_models_status = "ready" if unified_llm_service.is_model_loaded() else "loading"
        rag_status = "ready" if unified_rag_service.is_ready() else "loading"
        
        # Определяем общий статус
        overall_status = "healthy"
        if db_health["status"] != "healthy":
            overall_status = "degraded"
        elif system_health.status.value in ["unhealthy", "error"]:
            overall_status = "unhealthy"
        elif ai_models_status == "loading" or rag_status == "loading":
            overall_status = "loading"
        elif system_health.status.value == "degraded":
            overall_status = "degraded"
        elif cache_health["fallback_active"] and not cache_health["redis_connected"]:
            # Кэш работает в fallback режиме - система деградирована, но работает
            if overall_status == "healthy":
                overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "database": {
                "status": db_health["status"],
                "response_time_ms": db_health.get("response_time_ms", 0),
                "type": db_health.get("database_type", "unknown"),
                "error": db_health.get("error")
            },
            "services": {
                "vector_store": "ready" if vector_store_service.is_ready() else "not_ready",
                "ai_models": ai_models_status,
                "embeddings": embeddings_status,
                "rag": rag_status,
                "service_manager": system_health.status.value,
                "unified_monitoring": unified_health["status"]
            },
            "service_manager": {
                "total_services": system_health.total_services,
                "healthy_services": system_health.healthy_services,
                "degraded_services": system_health.degraded_services,
                "unhealthy_services": system_health.unhealthy_services,
                "uptime": system_health.uptime
            },
            "ai_models": {
                "unified_llm_vistral": {
                    "loaded": unified_llm_service.is_model_loaded(),
                    "type": "Vistral-24B-Instruct"
                },
                "unified_rag": {
                    "ready": unified_rag_service.is_ready(),
                    "type": "Unified RAG Service"
                },
                "embeddings": {
                    "ready": embeddings_status == "ready",
                    "model_name": "sentence-transformers"
                }
            },
            "cache": {
                "redis_available": cache_health["redis_available"],
                "redis_connected": cache_health["redis_connected"],
                "fallback_active": cache_health["fallback_active"],
                "in_memory_cache_size": cache_health["in_memory_cache_size"],
                "redis_url": cache_health["redis_url"],
                "error": cache_health.get("error"),
                "redis_info": cache_health.get("redis_info", {})
            },
            "monitoring": {
                "metrics_collected": unified_health.get("stats", {}).get("metrics_collected", 0),
                "active_alerts": unified_health.get("active_alerts", 0),
                "background_tasks": unified_health.get("background_tasks", 0)
            }
        }
    except Exception as e:
        logger.error(f"❌ Error in health check: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "database": {"status": "unknown"},
            "services": {"status": "unknown"},
            "ai_models": {"status": "unknown"}
        }


@router.get("/metrics")
async def get_system_metrics(current_admin: User = Depends(get_current_admin)):
    """Получить детальные метрики системы (только для админов)"""
    try:
        # Собираем метрики от всех систем мониторинга
        db_metrics = db_monitoring_service.get_database_metrics()
        unified_dashboard = unified_monitoring_service.get_dashboard_data()
        service_stats = service_manager.get_stats()
        
        # Пытаемся получить метрики backup системы
        try:
            backup_metrics = await backup_monitoring_service.get_system_metrics()
        except Exception as e:
            logger.warning(f"⚠️ Backup metrics unavailable: {e}")
            backup_metrics = {"status": "error", "error": str(e)}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "database": db_metrics,
            "unified_monitoring": unified_dashboard,
            "service_manager": service_stats,
            "backup_system": backup_metrics,
            "system_summary": {
                "overall_health": unified_dashboard.get("services", {}).get("status", "unknown"),
                "total_services": unified_dashboard.get("services", {}).get("total", 0),
                "healthy_services": unified_dashboard.get("services", {}).get("healthy", 0),
                "active_alerts": unified_dashboard.get("alerts", {}).get("count", 0),
                "metrics_collected": unified_dashboard.get("system", {}).get("metrics_collected", 0)
            }
        }
    except Exception as e:
        logger.error(f"❌ Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting metrics: {e}")


@router.get("/metrics/summary")
async def get_metrics_summary(
    hours: int = 24,
    current_admin: User = Depends(get_current_admin)
):
    """Получить сводку метрик за период (только для админов)"""
    summary = db_monitoring_service.get_metrics_summary(hours)
    return summary


@router.get("/monitoring/dashboard")
async def get_monitoring_dashboard(current_admin: User = Depends(get_current_admin)):
    """Получить данные для дашборда мониторинга"""
    try:
        dashboard_data = unified_monitoring_service.get_dashboard_data()
        return dashboard_data
    except Exception as e:
        logger.error(f"❌ Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting dashboard data: {e}")


@router.get("/monitoring/alerts")
async def get_active_alerts(current_admin: User = Depends(get_current_admin)):
    """Получить активные алерты"""
    try:
        alerts = unified_monitoring_service.alert_manager.get_active_alerts()
        alert_history = unified_monitoring_service.alert_manager.get_alert_history(limit=50)
        
        return {
            "active_alerts": [
                {
                    "rule_name": alert.rule_name,
                    "message": alert.message,
                    "severity": alert.severity,
                    "started_at": alert.started_at.isoformat(),
                    "last_triggered": alert.last_triggered.isoformat(),
                    "count": alert.count
                }
                for alert in alerts
            ],
            "alert_history": [
                {
                    "rule_name": alert.rule_name,
                    "message": alert.message,
                    "severity": alert.severity,
                    "started_at": alert.started_at.isoformat(),
                    "last_triggered": alert.last_triggered.isoformat(),
                    "count": alert.count
                }
                for alert in alert_history
            ],
            "total_active": len(alerts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting alerts: {e}")


@router.get("/monitoring/metrics/{metric_name}")
async def get_metric_history(
    metric_name: str,
    duration_minutes: int = 60,
    current_admin: User = Depends(get_current_admin)
):
    """Получить историю конкретной метрики"""
    try:
        history = unified_monitoring_service.get_metric_history(metric_name, duration_minutes)
        return {
            "metric_name": metric_name,
            "duration_minutes": duration_minutes,
            "data_points": len(history),
            "history": history,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error getting metric history: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting metric history: {e}")


@router.get("/services/status")
async def get_services_status(current_admin: User = Depends(get_current_admin)):
    """Получить детальный статус всех сервисов"""
    try:
        system_health = service_manager.get_service_status()
        
        services_detail = {}
        for service_name, service_info in system_health.services.items():
            services_detail[service_name] = {
                "name": service_info.name,
                "status": service_info.status.value,
                "priority": service_info.priority.name,
                "last_health_check": service_info.last_health_check.isoformat() if service_info.last_health_check else None,
                "initialization_time": service_info.initialization_time,
                "error_count": service_info.error_count,
                "last_error": service_info.last_error,
                "restart_count": service_info.restart_count,
                "dependencies": service_info.dependencies,
                "health_check_interval": service_info.health_check_interval
            }
        
        return {
            "system_status": system_health.status.value,
            "total_services": system_health.total_services,
            "healthy_services": system_health.healthy_services,
            "degraded_services": system_health.degraded_services,
            "unhealthy_services": system_health.unhealthy_services,
            "uptime": system_health.uptime,
            "last_check": system_health.last_check.isoformat(),
            "services": services_detail,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error getting services status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting services status: {e}")


@router.post("/services/{service_name}/restart")
async def restart_service(
    service_name: str,
    current_admin: User = Depends(get_current_admin)
):
    """Перезапустить конкретный сервис"""
    try:
        success = await service_manager.restart_service(service_name)
        
        if success:
            return {
                "status": "success",
                "message": f"Service {service_name} restarted successfully",
                "service_name": service_name,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to restart service {service_name}"
            )
    except Exception as e:
        logger.error(f"❌ Error restarting service {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error restarting service: {e}")


@router.get("/backup/status")
async def get_backup_status(current_admin: User = Depends(get_current_admin)):
    """Получить статус системы резервного копирования"""
    try:
        metrics = await backup_monitoring_service.get_system_metrics()
        health_report = await backup_monitoring_service.generate_health_report()
        
        return {
            "status": "success",
            "metrics": metrics,
            "health_report": health_report,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error getting backup status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Backup monitoring service unavailable",
            "timestamp": datetime.now().isoformat()
        }


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
