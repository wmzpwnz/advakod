#!/usr/bin/env python3
"""
Полный процесс скачивания и интеграции кодексов
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.codes_downloader import CodesDownloader
from app.services.codes_rag_integration import CodesRAGIntegration

def main():
    """Основная функция"""
    print("🚀 Запуск полного процесса кодексов...")
    
    # Этап 1: Скачивание
    print("\n📥 ЭТАП 1: СКАЧИВАНИЕ КОДЕКСОВ")
    downloader = CodesDownloader()
    
    try:
        success_count, total_count = downloader.download_all_codexes()
        print(f"✅ Скачивание завершено: {success_count}/{total_count} кодексов")
        
        if success_count == 0:
            print("❌ Не скачано ни одного кодекса")
            return 1
        
        # Этап 2: Интеграция с RAG
        print("\n🔗 ЭТАП 2: ИНТЕГРАЦИЯ С RAG СИСТЕМОЙ")
        rag_integration = CodesRAGIntegration()
        
        integration_result = rag_integration.integrate_all_codexes()
        
        if integration_result['success']:
            print(f"✅ Интеграция завершена: {integration_result['processed_files']} файлов")
            print(f"📊 Создано чанков: {integration_result['total_chunks']}")
        else:
            print(f"❌ Ошибка интеграции: {integration_result['error']}")
            return 1
        
        print("\n🎉 Полный процесс завершен успешно!")
        return 0
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())


