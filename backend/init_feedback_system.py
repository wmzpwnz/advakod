"""
Скрипт инициализации системы обратной связи и модерации
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.feedback import ProblemCategory, DEFAULT_PROBLEM_CATEGORIES
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_problem_categories():
    """Инициализация категорий проблем"""
    db = SessionLocal()
    
    try:
        logger.info("🔄 Инициализация категорий проблем...")
        
        # Проверяем, есть ли уже категории
        existing_count = db.query(ProblemCategory).count()
        
        if existing_count > 0:
            logger.info(f"✅ Категории уже существуют ({existing_count} шт.)")
            return
        
        # Создаем категории
        for cat_data in DEFAULT_PROBLEM_CATEGORIES:
            category = ProblemCategory(**cat_data)
            db.add(category)
        
        db.commit()
        logger.info(f"✅ Создано {len(DEFAULT_PROBLEM_CATEGORIES)} категорий проблем")
        
        # Выводим список
        categories = db.query(ProblemCategory).order_by(ProblemCategory.display_order).all()
        logger.info("\n📋 Список категорий:")
        for cat in categories:
            logger.info(f"  {cat.icon} {cat.display_name} (severity: {cat.severity})")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("🚀 Запуск инициализации системы обратной связи")
    init_problem_categories()
    logger.info("✅ Инициализация завершена!")
