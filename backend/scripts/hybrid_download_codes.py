#!/usr/bin/env python3
"""
Скрипт для гибридной загрузки кодексов
Комбинирует PDF через API и HTML парсинг
"""

import sys
import os
import asyncio
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.hybrid_codes_downloader import HybridCodesDownloader

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

async def main():
    """Основная функция"""
    print("🚀 Гибридная загрузка кодексов РФ")
    print("=" * 60)
    print("📋 Методы: PDF через API + HTML парсинг")
    print("=" * 60)
    
    downloader = HybridCodesDownloader()
    
    try:
        summary = await downloader.download_all_codexes()
        
        print("\n" + "=" * 60)
        print("📊 РЕЗУЛЬТАТЫ:")
        print(f"   ✅ Успешно: {summary['successful']}/{summary['total_codexes']}")
        print(f"   ❌ Ошибок: {summary['failed']}")
        print(f"   📦 Общий размер: {summary['total_size_mb']} МБ")
        print("=" * 60)
        
        # Показываем методы, которые использовались
        methods = {}
        for result in summary['results']:
            if result.get('success'):
                method = result.get('method_used', 'unknown')
                methods[method] = methods.get(method, 0) + 1
        
        print("\n📊 Методы загрузки:")
        for method, count in methods.items():
            print(f"   {method}: {count}")
        
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

