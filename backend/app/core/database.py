from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import logging
from .config import settings

logger = logging.getLogger(__name__)

# Определяем настройки движка в зависимости от типа БД
def get_engine_config():
    """Возвращает настройки движка в зависимости от типа базы данных"""
    if settings.DATABASE_URL.startswith("sqlite"):
        # SQLite настройки (для разработки)
        return {
            "pool_pre_ping": True,
            "echo": settings.DEBUG,
            "connect_args": {"check_same_thread": False}  # Для SQLite
        }
    else:
        # PostgreSQL настройки (для продакшена)
        return {
            "pool_pre_ping": True,
            "echo": settings.DEBUG,
            "pool_size": 20,  # Увеличенный размер пула для PostgreSQL
            "max_overflow": 30,  # Больше дополнительных соединений
            "pool_timeout": 30,  # Таймаут ожидания соединения
            "pool_recycle": 3600,  # Время жизни соединения
            "pool_reset_on_return": "commit"  # Сброс транзакций при возврате
        }

# Создание движка базы данных с оптимизированными настройками
engine = create_engine(settings.DATABASE_URL, **get_engine_config())

# Создание фабрики сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()


def get_db():
    """Зависимость для получения сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Инициализация базы данных"""
    try:
        # Импортируем все модели здесь для создания таблиц
        from app.models import user, chat, feedback, analytics
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

