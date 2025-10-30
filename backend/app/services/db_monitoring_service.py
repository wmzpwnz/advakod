"""
Сервис для мониторинга метрик базы данных
"""

import logging
import time
import sqlite3
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..core.database import engine, SessionLocal
from ..core.config import settings

logger = logging.getLogger(__name__)


class DatabaseMonitoringService:
    """Сервис мониторинга базы данных"""
    
    def __init__(self):
        self.metrics_history = []
        self.max_history_size = 1000
        
    def get_database_metrics(self) -> Dict[str, Any]:
        """Получает текущие метрики базы данных"""
        try:
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "database_type": "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql",
                "connection_pool": self._get_connection_pool_metrics(),
                "database_size": self._get_database_size(),
                "table_stats": self._get_table_statistics(),
                "performance": self._get_performance_metrics(),
                "health_status": "healthy"
            }
            
            # Добавляем в историю
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history.pop(0)
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения метрик БД: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "health_status": "error",
                "error": str(e)
            }
    
    def _get_connection_pool_metrics(self) -> Dict[str, Any]:
        """Метрики пула соединений"""
        try:
            pool = engine.pool
            
            return {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
        except Exception as e:
            logger.warning(f"⚠️ Не удалось получить метрики пула: {e}")
            return {"error": str(e)}
    
    def _get_database_size(self) -> Dict[str, Any]:
        """Размер базы данных"""
        try:
            if settings.DATABASE_URL.startswith("sqlite"):
                # SQLite размер файла
                db_path = settings.DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
                if db_path.startswith("./"):
                    db_path = os.path.join("backend", db_path[2:])
                
                if os.path.exists(db_path):
                    size_bytes = os.path.getsize(db_path)
                    return {
                        "size_bytes": size_bytes,
                        "size_mb": round(size_bytes / (1024 * 1024), 2),
                        "file_path": db_path
                    }
                else:
                    return {"error": "Database file not found"}
            else:
                # PostgreSQL размер через SQL
                with SessionLocal() as db:
                    result = db.execute(text("SELECT pg_database_size(current_database())")).scalar()
                    return {
                        "size_bytes": result,
                        "size_mb": round(result / (1024 * 1024), 2)
                    }
                    
        except Exception as e:
            logger.warning(f"⚠️ Не удалось получить размер БД: {e}")
            return {"error": str(e)}
    
    def _get_table_statistics(self) -> Dict[str, Any]:
        """Статистика по таблицам"""
        try:
            stats = {}
            
            with SessionLocal() as db:
                if settings.DATABASE_URL.startswith("sqlite"):
                    # SQLite статистика
                    tables_query = text("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = db.execute(tables_query).fetchall()
                    
                    for table in tables:
                        table_name = table[0]
                        try:
                            # Безопасный запрос для SQLite
                            count_query = text(f"SELECT COUNT(*) FROM `{table_name}`")
                            count = db.execute(count_query).scalar()
                            stats[table_name] = {"row_count": count}
                        except Exception as table_error:
                            logger.warning(f"⚠️ Error getting count for table {table_name}: {table_error}")
                            stats[table_name] = {"row_count": 0, "error": str(table_error)}
                        
                else:
                    # PostgreSQL статистика
                    query = text("""
                        SELECT 
                            schemaname,
                            tablename,
                            n_tup_ins as inserts,
                            n_tup_upd as updates,
                            n_tup_del as deletes,
                            n_live_tup as live_rows,
                            n_dead_tup as dead_rows
                        FROM pg_stat_user_tables
                    """)
                    
                    results = db.execute(query).fetchall()
                    for row in results:
                        stats[row.tablename] = {
                            "inserts": row.inserts,
                            "updates": row.updates,
                            "deletes": row.deletes,
                            "live_rows": row.live_rows,
                            "dead_rows": row.dead_rows
                        }
            
            return stats
            
        except Exception as e:
            logger.warning(f"⚠️ Не удалось получить статистику таблиц: {e}")
            return {"error": str(e), "connection_issue": "postgres" in str(e).lower()}
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Метрики производительности"""
        try:
            # Простой тест производительности
            start_time = time.time()
            
            with SessionLocal() as db:
                # Простой запрос для измерения времени отклика
                db.execute(text("SELECT 1")).scalar()
            
            query_time = time.time() - start_time
            
            return {
                "query_response_time_ms": round(query_time * 1000, 2),
                "status": "fast" if query_time < 0.1 else "slow" if query_time < 1.0 else "very_slow"
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Не удалось получить метрики производительности: {e}")
            return {"error": str(e)}
    
    def get_health_check(self) -> Dict[str, Any]:
        """Проверка здоровья базы данных"""
        try:
            start_time = time.time()
            
            with SessionLocal() as db:
                # Проверяем подключение
                db.execute(text("SELECT 1")).scalar()
                
                # Проверяем основные таблицы
                tables_to_check = ["users", "chat_sessions", "chat_messages"]
                table_status = {}
                
                for table in tables_to_check:
                    try:
                        if settings.DATABASE_URL.startswith("sqlite"):
                            # SQLite безопасный запрос
                            count = db.execute(text(f"SELECT COUNT(*) FROM `{table}`")).scalar()
                        else:
                            # PostgreSQL безопасный запрос
                            count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                        table_status[table] = {"status": "ok", "count": count}
                    except Exception as e:
                        table_status[table] = {"status": "error", "error": str(e)}
            
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "timestamp": datetime.now().isoformat(),
                "tables": table_status,
                "database_type": "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql"
            }
            
        except Exception as e:
            logger.error(f"❌ Проверка здоровья БД не удалась: {e}")
            
            # Определяем тип ошибки для более информативного ответа
            error_type = "connection_error"
            if "postgres" in str(e).lower() and "name resolution" in str(e).lower():
                error_type = "postgres_connection_error"
            elif "sqlite" in str(e).lower():
                error_type = "sqlite_error"
            
            return {
                "status": "unhealthy",
                "error": str(e),
                "error_type": error_type,
                "timestamp": datetime.now().isoformat(),
                "database_type": "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql"
            }
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Получает сводку метрик за указанный период"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            recent_metrics = [
                m for m in self.metrics_history
                if datetime.fromisoformat(m["timestamp"]) > cutoff_time
            ]
            
            if not recent_metrics:
                return {"status": "no_data", "period_hours": hours}
            
            # Анализируем метрики
            response_times = [
                m.get("performance", {}).get("query_response_time_ms", 0)
                for m in recent_metrics
                if "performance" in m and "query_response_time_ms" in m["performance"]
            ]
            
            sizes = [
                m.get("database_size", {}).get("size_mb", 0)
                for m in recent_metrics
                if "database_size" in m and "size_mb" in m["database_size"]
            ]
            
            return {
                "status": "ok",
                "period_hours": hours,
                "metrics_count": len(recent_metrics),
                "performance": {
                    "avg_response_time_ms": round(sum(response_times) / len(response_times), 2) if response_times else 0,
                    "max_response_time_ms": max(response_times) if response_times else 0,
                    "min_response_time_ms": min(response_times) if response_times else 0
                },
                "storage": {
                    "current_size_mb": sizes[-1] if sizes else 0,
                    "growth_mb": (sizes[-1] - sizes[0]) if len(sizes) > 1 else 0
                },
                "latest_check": recent_metrics[-1]["timestamp"]
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа метрик: {e}")
            return {"status": "error", "error": str(e)}


# Создаем глобальный экземпляр
db_monitoring_service = DatabaseMonitoringService()
