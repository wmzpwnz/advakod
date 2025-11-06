#!/usr/bin/env python3
"""Перезагрузить Трудовой кодекс в ChromaDB"""
import sys
import os
sys.path.insert(0, '/app')

from app.services.vector_store_service import vector_store_service
from app.services.embeddings_service import embeddings_service
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reload_tk_codex():
    """Перезагрузить Трудовой кодекс"""
    file_path = Path("/app/data/codes_downloads/Трудовой_кодекс_РФ.txt")
    
    if not file_path.exists():
        logger.error(f"Файл не найден: {file_path}")
        return
    
    file_size = file_path.stat().st_size
    logger.info(f"Файл найден: {file_path}, размер: {file_size} bytes")
    
    if file_size < 100000:
        logger.warning(f"⚠️ Файл слишком маленький ({file_size} bytes), возможно неполный")
    
    # Инициализируем сервисы
    vector_store_service.initialize()
    
    # Читаем файл
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"Файл прочитан: {len(content)} символов")
        
        # Разбиваем на чанки (если большой)
        chunk_size = 1000  # символов
        chunks = []
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i+chunk_size]
            chunks.append(chunk)
        
        logger.info(f"Разбито на {len(chunks)} чанков")
        
        # Загружаем через vector_store_service.add_document
        metadata = {
            'filename': file_path.name,
            'source_path': str(file_path),
            'size': file_size,
            'type': 'legal_document',
            'language': 'ru',
            'upload_date': datetime.now().isoformat()
        }
        
        # Загружаем документ
        result = vector_store_service.add_document(
            content=content,
            metadata=metadata,
            document_id=f"tk_codex_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        logger.info(f"✅ Файл перезагружен: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    reload_tk_codex()
