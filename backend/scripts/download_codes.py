#!/usr/bin/env python3
"""
Скрипт для скачивания кодексов
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.codes_downloader import CodesDownloader

def main():
    """Основная функция"""
    print("🚀 Запуск скачивания кодексов...")
    
    downloader = CodesDownloader()
    
    try:
        success_count, total_count = downloader.download_all_codexes()
        
        print(f"✅ Скачивание завершено: {success_count}/{total_count} кодексов")
        
        # Получаем статус
        status = downloader.get_status()
        print(f"📊 Статус:")
        print(f"Всего файлов: {status['total_files']}")
        print(f"Общий размер: {status['total_size']:,} байт")
        
        return 0 if success_count == total_count else 1
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())


