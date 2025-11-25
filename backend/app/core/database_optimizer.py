"""
Сервис оптимизации базы данных
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import asynccontextmanager

from .config import settings
from .enhanced_logging import performance_logger


class DatabaseOptimizer:
    """Сервис оптимизации базы данных"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.engine = None
        self.session_factory = None
        self.connection_pool = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Инициализация оптимизированного движка БД"""
        try:
            # Оптимизированная конфигурация пула соединений
            pool_config = {
                "poolclass": QueuePool,
                "pool_size": 20,  # Увеличиваем размер пула
                "max_overflow": 30,  # Больше дополнительных соединений
                "pool_timeout": 30,  # Таймаут ожидания соединения
                "pool_recycle": 3600,  # Время жизни соединения
                "pool_reset_on_return": "commit",  # Сброс транзакций
                "pool_pre_ping": True,  # Проверка соединений
            }
            
            # Создаем движок с оптимизациями
            self.engine = create_engine(
                settings.DATABASE_URL,
                **pool_config,
                echo=settings.DEBUG
            )
            
            # Создаем фабрику сессий
            self.session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False  # Оптимизация для производительности
            )
            
            self.logger.info("✅ Database optimizer initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize database optimizer: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self):
        """Асинхронный контекстный менеджер для сессий БД"""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    async def optimize_queries(self) -> Dict[str, Any]:
        """Оптимизирует запросы к БД"""
        try:
            optimizations = {}
            
            async with self.get_session() as session:
                # Анализируем медленные запросы
                slow_queries = await self._analyze_slow_queries(session)
                optimizations["slow_queries"] = slow_queries
                
                # Оптимизируем индексы
                index_optimizations = await self._optimize_indexes(session)
                optimizations["index_optimizations"] = index_optimizations
                
                # Очищаем неиспользуемые данные
                cleanup_results = await self._cleanup_old_data(session)
                optimizations["cleanup_results"] = cleanup_results
            
            self.logger.info("✅ Database queries optimized successfully")
            return optimizations
            
        except Exception as e:
            self.logger.error(f"❌ Query optimization failed: {e}")
            return {"error": str(e)}
    
    async def _analyze_slow_queries(self, session) -> List[Dict[str, Any]]:
        """Анализирует медленные запросы"""
        try:
            # Получаем статистику запросов (если поддерживается)
            if settings.DATABASE_URL.startswith("postgresql"):
                query = text("""
                    SELECT query, mean_time, calls, total_time
                    FROM pg_stat_statements
                    WHERE mean_time > 1000
                    ORDER BY mean_time DESC
                    LIMIT 10
                """)
                
                result = session.execute(query)
                slow_queries = []
                
                for row in result:
                    slow_queries.append({
                        "query": row[0][:100] + "..." if len(row[0]) > 100 else row[0],
                        "mean_time": float(row[1]),
                        "calls": int(row[2]),
                        "total_time": float(row[3])
                    })
                
                return slow_queries
            else:
                # Для SQLite возвращаем пустой список
                return []
                
        except Exception as e:
            self.logger.warning(f"Slow query analysis not available: {e}")
            return []
    
    async def _optimize_indexes(self, session) -> Dict[str, Any]:
        """Оптимизирует индексы"""
        try:
            optimizations = {
                "indexes_created": 0,
                "indexes_dropped": 0,
                "recommendations": []
            }
            
            # Создаем индексы для часто используемых полей
            index_queries = [
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
                "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
                "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)",
                "CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin)",
                "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at)",
            ]
            
            for query in index_queries:
                try:
                    session.execute(text(query))
                    optimizations["indexes_created"] += 1
                except Exception as e:
                    self.logger.warning(f"Index creation failed: {e}")
            
            # Анализируем неиспользуемые индексы
            if settings.DATABASE_URL.startswith("postgresql"):
                unused_indexes_query = text("""
                    SELECT schemaname, tablename, indexname
                    FROM pg_stat_user_indexes
                    WHERE idx_scan = 0
                    AND indexname NOT LIKE '%_pkey'
                """)
                
                result = session.execute(unused_indexes_query)
                unused_indexes = [row[2] for row in result]
                
                if unused_indexes:
                    optimizations["recommendations"].append(
                        f"Consider dropping unused indexes: {', '.join(unused_indexes)}"
                    )
            
            return optimizations
            
        except Exception as e:
            self.logger.error(f"Index optimization failed: {e}")
            return {"error": str(e)}
    
    async def _cleanup_old_data(self, session) -> Dict[str, Any]:
        """Очищает старые данные"""
        try:
            cleanup_results = {
                "deleted_records": 0,
                "freed_space": 0
            }
            
            # Очищаем старые аудит логи (старше 90 дней)
            audit_cleanup_query = text("""
                DELETE FROM audit_logs 
                WHERE created_at < datetime('now', '-90 days')
            """)
            
            result = session.execute(audit_cleanup_query)
            cleanup_results["deleted_records"] += result.rowcount
            
            # Очищаем старые сессии чата (старше 30 дней)
            chat_cleanup_query = text("""
                DELETE FROM chat_sessions 
                WHERE created_at < datetime('now', '-30 days')
                AND (SELECT COUNT(*) FROM chat_messages WHERE session_id = chat_sessions.id) = 0
            """)
            
            result = session.execute(chat_cleanup_query)
            cleanup_results["deleted_records"] += result.rowcount
            
            # Выполняем VACUUM для SQLite
            if settings.DATABASE_URL.startswith("sqlite"):
                session.execute(text("VACUUM"))
                cleanup_results["freed_space"] = 1  # VACUUM освобождает место
            
            return cleanup_results
            
        except Exception as e:
            self.logger.error(f"Data cleanup failed: {e}")
            return {"error": str(e)}
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Получает статистику базы данных"""
        try:
            stats = {}
            
            async with self.get_session() as session:
                # Размер базы данных
                if settings.DATABASE_URL.startswith("sqlite"):
                    size_query = text("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                    result = session.execute(size_query)
                    stats["database_size_bytes"] = result.scalar()
                elif settings.DATABASE_URL.startswith("postgresql"):
                    size_query = text("SELECT pg_database_size(current_database())")
                    result = session.execute(size_query)
                    stats["database_size_bytes"] = result.scalar()
                
                # Количество таблиц
                tables_query = text("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                result = session.execute(tables_query)
                stats["table_count"] = result.scalar()
                
                # Количество записей в основных таблицах
                table_counts = {}
                tables = ["users", "chat_sessions", "chat_messages", "audit_logs"]
                
                for table in tables:
                    try:
                        count_query = text(f"SELECT COUNT(*) FROM {table}")
                        result = session.execute(count_query)
                        table_counts[table] = result.scalar()
                    except Exception:
                        table_counts[table] = 0
                
                stats["table_counts"] = table_counts
                
                # Статистика пула соединений
                stats["pool_stats"] = {
                    "pool_size": self.engine.pool.size(),
                    "checked_in": self.engine.pool.checkedin(),
                    "checked_out": self.engine.pool.checkedout(),
                    "overflow": self.engine.pool.overflow(),
                    "invalid": self.engine.pool.invalid()
                }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверяет здоровье базы данных"""
        try:
            start_time = asyncio.get_event_loop().time()
            
            async with self.get_session() as session:
                # Простой запрос для проверки соединения
                result = session.execute(text("SELECT 1"))
                test_result = result.scalar()
                
                response_time = asyncio.get_event_loop().time() - start_time
                
                health_status = {
                    "status": "healthy" if test_result == 1 else "unhealthy",
                    "response_time_ms": round(response_time * 1000, 2),
                    "connection_test": test_result == 1,
                    "timestamp": asyncio.get_event_loop().time()
                }
                
                # Логируем производительность
                performance_logger.log_performance(
                    operation="database_health_check",
                    duration=response_time
                )
                
                return health_status
                
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }
    
    def close(self):
        """Закрывает соединения"""
        try:
            if self.engine:
                self.engine.dispose()
            self.logger.info("✅ Database optimizer closed")
        except Exception as e:
            self.logger.error(f"Failed to close database optimizer: {e}")


# Глобальный экземпляр оптимизатора БД
database_optimizer = DatabaseOptimizer()
