#!/usr/bin/env python3
"""
Скрипт для получения метаданных из API для всех документов, у которых их нет
"""
import sys
import os
import asyncio
import aiohttp
import json
from pathlib import Path
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.codes_downloader import CodesDownloader

async def fetch_missing_metadata():
    """Получает метаданные для всех документов, у которых их нет"""
    codes_dir = Path("data/codes_downloads")
    
    # Список кодексов для получения правильных названий
    codex_names = {
        '0001201410140002': 'Гражданский кодекс РФ',
        '0001202203030006': 'Уголовный кодекс РФ',
        '0001201412140001': 'Трудовой кодекс РФ',
        '0001201412140002': 'Семейный кодекс РФ',
        '0001201412140003': 'Жилищный кодекс РФ',
        '0001201412140004': 'Налоговый кодекс РФ',
        '0001201412140005': 'Бюджетный кодекс РФ',
        '0001201412140006': 'Кодекс об административных правонарушениях РФ'
    }
    
    if not codes_dir.exists():
        print(f"❌ Директория {codes_dir} не существует")
        return
    
    # Находим все .txt файлы
    txt_files = list(codes_dir.glob("*.txt"))
    print(f"📄 Найдено {len(txt_files)} документов\n")
    
    async with CodesDownloader(output_dir=str(codes_dir)) as downloader:
        fetched_count = 0
        skipped_count = 0
        
        for txt_file in txt_files:
            eo_number = txt_file.stem
            json_file = txt_file.with_suffix('.json')
            
            # Проверяем, есть ли уже JSON файл
            if json_file.exists():
                print(f"⏭️  {eo_number}: метаданные уже есть")
                skipped_count += 1
                continue
            
            print(f"📥 Получение метаданных для {eo_number}...")
            
            # Получаем метаданные из API
            metadata = await downloader._get_document_metadata(eo_number)
            
            if metadata:
                # Добавляем имя кодекса
                metadata["codex_name"] = codex_names.get(eo_number, "Неизвестный кодекс")
                metadata["file_path"] = str(txt_file)
                metadata["file_name"] = txt_file.name
                
                # Сохраняем в JSON
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                
                print(f"✅ {eo_number}: метаданные сохранены ({metadata.get('name', 'unknown')[:50]}...)")
                fetched_count += 1
            else:
                print(f"⚠️  {eo_number}: не удалось получить метаданные")
            
            # Пауза между запросами
            await asyncio.sleep(1)
    
    print(f"\n📊 Итого:")
    print(f"   ✅ Получено: {fetched_count}")
    print(f"   ⏭️  Пропущено: {skipped_count}")
    print(f"   📄 Всего документов: {len(txt_files)}")

if __name__ == "__main__":
    asyncio.run(fetch_missing_metadata())




