#!/usr/bin/env python3
"""
Автоматическое удаление всех старых заглушек кодексов из системы
Работает напрямую с ChromaDB и Simple RAG, без API
"""

import sys
import os
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
from app.services.vector_store_service import vector_store_service
from app.services.simple_expert_rag import simple_expert_rag

# Список старых заглушек для удаления
OLD_CODEXES = [
    "0001201412140001",  # Трудовой кодекс РФ
    "0001201412140002",  # Семейный кодекс РФ
    "0001201412140003",  # Жилищный кодекс РФ
    "0001201412140004",  # Налоговый кодекс РФ
    "0001201412140005",  # Бюджетный кодекс РФ
    "0001201412140006",  # Кодекс об административных правонарушениях РФ
    "0001201410140002",  # Гражданский кодекс РФ (часть 1) - заглушка
    "0001201905010039",  # Налоговый кодекс РФ (часть 1) - заглушка
    "0001202203030006",  # Уголовный кодекс РФ - заглушка
    "198",
    "289-11",
]

async def cleanup_stubs():
    """Удаляет все заглушки из системы"""
    print("="*60)
    print("🧹 Автоматическая очистка старых заглушек кодексов")
    print("="*60)
    print()
    
    # Инициализируем vector store
    print("🔧 Инициализация vector store...")
    try:
        vector_store_service.initialize()
        import time
        time.sleep(2)  # Даем время на инициализацию
    except Exception as e:
        print(f"⚠️ Предупреждение при инициализации: {e}")
    
    if not vector_store_service.is_ready():
        print("⚠️ Vector store не готов, но продолжаем удаление из файловой системы...")
        # Продолжаем удаление файлов даже если vector store не готов
    
    collection = vector_store_service.collection
    
    # Получаем все документы
    print("📋 Получаем список документов из ChromaDB...")
    all_docs = collection.get(include=['metadatas'])
    
    if not all_docs['ids']:
        print("✅ Документов не найдено")
        return
    
    print(f"✅ Найдено документов: {len(all_docs['ids'])}\n")
    
    # Находим документы для удаления
    documents_to_delete = []
    
    for i, doc_id in enumerate(all_docs['ids']):
        metadata = all_docs['metadatas'][i] if all_docs['metadatas'] else {}
        filename = metadata.get('filename', '') or metadata.get('file_name', '') or str(doc_id)
        source_path = metadata.get('source_path', '')
        file_size = metadata.get('size', 0) or metadata.get('file_size', 0) or 0
        
        should_delete = False
        reason = ""
        
        # Проверяем по ID или имени файла
        for old_id in OLD_CODEXES:
            if old_id in str(doc_id) or old_id in filename or old_id in source_path:
                should_delete = True
                reason = f"Старая заглушка (ID: {old_id})"
                break
        
        # Проверяем маленькие файлы кодексов
        if not should_delete and file_size <= 1000:
            title = (metadata.get('title', '') or metadata.get('name', '') or '').lower()
            if any(kw in title for kw in ["кодекс", "codex"]):
                should_delete = True
                reason = f"Маленький файл кодекса ({file_size} байт)"
        
        if should_delete:
            documents_to_delete.append({
                "id": doc_id,
                "filename": filename,
                "title": metadata.get('title', metadata.get('name', 'Unknown')),
                "size": file_size,
                "reason": reason
            })
    
    if not documents_to_delete:
        print("✅ Старые заглушки не найдены!\n")
        return
    
    print(f"🗑️ Найдено документов для удаления: {len(documents_to_delete)}\n")
    
    # Показываем список
    for i, doc in enumerate(documents_to_delete, 1):
        print(f"{i}. {doc['title']}")
        print(f"   ID: {doc['id']}")
        print(f"   Файл: {doc['filename']}")
        print(f"   Размер: {doc['size']} байт")
        print(f"   Причина: {doc['reason']}\n")
    
    print("🗑️ Удаляем документы...\n")
    
    # Удаляем из ChromaDB
    ids_to_delete = [doc['id'] for doc in documents_to_delete]
    collection.delete(ids=ids_to_delete)
    print(f"✅ Удалено из ChromaDB: {len(ids_to_delete)} документов")
    
    # Удаляем из Simple RAG
    simple_rag_deleted = 0
    simple_rag_chunks = 0
    
    for doc in documents_to_delete:
        try:
            # Пробуем удалить по ID
            result = await simple_expert_rag.delete_document(doc['id'])
            if result.get('success', False):
                simple_rag_deleted += 1
                simple_rag_chunks += result.get('chunks_deleted', 0)
            else:
                # Пробуем удалить по имени файла
                if doc['filename']:
                    result = await simple_expert_rag.delete_document(doc['filename'])
                    if result.get('success', False):
                        simple_rag_deleted += 1
                        simple_rag_chunks += result.get('chunks_deleted', 0)
        except Exception as e:
            print(f"⚠️ Ошибка удаления {doc['id']} из Simple RAG: {e}")
    
    print(f"✅ Удалено из Simple RAG: {simple_rag_deleted} документов, {simple_rag_chunks} чанков")
    
    # Удаляем файлы из файловой системы
    files_deleted = 0
    possible_paths = [
        "/app/data/codes_downloads",
        "/app/downloaded_codexes",
        "/app/data/downloaded_codexes",
        "/root/advakod/data/codes_downloads",
        "/root/advakod/downloaded_codexes",
    ]
    
    for doc in documents_to_delete:
        filename = doc['filename']
        if not filename:
            continue
        
        for base_path in possible_paths:
            base = Path(base_path)
            if not base.exists():
                continue
            
            # Ищем файл
            for file_path in base.rglob(filename):
                try:
                    file_path.unlink()
                    files_deleted += 1
                    print(f"   Удален файл: {file_path}")
                    # Удаляем связанные файлы (JSON метаданные)
                    json_file = file_path.with_suffix('.json')
                    if json_file.exists():
                        json_file.unlink()
                        print(f"   Удален JSON: {json_file}")
                except Exception as e:
                    print(f"⚠️ Ошибка удаления файла {file_path}: {e}")
    
    # Итоги
    print("\n" + "="*60)
    print(f"✅ Успешно удалено:")
    print(f"   - ChromaDB: {len(documents_to_delete)} документов")
    print(f"   - Simple RAG: {simple_rag_deleted} документов, {simple_rag_chunks} чанков")
    print(f"   - Файлы: {files_deleted} файлов")
    print("="*60)
    print("\n✅ Очистка завершена!")

def main():
    """Главная функция"""
    asyncio.run(cleanup_stubs())

if __name__ == "__main__":
    main()

