"""
Сервис для скачивания кодексов с pravo.gov.ru
"""

import asyncio
import aiohttp
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class CodesDownloader:
    def __init__(self, output_dir: str = "downloaded_codexes"):
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
        
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Асинхронный контекстный менеджер"""
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()

    async def download_pdf(self, url: str, filename: str) -> bool:
        """Скачивает PDF файл"""
        try:
            logger.info(f"Скачивание: {filename}")
            
            async with self.session.get(url) as response:
                response.raise_for_status()
                content = await response.read()
            
            filepath = self.output_dir / filename
            with open(filepath, 'wb') as f:
                f.write(content)
            
            logger.info(f"✅ Скачан: {filename} ({len(content)} байт)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка скачивания {filename}: {e}")
            return False

    async def download_codex(self, name: str, url: str) -> bool:
        """Скачивает кодекс по URL"""
        logger.info(f"📖 Обработка кодекса: {name}")
        
        # Извлекаем ID из URL для имени файла
        link_param = url.split('link=')[-1] if 'link=' in url else 'unknown'
        filename = f"{link_param}.pdf"
        
        return await self.download_pdf(url, filename)

    async def download_all_codexes(self) -> Tuple[int, int]:
        """Скачивает все кодексы"""
        logger.info("🚀 Начало скачивания кодексов")
        logger.info(f"📁 Выходная директория: {self.output_dir}")
        
        success_count = 0
        total_count = len(self.codexes)
        
        async with self:
            for name, url in self.codexes.items():
                if await self.download_codex(name, url):
                    success_count += 1
                
                # Пауза между запросами
                await asyncio.sleep(2)
        
        logger.info(f"✅ Скачивание завершено: {success_count}/{total_count} кодексов")
        return success_count, total_count

    def get_status(self) -> Dict:
        """Возвращает статус скачанных файлов"""
        files = list(self.output_dir.glob("*.pdf"))
        return {
            "total_files": len(files),
            "files": [f.name for f in files],
            "total_size": sum(f.stat().st_size for f in files),
            "output_dir": str(self.output_dir)
        }

    def get_downloaded_files(self) -> List[Path]:
        """Возвращает список скачанных файлов"""
        return list(self.output_dir.glob("*.pdf"))

    def cleanup_old_files(self, days: int = 30):
        """Очищает старые файлы"""
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        cleaned_count = 0
        
        for file_path in self.output_dir.glob("*.pdf"):
            if file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                cleaned_count += 1
                logger.info(f"🗑️ Удален старый файл: {file_path.name}")
        
        if cleaned_count > 0:
            logger.info(f"✅ Очищено {cleaned_count} старых файлов")
        else:
            logger.info("ℹ️ Старых файлов для очистки не найдено")



