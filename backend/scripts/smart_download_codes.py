#!/usr/bin/env python3
"""
Скрипт для умной загрузки полных кодексов через API pravo.gov.ru
"""

import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.smart_codes_downloader import SmartCodesDownloader

async def main():
    """Основная функция"""
    print("🚀 Умная загрузка полных кодексов РФ")
    print("=" * 60)
    
    downloader = SmartCodesDownloader()
    
    try:
        summary = await downloader.download_all_codexes()
        
        print("\n" + "=" * 60)
        print("📊 РЕЗУЛЬТАТЫ:")
        print(f"   ✅ Успешно: {summary['successful']}/{summary['total_codexes']}")
        print(f"   ❌ Ошибок: {summary['failed']}")
        print(f"   📦 Общий размер: {summary['total_size_mb']} МБ")
        print("=" * 60)
        
        if summary['successful'] > 0:
            print("\n✅ Загрузка завершена успешно!")
            return 0
        else:
            print("\n❌ Не удалось загрузить ни одного кодекса")
            return 1
            
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

