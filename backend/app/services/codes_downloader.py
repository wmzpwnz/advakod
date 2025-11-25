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
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

class CodesDownloader:
    def __init__(self, output_dir: str = "data/codes_downloads"):
        import os
        # Используем абсолютный путь внутри контейнера
        if not os.path.isabs(output_dir):
            base_dir = os.getenv("DATA_DIR", "/app/data")
            self.output_dir = Path(base_dir) / output_dir
        else:
            self.output_dir = Path(output_dir)
        
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            # Если нет прав, используем временную директорию
            import tempfile
            temp_base = Path(tempfile.gettempdir()) / "codes_downloads"
            temp_base.mkdir(parents=True, exist_ok=True)
            self.output_dir = temp_base
            logger.warning(f"⚠️ Не удалось создать директорию, используем временную: {temp_base}")
        
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

    def _is_html_content(self, content: bytes) -> bool:
        """Проверяет, является ли контент HTML"""
        try:
            # Проверяем начало файла на наличие HTML тегов
            content_start = content[:1024].decode('utf-8', errors='ignore').lower()
            return '<html' in content_start or '<!doctype html' in content_start
        except:
            return False
    
    async def _get_document_metadata(self, eo_number: str) -> Optional[Dict]:
        """Получает метаданные документа из API publication.pravo.gov.ru"""
        try:
            api_url = f"http://publication.pravo.gov.ru/api/Document?eoNumber={eo_number}"
            
            async with self.session.get(api_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Извлекаем нужные метаданные
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
                        "document_type": data.get("documentType", {}).get("name") if data.get("documentType") else None,
                        "signatory_authorities": [
                            auth.get("name") for auth in data.get("signatoryAuthorities", [])
                        ],
                        "document_id": data.get("id"),
                        "source_url": f"http://publication.pravo.gov.ru/Document/View/{eo_number}",
                        "api_metadata_retrieved_at": datetime.now().isoformat()
                    }
                    
                    logger.info(f"✅ Получены метаданные для {eo_number}: {metadata.get('name', 'unknown')}")
                    return metadata
                else:
                    logger.warning(f"⚠️ Не удалось получить метаданные для {eo_number}: статус {response.status}")
                    return None
        except Exception as e:
            logger.warning(f"⚠️ Ошибка получения метаданных для {eo_number}: {e}")
            return None
    
    def _extract_text_from_html(self, html_content: bytes) -> Optional[str]:
        """Извлекает текст из HTML"""
        try:
            # Пробуем разные кодировки
            for encoding in ['utf-8', 'windows-1251', 'cp1251', 'iso-8859-1']:
                try:
                    html_text = html_content.decode(encoding)
                    soup = BeautifulSoup(html_text, 'html.parser')
                    
                    # Удаляем script и style теги
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # Извлекаем текст
                    text = soup.get_text()
                    
                    # Очищаем текст от лишних пробелов
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = '\n'.join(chunk for chunk in chunks if chunk)
                    
                    if len(text) > 100:  # Минимальный размер текста
                        return text
                except (UnicodeDecodeError, Exception):
                    continue
            
            return None
        except Exception as e:
            logger.warning(f"Ошибка извлечения текста из HTML: {e}")
            return None

    async def download_pdf(self, url: str, filename: str, eo_number: str = None) -> bool:
        """Скачивает PDF файл или извлекает текст из HTML"""
        try:
            # Если есть eo_number, используем прямой URL на полный PDF
            if eo_number:
                pdf_url = f"http://publication.pravo.gov.ru/file/pdf?eoNumber={eo_number}"
                logger.info(f"📥 Скачивание полного PDF через API: {filename}")
            else:
                pdf_url = url
                logger.info(f"Скачивание: {filename}")
            
            async with self.session.get(pdf_url) as response:
                response.raise_for_status()
                content = await response.read()
            
            # Проверяем, является ли контент HTML
            if self._is_html_content(content):
                logger.info(f"⚠️ Получен HTML вместо PDF, извлекаем текст...")
                
                # Пробуем найти iframe с doc_itself - там реальный документ
                try:
                    html_text = content.decode('windows-1251', errors='ignore')
                    soup = BeautifulSoup(html_text, 'html.parser')
                    
                    # Ищем iframe с doc_itself
                    iframes = soup.find_all('iframe', src=True)
                    doc_iframe_url = None
                    for iframe in iframes:
                        src = iframe.get('src', '')
                        if 'doc_itself' in src:
                            # Строим полный URL для iframe
                            from urllib.parse import urljoin
                            doc_iframe_url = urljoin(url, src)
                            logger.info(f"📄 Найден iframe с документом: {doc_iframe_url}")
                            break
                    
                    # Если нашли iframe с документом, загружаем его
                    if doc_iframe_url:
                        async with self.session.get(doc_iframe_url) as iframe_response:
                            iframe_response.raise_for_status()
                            iframe_content = await iframe_response.read()
                            logger.info(f"✅ Загружен контент из iframe: {len(iframe_content)} bytes")
                            # Используем контент из iframe для извлечения текста
                            text = self._extract_text_from_html(iframe_content)
                        if text and len(text) > 500:  # Если получили хороший текст из iframe
                            txt_filename = filename.replace('.pdf', '.txt')
                            filepath = self.output_dir / txt_filename
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(text)
                            logger.info(f"✅ Текст извлечен из iframe: {txt_filename} ({len(text)} символов)")
                            return True
                except Exception as iframe_err:
                    logger.warning(f"⚠️ Ошибка при работе с iframe: {iframe_err}, используем основной контент")
                
                # Если iframe не сработал, используем основной контент
                text = self._extract_text_from_html(content)
                
                if text:
                    # Сохраняем как текстовый файл (DocumentService поддерживает .txt)
                    txt_filename = filename.replace('.pdf', '.txt')
                    filepath = self.output_dir / txt_filename
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(text)
                    logger.info(f"✅ Текст извлечен из HTML: {txt_filename} ({len(text)} символов)")
                    # HTML файлы не сохраняем - они не нужны, только текст
                    return True
                else:
                    logger.warning(f"⚠️ Не удалось извлечь текст из HTML для {filename}")
                    # Пробуем сохранить как TXT с минимальным содержимым
                    txt_filename = filename.replace('.pdf', '.txt')
                    filepath = self.output_dir / txt_filename
                    # Пытаемся извлечь хотя бы что-то из HTML
                    try:
                        html_text = content.decode('windows-1251', errors='ignore')
                        # Простое извлечение текста без BeautifulSoup
                        import re
                        text = re.sub(r'<[^>]+>', '', html_text)
                        text = re.sub(r'\s+', ' ', text).strip()
                        if len(text) > 100:
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(text)
                            logger.info(f"✅ Текст извлечен простым методом: {txt_filename}")
                            return True
                    except:
                        pass
                    return False
            else:
                # Это PDF или другой бинарный файл
                filepath = self.output_dir / filename
                with open(filepath, 'wb') as f:
                    f.write(content)
                
                # Проверяем, что это действительно PDF
                if content[:4] == b'%PDF':
                    logger.info(f"✅ Скачан PDF: {filename} ({len(content)} байт)")
                else:
                    logger.warning(f"⚠️ Скачан файл, но не PDF: {filename} ({len(content)} байт)")
                
                return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка скачивания {filename}: {e}")
            return False

    async def download_codex(self, name: str, url: str) -> bool:
        """Скачивает кодекс по URL и получает метаданные из API"""
        logger.info(f"📖 Обработка кодекса: {name}")
        
        # Извлекаем eo_number (ID) из URL для имени файла
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        link_param = query_params.get('link', [None])[0] if query_params.get('link') else None
        
        if not link_param:
            # Пробуем извлечь из строки напрямую
            link_param = url.split('link=')[-1].split('&')[0] if 'link=' in url else 'unknown'
        
        eo_number = link_param
        filename = f"{eo_number}.pdf"
        
        # Получаем метаданные из API
        metadata = await self._get_document_metadata(eo_number)
        
        # Скачиваем файл (используем прямой URL на полный PDF)
        download_success = await self.download_pdf(url, filename, eo_number=eo_number)
        
        # Сохраняем метаданные в JSON файл
        if download_success and metadata:
            # Определяем имя файла для метаданных (может быть .txt если это HTML)
            downloaded_files = list(self.output_dir.glob(f"{eo_number}.*"))
            actual_file = None
            if downloaded_files:
                actual_file = downloaded_files[0]
                metadata_file = actual_file.with_suffix('.json')
            else:
                metadata_file = self.output_dir / f"{eo_number}.json"
            
            # Добавляем имя кодекса и путь к файлу
            metadata["codex_name"] = name
            if actual_file:
                metadata["file_path"] = str(actual_file)
                metadata["file_name"] = actual_file.name
            else:
                metadata["file_path"] = None
                metadata["file_name"] = filename
            
            # Сохраняем метаданные
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Метаданные сохранены: {metadata_file.name}")
        
        return download_success

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
        # Ищем PDF, TXT и HTML файлы
        pdf_files = list(self.output_dir.glob("*.pdf"))
        txt_files = list(self.output_dir.glob("*.txt"))
        html_files = list(self.output_dir.glob("*.html"))
        all_files = pdf_files + txt_files + html_files
        
        return {
            "total_files": len(all_files),
            "files": [f.name for f in all_files],
            "pdf_files": len(pdf_files),
            "txt_files": len(txt_files),
            "html_files": len(html_files),
            "total_size": sum(f.stat().st_size for f in all_files),
            "output_dir": str(self.output_dir)
        }

    def get_downloaded_files(self) -> List[Path]:
        """Возвращает список скачанных файлов (PDF, TXT, HTML)"""
        pdf_files = list(self.output_dir.glob("*.pdf"))
        txt_files = list(self.output_dir.glob("*.txt"))
        html_files = list(self.output_dir.glob("*.html"))
        return pdf_files + txt_files + html_files

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



