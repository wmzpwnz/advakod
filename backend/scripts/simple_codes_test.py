#!/usr/bin/env python3
"""
Простой тест скачивания кодексов без сложных зависимостей
"""

import asyncio
import logging
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleCodesDownloader:
    """Простой скачиватель кодексов для тестирования"""
    
    def __init__(self, output_dir: str = "/app/data/legal_documents/raw/codes"):
        self.base_url = "http://pravo.gov.ru"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.download_delay = 2  # Задержка между запросами
        logger.info(f"SimpleCodesDownloader инициализирован. Выходная директория: {self.output_dir}")

    async def test_connection(self):
        """Тестирует подключение к pravo.gov.ru"""
        try:
            logger.info("🔍 Тестируем подключение к pravo.gov.ru...")
            response = await asyncio.to_thread(self.session.get, self.base_url, timeout=30)
            response.raise_for_status()
            logger.info(f"✅ Подключение успешно! Статус: {response.status_code}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка подключения: {e}")
            return False

    async def download_sample_document(self):
        """Скачивает один тестовый документ"""
        try:
            logger.info("📥 Скачиваем тестовый документ...")
            # Простой тест - скачиваем главную страницу
            response = await asyncio.to_thread(self.session.get, self.base_url, timeout=30)
            response.raise_for_status()
            
            # Сохраняем как тестовый файл
            test_file = self.output_dir / "test_page.html"
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            logger.info(f"✅ Тестовый файл сохранен: {test_file}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка скачивания: {e}")
            return False

async def main():
    """Основная функция"""
    logger.info("🚀 Запуск простого теста скачивания кодексов...")
    
    downloader = SimpleCodesDownloader()
    
    # Тест подключения
    if not await downloader.test_connection():
        logger.error("❌ Не удалось подключиться к pravo.gov.ru")
        return
    
    # Тест скачивания
    if not await downloader.download_sample_document():
        logger.error("❌ Не удалось скачать тестовый документ")
        return
    
    logger.info("🎉 Все тесты прошли успешно!")

if __name__ == "__main__":
    asyncio.run(main())

