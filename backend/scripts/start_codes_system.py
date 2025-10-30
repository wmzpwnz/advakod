#!/usr/bin/env python3
"""
Главный скрипт для запуска системы кодексов
"""

import sys
import os
import time
import signal
import logging
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.codes_downloader import CodesDownloader
from app.services.codes_rag_integration import CodesRAGIntegration
from app.services.codes_monitor import CodesMonitor

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('codes_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CodesSystemManager:
    def __init__(self):
        self.downloader = CodesDownloader()
        self.rag_integration = CodesRAGIntegration()
        self.monitor = CodesMonitor()
        self.running = True
        
        # Обработка сигналов
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        logger.info(f"Получен сигнал {signum}, завершение работы...")
        self.running = False

    def initialize_system(self):
        """Инициализация системы"""
        logger.info("🔧 Инициализация системы кодексов...")
        
        # Проверка директорий
        output_dir = Path(self.downloader.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        logger.info("✅ Система инициализирована")

    def run_download_cycle(self):
        """Запуск цикла скачивания"""
        logger.info("📥 Запуск цикла скачивания...")
        
        try:
            success_count, total_count = self.downloader.download_all_codexes()
            logger.info(f"✅ Цикл скачивания завершен: {success_count}/{total_count}")
            return success_count > 0
        except Exception as e:
            logger.error(f"❌ Ошибка в цикле скачивания: {e}")
            return False

    def run_integration_cycle(self):
        """Запуск цикла интеграции"""
        logger.info("🔗 Запуск цикла интеграции...")
        
        try:
            result = self.rag_integration.integrate_all_codexes()
            if result['success']:
                logger.info(f"✅ Цикл интеграции завершен: {result['processed_files']} файлов")
                return True
            else:
                logger.error(f"❌ Ошибка интеграции: {result['error']}")
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка в цикле интеграции: {e}")
            return False

    def run_monitoring_cycle(self):
        """Запуск цикла мониторинга"""
        logger.info("📊 Запуск цикла мониторинга...")
        
        try:
            status = self.monitor.get_system_status()
            logger.info(f"📈 Статус системы: {status}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка мониторинга: {e}")
            return False

    def run_system(self):
        """Основной цикл работы системы"""
        logger.info("🚀 Запуск системы кодексов")
        
        self.initialize_system()
        
        cycle_count = 0
        
        while self.running:
            cycle_count += 1
            logger.info(f"🔄 Цикл #{cycle_count}")
            
            # Скачивание
            download_success = self.run_download_cycle()
            
            # Интеграция (только если есть новые файлы)
            if download_success:
                integration_success = self.run_integration_cycle()
            else:
                logger.info("⏭️ Пропуск интеграции - нет новых файлов")
                integration_success = True
            
            # Мониторинг
            self.run_monitoring_cycle()
            
            # Пауза между циклами
            if self.running:
                logger.info("⏳ Пауза 30 минут до следующего цикла...")
                for i in range(1800):  # 30 минут
                    if not self.running:
                        break
                    time.sleep(1)
        
        logger.info("🛑 Система кодексов остановлена")

def main():
    """Основная функция"""
    if len(sys.argv) > 1 and sys.argv[1] == "background":
        # Фоновый режим
        manager = CodesSystemManager()
        manager.run_system()
    else:
        # Интерактивный режим
        print("🚀 Система кодексов АДВАКОД")
        print("Выберите действие:")
        print("1. Скачать кодексы")
        print("2. Интегрировать с RAG")
        print("3. Полный процесс")
        print("4. Запустить в фоновом режиме")
        print("5. Статус системы")
        
        choice = input("\nВведите номер (1-5): ").strip()
        
        manager = CodesSystemManager()
        manager.initialize_system()
        
        if choice == "1":
            manager.run_download_cycle()
        elif choice == "2":
            manager.run_integration_cycle()
        elif choice == "3":
            manager.run_download_cycle()
            manager.run_integration_cycle()
        elif choice == "4":
            manager.run_system()
        elif choice == "5":
            manager.run_monitoring_cycle()
        else:
            print("❌ Неверный выбор")

if __name__ == "__main__":
    main()



