#!/usr/bin/env python3
"""
Скрипт для полной очистки векторной базы данных
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from app.services.vector_store_service import vector_store_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_all_documents():
    """Полностью очищает векторную базу данных"""
    try:
        # Инициализируем векторную базу данных
        if not vector_store_service.is_ready():
            vector_store_service.initialize()
        
        collection = vector_store_service.collection
        total_docs = collection.count()
        
        print(f"📊 Найдено документов: {total_docs}")
        
        if total_docs == 0:
            print("📄 Векторная база данных уже пуста")
            return
        
        # Удаляем все документы
        print(f"🗑️  Удаляем все {total_docs} документов...")
        
        # Получаем все ID документов
        results = collection.get(limit=total_docs, include=['metadatas'])
        all_ids = results['ids']
        
        # Удаляем все документы
        collection.delete(ids=all_ids)
        
        # Проверяем результат
        remaining_docs = collection.count()
        print(f"✅ Удалено документов: {total_docs - remaining_docs}")
        print(f"📊 Осталось документов: {remaining_docs}")
        
    except Exception as e:
        logger.error(f"Ошибка очистки документов: {e}")
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    clear_all_documents()
