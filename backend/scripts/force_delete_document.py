#!/usr/bin/env python3
"""Принудительное удаление документа по имени файла"""
import sys
import os
sys.path.insert(0, '/app')

from app.services.vector_store_service import vector_store_service
from app.services.deleted_documents_cache import deleted_documents_cache
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_delete_document(filename: str):
    """Принудительно удаляет документ по имени файла"""
    logger.info(f"🗑️ Принудительное удаление документа: {filename}")
    
    # 1. Инициализируем сервисы
    vector_store_service.initialize()
    
    # 2. Удаляем из файловой системы
    files_deleted = []
    possible_paths = [
        "/app/data/codes_downloads",
        "/app/downloaded_codexes",
        "/app/data/downloaded_codexes"
    ]
    
    for base_path in possible_paths:
        try:
            base_dir = Path(base_path)
            if base_dir.exists():
                for file_path in base_dir.rglob(filename):
                    if file_path.exists() and file_path.is_file():
                        file_path.unlink()
                        files_deleted.append(str(file_path))
                        logger.info(f"🗑️ Удален файл: {file_path}")
                        # Также удаляем JSON метаданные если есть
                        json_path = file_path.with_suffix('.json')
                        if json_path.exists():
                            json_path.unlink()
                            files_deleted.append(str(json_path))
        except Exception as e:
            logger.warning(f"Ошибка поиска файла в {base_path}: {e}")
    
    # 3. Помечаем в кэше удаленных документов
    try:
        filename_stem = Path(filename).stem
        deleted_documents_cache.mark_deleted(filename=filename, document_id=filename_stem)
        logger.info(f"✅ Документ помечен как удаленный в кэше")
    except Exception as e:
        logger.warning(f"Ошибка добавления в кэш: {e}")
    
    # 4. Пробуем удалить из ChromaDB (если можем получить доступ)
    try:
        collection = vector_store_service.collection
        # Пробуем удалить напрямую по имени файла как ID
        try:
            collection.delete(ids=[filename, filename_stem])
            logger.info(f"✅ Удалено из ChromaDB по ID: {filename}, {filename_stem}")
        except Exception as e:
            logger.warning(f"Не удалось удалить из ChromaDB напрямую: {e}")
    except Exception as e:
        logger.warning(f"Ошибка доступа к ChromaDB: {e}")
    
    logger.info(f"✅ Удаление завершено. Удалено файлов: {len(files_deleted)}")
    return files_deleted

if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else "Трудовой_кодекс_РФ.txt"
    force_delete_document(filename)

