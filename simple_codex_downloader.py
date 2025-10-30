#!/usr/bin/env python3
"""
Простой загрузчик кодексов с pravo.gov.ru
Использует только стандартные библиотеки Python
"""

import os
import sys
import requests
import time
from urllib.parse import urljoin, urlparse
from pathlib import Path
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('codex_downloader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleCodexDownloader:
    def __init__(self, output_dir="downloaded_codexes"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Список кодексов для скачивания
        self.codexes = {
            "Гражданский кодекс РФ": "http://pravo.gov.ru/proxy/ips/?docbody=&nd=102120000&rdk=&backlink=1&page=1&rdnd=102120000&link=0001201410140002",
            "Уголовный кодекс РФ": "http://pravo.gov.ru/proxy/ips/?docbody=&nd=102120000&rdk=&backlink=1&page=1&rdnd=102120000&link=0001202203030006",
            "Трудовой кодекс РФ": "http://pravo.gov.ru/proxy/ips/?docbody=&nd=102120000&rdk=&backlink=1&page=1&rdnd=102120000&link=0001201412140001",
            "Семейный кодекс РФ": "http://pravo.gov.ru/proxy/ips/?docbody=&nd=102120000&rdk=&backlink=1&page=1&rdnd=102120000&link=0001201412140002",
            "Жилищный кодекс РФ": "http://pravo.gov.ru/proxy/ips/?docbody=&nd=102120000&rdk=&backlink=1&page=1&rdnd=102120000&link=0001201412140003",
            "Налоговый кодекс РФ": "http://pravo.gov.ru/proxy/ips/?docbody=&nd=102120000&rdk=&backlink=1&page=1&rdnd=102120000&link=0001201412140004",
            "Бюджетный кодекс РФ": "http://pravo.gov.ru/proxy/ips/?docbody=&nd=102120000&rdk=&backlink=1&page=1&rdnd=102120000&link=0001201412140005",
            "Кодекс об административных правонарушениях РФ": "http://pravo.gov.ru/proxy/ips/?docbody=&nd=102120000&rdk=&backlink=1&page=1&rdnd=102120000&link=0001201412140006"
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def download_pdf(self, url, filename):
        """Скачивает PDF файл"""
        try:
            logger.info(f"Скачивание: {filename}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            filepath = self.output_dir / filename
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✅ Скачан: {filename} ({len(response.content)} байт)")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка скачивания {filename}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка {filename}: {e}")
            return False

    def download_codex(self, name, url):
        """Скачивает кодекс по URL"""
        logger.info(f"📖 Обработка кодекса: {name}")
        
        # Извлекаем ID из URL для имени файла
        parsed_url = urlparse(url)
        link_param = parsed_url.query.split('link=')[-1] if 'link=' in parsed_url.query else 'unknown'
        filename = f"{link_param}.pdf"
        
        return self.download_pdf(url, filename)

    def download_all(self):
        """Скачивает все кодексы"""
        logger.info("🚀 Начало скачивания кодексов")
        logger.info(f"📁 Выходная директория: {self.output_dir}")
        
        success_count = 0
        total_count = len(self.codexes)
        
        for name, url in self.codexes.items():
            if self.download_codex(name, url):
                success_count += 1
            
            # Пауза между запросами
            time.sleep(2)
        
        logger.info(f"✅ Скачивание завершено: {success_count}/{total_count} кодексов")
        return success_count, total_count

    def get_status(self):
        """Возвращает статус скачанных файлов"""
        files = list(self.output_dir.glob("*.pdf"))
        return {
            "total_files": len(files),
            "files": [f.name for f in files],
            "total_size": sum(f.stat().st_size for f in files)
        }

def main():
    """Основная функция"""
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    else:
        output_dir = "downloaded_codexes"
    
    downloader = SimpleCodexDownloader(output_dir)
    
    try:
        success, total = downloader.download_all()
        
        # Выводим статус
        status = downloader.get_status()
        print(f"\n📊 Статус:")
        print(f"Скачано файлов: {status['total_files']}")
        print(f"Общий размер: {status['total_size']:,} байт")
        
        if status['files']:
            print(f"Файлы: {', '.join(status['files'])}")
        
        return 0 if success == total else 1
        
    except KeyboardInterrupt:
        logger.info("⏹️ Скачивание прервано пользователем")
        return 1
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())



