#!/usr/bin/env python3
"""
Скрипт для очистки тестовых документов из векторной базы данных
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from app.services.vector_store_service import vector_store_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_test_documents():
    """Удаляет тестовые документы из векторной базы данных"""
    try:
        # Инициализируем векторную базу данных
        if not vector_store_service.is_ready():
            vector_store_service.initialize()
        
        collection = vector_store_service.collection
        total_docs = collection.count()
        
        if total_docs == 0:
            print("📄 Векторная база данных пуста")
            return
        
        print(f"📊 Найдено документов: {total_docs}")
        
        # Получаем все документы с метаданными
        results = collection.get(
            limit=total_docs,
            include=['metadatas', 'documents']
        )
        
        # Находим тестовые документы
        test_doc_ids = []
        real_doc_ids = []
        
        for i, (doc_id, meta) in enumerate(zip(results['ids'], results['metadatas'])):
            filename = meta.get('filename', '')
            
            # Определяем тестовые документы по имени файла
            if (filename.startswith('tmp') or 
                filename == 'Unknown' or 
                'test' in filename.lower() or
                meta.get('file_size', 0) == 0):
                test_doc_ids.append(doc_id)
                print(f"🗑️  Тестовый документ: {filename} (ID: {doc_id})")
            else:
                real_doc_ids.append(doc_id)
                print(f"✅ Реальный документ: {filename} (ID: {doc_id})")
        
        print(f"\n📊 Статистика:")
        print(f"   Тестовых документов: {len(test_doc_ids)}")
        print(f"   Реальных документов: {len(real_doc_ids)}")
        
        if test_doc_ids:
            # Удаляем тестовые документы
            print(f"\n🗑️  Удаляем {len(test_doc_ids)} тестовых документов...")
            collection.delete(ids=test_doc_ids)
            print("✅ Тестовые документы удалены")
        else:
            print("✅ Тестовых документов не найдено")
        
        # Проверяем результат
        remaining_docs = collection.count()
        print(f"\n📊 Осталось документов: {remaining_docs}")
        
        if remaining_docs > 0:
            # Показываем оставшиеся документы
            remaining_results = collection.get(
                limit=remaining_docs,
                include=['metadatas']
            )
            
            print("\n📄 Оставшиеся документы:")
            for i, (doc_id, meta) in enumerate(zip(remaining_results['ids'], remaining_results['metadatas'])):
                filename = meta.get('filename', 'Unknown')
                doc_type = meta.get('document_type', 'unknown')
                pages = meta.get('pages', 'неизвестно')
                file_size = meta.get('file_size', 0)
                print(f"   {i+1}. {filename}")
                print(f"      Тип: {doc_type}, Страниц: {pages}, Размер: {file_size} байт")
        
    except Exception as e:
        logger.error(f"Ошибка очистки тестовых документов: {e}")
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    cleanup_test_documents()
