"""
Сервис для извлечения текста из PDF с использованием OCR
"""

import logging
import io
from typing import Optional, List
from pathlib import Path

import pypdf
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)

class PDFOCRService:
    """Сервис для извлечения текста из PDF с OCR"""
    
    def __init__(self):
        self.supported_languages = ['rus', 'eng']
        
    def extract_text_from_pdf(self, file_path: str) -> Optional[str]:
        """Извлекает текст из PDF файла с использованием OCR"""
        try:
            file_path = Path(file_path)
            
            # Сначала пробуем стандартное извлечение текста
            text = self._extract_text_standard(file_path)
            if text and len(text.strip()) > 100:  # Если получили достаточно текста
                logger.info(f"Стандартное извлечение текста успешно: {len(text)} символов")
                return text
            
            # Если стандартное извлечение не дало результата, используем OCR
            logger.info("Стандартное извлечение не дало результата, используем OCR")
            text = self._extract_text_with_ocr(file_path)
            
            if text and len(text.strip()) > 50:
                logger.info(f"OCR извлечение успешно: {len(text)} символов")
                return text
            else:
                logger.warning("OCR не смог извлечь текст из PDF")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка извлечения текста из PDF {file_path}: {e}")
            return None
    
    def _extract_text_standard(self, file_path: Path) -> Optional[str]:
        """Стандартное извлечение текста из PDF"""
        try:
            with open(file_path, 'rb') as file:
                reader = pypdf.PdfReader(file)
                text_parts = []
                
                for page_num, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                    except Exception as e:
                        logger.warning(f"Ошибка извлечения текста со страницы {page_num}: {e}")
                        continue
                
                return '\n\n'.join(text_parts) if text_parts else None
                
        except Exception as e:
            logger.error(f"Ошибка стандартного извлечения текста: {e}")
            return None
    
    def _extract_text_with_ocr(self, file_path: Path) -> Optional[str]:
        """Извлечение текста с использованием OCR"""
        try:
            # Конвертируем PDF в изображения
            images = self._pdf_to_images(file_path)
            if not images:
                return None
            
            # Извлекаем текст с каждого изображения
            text_parts = []
            for i, image in enumerate(images):
                try:
                    # Используем OCR для извлечения текста
                    page_text = pytesseract.image_to_string(
                        image, 
                        lang='rus+eng',  # Русский и английский языки
                        config='--psm 6'  # Предполагаем единый блок текста
                    )
                    
                    if page_text.strip():
                        text_parts.append(page_text.strip())
                        logger.info(f"OCR обработал страницу {i+1}: {len(page_text)} символов")
                    
                except Exception as e:
                    logger.warning(f"Ошибка OCR на странице {i+1}: {e}")
                    continue
            
            return '\n\n'.join(text_parts) if text_parts else None
            
        except Exception as e:
            logger.error(f"Ошибка OCR извлечения текста: {e}")
            return None
    
    def _pdf_to_images(self, file_path: Path) -> List[Image.Image]:
        """Конвертирует PDF в изображения"""
        try:
            logger.info(f"Конвертируем PDF в изображения: {file_path}")
            
            # Конвертируем PDF в изображения
            images = convert_from_path(
                str(file_path),
                dpi=300,  # Высокое разрешение для лучшего OCR
                first_page=1,
                last_page=5  # Обрабатываем только первые 5 страниц для теста
            )
            
            logger.info(f"Получено {len(images)} изображений из PDF")
            return images
            
        except Exception as e:
            logger.error(f"Ошибка конвертации PDF в изображения: {e}")
            return []
    
    def is_pdf_readable(self, file_path: str) -> bool:
        """Проверяет, можно ли извлечь текст из PDF"""
        try:
            file_path = Path(file_path)
            
            # Пробуем открыть PDF
            with open(file_path, 'rb') as file:
                reader = pypdf.PdfReader(file)
                
                # Проверяем количество страниц
                if len(reader.pages) == 0:
                    return False
                
                # Пробуем извлечь текст с первой страницы
                first_page = reader.pages[0]
                text = first_page.extract_text()
                
                # Если получили текст, PDF читаемый
                return text and len(text.strip()) > 10
                
        except Exception as e:
            logger.error(f"Ошибка проверки читаемости PDF: {e}")
            return False

# Глобальный экземпляр сервиса
pdf_ocr_service = PDFOCRService()
