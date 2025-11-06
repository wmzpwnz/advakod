"""
Кэш удаленных документов для предотвращения их повторного отображения
"""
import json
import os
from pathlib import Path
from typing import Set
import logging

logger = logging.getLogger(__name__)

class DeletedDocumentsCache:
    """Кэш для хранения информации об удаленных документах"""
    
    def __init__(self, cache_file: str = "/app/data/deleted_documents.json"):
        self.cache_file = Path(cache_file)
        self.deleted_ids: Set[str] = set()
        self.deleted_filenames: Set[str] = set()
        self._load_cache()
    
    def _load_cache(self):
        """Загружает кэш из файла"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.deleted_ids = set(data.get('ids', []))
                    self.deleted_filenames = set(data.get('filenames', []))
                logger.info(f"Загружен кэш удаленных документов: {len(self.deleted_ids)} ID, {len(self.deleted_filenames)} имен файлов")
        except Exception as e:
            logger.warning(f"Ошибка загрузки кэша удаленных документов: {e}")
            self.deleted_ids = set()
            self.deleted_filenames = set()
    
    def _save_cache(self):
        """Сохраняет кэш в файл"""
        try:
            # Создаем директорию если не существует
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'ids': list(self.deleted_ids),
                    'filenames': list(self.deleted_filenames)
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения кэша удаленных документов: {e}")
    
    def mark_deleted(self, document_id: str = None, filename: str = None):
        """Помечает документ как удаленный"""
        if document_id:
            self.deleted_ids.add(document_id)
        if filename:
            self.deleted_filenames.add(filename)
        self._save_cache()
        logger.info(f"Документ помечен как удаленный: ID={document_id}, filename={filename}")
    
    def is_deleted(self, document_id: str = None, filename: str = None) -> bool:
        """Проверяет, удален ли документ"""
        if document_id and document_id in self.deleted_ids:
            return True
        if filename and filename in self.deleted_filenames:
            return True
        return False
    
    def clear(self):
        """Очищает кэш"""
        self.deleted_ids.clear()
        self.deleted_filenames.clear()
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
        except Exception as e:
            logger.warning(f"Ошибка удаления файла кэша: {e}")

# Глобальный экземпляр
deleted_documents_cache = DeletedDocumentsCache()

