#!/usr/bin/env python3
"""
Прямое удаление заглушек из файловой системы и Simple RAG
"""

import sys
import os
from pathlib import Path
import asyncio

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.simple_expert_rag import simple_expert_rag

# Список старых заглушек
OLD_CODEXES = [
    "0001201412140001",
    "0001201412140002",
    "0001201412140003",
    "0001201412140004",
    "0001201412140005",
    "0001201412140006",
    "0001201410140002",
    "0001201905010039",
    "0001202203030006",
    "198",
    "289-11",
]

async def cleanup_files_and_rag():
    """Удаляет заглушки из файловой системы и Simple RAG"""
    print("="*60)
    print("🧹 Удаление заглушек из файловой системы и Simple RAG")
    print("="*60)
    print()
    
    # Пути для поиска файлов
    possible_paths = [
        "/app/data/codes_downloads",
        "/app/downloaded_codexes",
        "/app/data/downloaded_codexes",
        "/root/advakod/data/codes_downloads",
        "/root/advakod/downloaded_codexes",
    ]
    
    files_deleted = 0
    simple_rag_deleted = 0
    simple_rag_chunks = 0
    
    # Удаляем файлы
    print("📁 Удаление файлов...")
    for old_id in OLD_CODEXES:
        for base_path in possible_paths:
            base = Path(base_path)
            if not base.exists():
                continue
            
            # Ищем файлы с этим ID
            for file_path in base.rglob(f"*{old_id}*"):
                try:
                    if file_path.is_file():
                        file_path.unlink()
                        files_deleted += 1
                        print(f"   ✅ Удален: {file_path}")
                        
                        # Удаляем JSON метаданные
                        json_file = file_path.with_suffix('.json')
                        if json_file.exists():
                            json_file.unlink()
                            print(f"   ✅ Удален JSON: {json_file}")
                except Exception as e:
                    print(f"   ⚠️ Ошибка удаления {file_path}: {e}")
    
    # Удаляем маленькие файлы кодексов (<= 1000 байт)
    print("\n📁 Удаление маленьких файлов кодексов (<= 1000 байт)...")
    for base_path in possible_paths:
        base = Path(base_path)
        if not base.exists():
            continue
        
        for file_path in base.rglob("*.txt"):
            try:
                if file_path.stat().st_size <= 1000:
                    # Проверяем, что это кодекс (по содержимому или имени)
                    content_preview = file_path.read_text(encoding='utf-8', errors='ignore')[:200].lower()
                    filename_lower = file_path.name.lower()
                    
                    if any(kw in content_preview or kw in filename_lower for kw in ["кодекс", "codex"]):
                        file_path.unlink()
                        files_deleted += 1
                        print(f"   ✅ Удален маленький файл: {file_path} ({file_path.stat().st_size if file_path.exists() else 0} байт)")
                        
                        json_file = file_path.with_suffix('.json')
                        if json_file.exists():
                            json_file.unlink()
            except Exception as e:
                pass  # Файл уже удален или ошибка
    
    # Удаляем из Simple RAG
    print("\n🗄️ Удаление из Simple RAG...")
    for old_id in OLD_CODEXES:
        # Пробуем удалить по ID
        try:
            result = await simple_expert_rag.delete_document(old_id)
            if result.get('success', False):
                simple_rag_deleted += 1
                chunks = result.get('chunks_deleted', 0)
                simple_rag_chunks += chunks
                print(f"   ✅ Удален из Simple RAG: {old_id} (чанков: {chunks})")
        except Exception as e:
            print(f"   ⚠️ Ошибка удаления {old_id} из Simple RAG: {e}")
    
    # Итоги
    print("\n" + "="*60)
    print(f"✅ Удалено:")
    print(f"   - Файлов: {files_deleted}")
    print(f"   - Simple RAG: {simple_rag_deleted} документов, {simple_rag_chunks} чанков")
    print("="*60)
    print("\n✅ Очистка завершена!")

def main():
    asyncio.run(cleanup_files_and_rag())

if __name__ == "__main__":
    main()

