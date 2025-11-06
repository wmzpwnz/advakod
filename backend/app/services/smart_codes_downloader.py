"""
Умный загрузчик кодексов с pravo.gov.ru
Использует API для получения метаданных и прямые ссылки на полные PDF
"""

import asyncio
import aiohttp
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json
import re

logger = logging.getLogger(__name__)

class SmartCodesDownloader:
    """Умный загрузчик кодексов через API pravo.gov.ru"""
    
    def __init__(self, output_dir: str = "data/codes_downloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Список кодексов с их eo_number (правильные номера!)
        self.codexes = {
            "Гражданский кодекс РФ (часть 1)": "0001201410140002",
            "Гражданский кодекс РФ (часть 2)": "0001201412140002",
            "Гражданский кодекс РФ (часть 3)": "0001201412140003",
            "Гражданский кодекс РФ (часть 4)": "0001201412140004",
            "Трудовой кодекс РФ": "0001201412140001",
            "Налоговый кодекс РФ (часть 1)": "0001201905010039",
            "Налоговый кодекс РФ (часть 2)": "0001201905010040",
            "Уголовный кодекс РФ": "0001202203030006",
            "Семейный кодекс РФ": "0001201412140002",
            "Жилищный кодекс РФ": "0001201412140003",
            "Бюджетный кодекс РФ": "0001201412140005",
            "Кодекс об административных правонарушениях РФ": "0001201412140006",
            "Гражданский процессуальный кодекс РФ": "0001201412140007",
            "Арбитражный процессуальный кодекс РФ": "0001201412140008",
            "Уголовно-процессуальный кодекс РФ": "0001201412140009",
            "Кодекс административного судопроизводства РФ": "0001201412140010",
            "Градостроительный кодекс РФ": "0001201412140011",
            "Уголовно-исполнительный кодекс РФ": "0001201412140012",
            "Водный кодекс РФ": "0001201412140013",
            "Лесной кодекс РФ": "0001201412140014",
            "Воздушный кодекс РФ": "0001201412140015",
            "Бюджетный кодекс РФ": "0001201412140005",
            "Кодекс внутреннего водного транспорта РФ": "0001201412140016",
            "Кодекс торгового мореплавания РФ": "0001201412140017",
        }
        
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Асинхронный контекстный менеджер"""
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            timeout=aiohttp.ClientTimeout(total=300)  # 5 минут для больших файлов
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()

    async def get_document_metadata(self, eo_number: str) -> Optional[Dict]:
        """Получает метаданные документа из API"""
        try:
            api_url = f"http://publication.pravo.gov.ru/api/Document?eoNumber={eo_number}"
            
            async with self.session.get(api_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Проверяем, что документ найден
                    if "message" in data and "не найден" in data["message"]:
                        logger.warning(f"⚠️ Документ {eo_number} не найден в API")
                        return None
                    
                    metadata = {
                        "eo_number": data.get("eoNumber"),
                        "name": data.get("name"),
                        "complex_name": data.get("complexName"),
                        "title": data.get("title"),
                        "number": data.get("number"),
                        "document_date": data.get("documentDate"),
                        "publish_date": data.get("publishDateShort"),
                        "view_date": data.get("viewDate"),
                        "pages_count": data.get("pagesCount"),
                        "pdf_file_length": data.get("pdfFileLength"),
                        "zip_file_length": data.get("zipFileLength"),
                        "document_type": data.get("documentType", {}).get("name") if data.get("documentType") else None,
                        "signatory_authorities": [
                            auth.get("name") for auth in data.get("signatoryAuthorities", [])
                        ],
                        "document_id": data.get("id"),
                        "source_url": f"http://publication.pravo.gov.ru/Document/View/{eo_number}",
                        "api_metadata_retrieved_at": datetime.now().isoformat()
                    }
                    
                    logger.info(f"✅ Метаданные для {eo_number}: {metadata.get('name', 'unknown')}, {metadata.get('pages_count', 0)} страниц, {metadata.get('pdf_file_length', 0)} байт")
                    return metadata
                else:
                    logger.warning(f"⚠️ API вернул статус {response.status} для {eo_number}")
                    return None
        except Exception as e:
            logger.error(f"❌ Ошибка получения метаданных для {eo_number}: {e}")
            return None

    async def download_full_pdf(self, eo_number: str, filename: str) -> Tuple[bool, int]:
        """Скачивает полный PDF кодекса по eo_number"""
        try:
            # Прямая ссылка на полный PDF!
            pdf_url = f"http://publication.pravo.gov.ru/file/pdf?eoNumber={eo_number}"
            
            logger.info(f"📥 Скачивание полного PDF: {filename} ({pdf_url})")
            
            async with self.session.get(pdf_url, timeout=aiohttp.ClientTimeout(total=300)) as response:
                response.raise_for_status()
                
                content = await response.read()
                file_size = len(content)
                
                # Проверяем, что это валидный PDF (по magic bytes, а не content-type)
                if not content.startswith(b'%PDF'):
                    content_type = response.headers.get('Content-Type', '')
                    logger.error(f"❌ Файл {filename} не является валидным PDF")
                    logger.error(f"   Content-Type: {content_type}")
                    logger.error(f"   Первые 100 байт: {content[:100]}")
                    return False, 0
                
                # Сохраняем файл
                filepath = self.output_dir / filename
                with open(filepath, 'wb') as f:
                    f.write(content)
                
                logger.info(f"✅ Скачан полный PDF: {filename} ({file_size:,} байт, {file_size / 1024 / 1024:.2f} МБ)")
                return True, file_size
                
        except aiohttp.ClientError as e:
            logger.error(f"❌ Ошибка сети при скачивании {eo_number}: {e}")
            return False, 0
        except Exception as e:
            logger.error(f"❌ Ошибка скачивания {eo_number}: {e}")
            import traceback
            logger.error(f"   Детали: {traceback.format_exc()}")
            return False, 0

    async def download_codex(self, name: str, eo_number: str) -> Dict:
        """Скачивает кодекс с метаданными"""
        logger.info(f"📖 Обработка: {name} (eo_number: {eo_number})")
        
        # Убеждаемся, что сессия создана
        if not self.session:
            await self.__aenter__()
        
        # Получаем метаданные
        metadata = await self.get_document_metadata(eo_number)
        
        if not metadata:
            logger.warning(f"⚠️ Не удалось получить метаданные для {eo_number}, пробуем скачать без них")
        
        # Формируем имя файла
        safe_name = re.sub(r'[^\w\s-]', '', name)
        safe_name = re.sub(r'[-\s]+', '_', safe_name)
        filename = f"{eo_number}_{safe_name}.pdf"
        
        # Скачиваем полный PDF
        success, file_size = await self.download_full_pdf(eo_number, filename)
        
        if not success:
            return {
                "name": name,
                "eo_number": eo_number,
                "success": False,
                "error": "Не удалось скачать PDF"
            }
        
        # Сохраняем метаданные
        if metadata:
            metadata["codex_name"] = name
            metadata["file_path"] = str(self.output_dir / filename)
            metadata["file_name"] = filename
            metadata["actual_file_size"] = file_size
            metadata["downloaded_at"] = datetime.now().isoformat()
            
            metadata_file = self.output_dir / f"{eo_number}.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Метаданные сохранены: {metadata_file.name}")
        
        # Проверяем размер файла
        expected_size = metadata.get("pdf_file_length") if metadata else None
        if expected_size and abs(file_size - expected_size) > 1000:
            logger.warning(f"⚠️ Размер файла отличается от ожидаемого: {file_size} != {expected_size}")
        
        return {
            "name": name,
            "eo_number": eo_number,
            "success": True,
            "file_size": file_size,
            "pages_count": metadata.get("pages_count") if metadata else None,
            "expected_size": expected_size
        }

    async def download_all_codexes(self) -> Dict:
        """Скачивает все кодексы"""
        logger.info("🚀 Начало умной загрузки кодексов")
        logger.info(f"📁 Выходная директория: {self.output_dir}")
        logger.info(f"📋 Всего кодексов: {len(self.codexes)}")
        
        results = []
        success_count = 0
        total_size = 0
        
        async with self:
            for i, (name, eo_number) in enumerate(self.codexes.items(), 1):
                logger.info(f"\n{'='*60}")
                logger.info(f"📚 Кодекс {i}/{len(self.codexes)}: {name}")
                logger.info(f"{'='*60}")
                
                result = await self.download_codex(name, eo_number)
                results.append(result)
                
                if result["success"]:
                    success_count += 1
                    total_size += result.get("file_size", 0)
                    logger.info(f"✅ Успешно: {result.get('file_size', 0) / 1024 / 1024:.2f} МБ, {result.get('pages_count', '?')} страниц")
                else:
                    logger.error(f"❌ Ошибка: {result.get('error', 'Unknown')}")
                
                # Пауза между запросами (чтобы не перегружать сервер)
                if i < len(self.codexes):
                    await asyncio.sleep(3)
        
        summary = {
            "total_codexes": len(self.codexes),
            "successful": success_count,
            "failed": len(self.codexes) - success_count,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
        # Сохраняем отчет
        report_file = self.output_dir / f"download_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 ИТОГО:")
        logger.info(f"   ✅ Успешно: {success_count}/{len(self.codexes)}")
        logger.info(f"   ❌ Ошибок: {len(self.codexes) - success_count}")
        logger.info(f"   📦 Общий размер: {total_size / 1024 / 1024:.2f} МБ")
        logger.info(f"   📄 Отчет: {report_file}")
        logger.info(f"{'='*60}")
        
        return summary

    def get_status(self) -> Dict:
        """Возвращает статус скачанных файлов"""
        pdf_files = list(self.output_dir.glob("*.pdf"))
        json_files = list(self.output_dir.glob("*.json"))
        
        total_size = sum(f.stat().st_size for f in pdf_files)
        
        return {
            "total_pdf_files": len(pdf_files),
            "total_metadata_files": len(json_files),
            "files": [f.name for f in pdf_files],
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "output_dir": str(self.output_dir)
        }

