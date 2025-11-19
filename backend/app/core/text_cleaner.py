"""
Модуль для очистки текста кодексов от служебной информации
Удаляет даты редакций, элементы навигации, метаинформацию и другой мусор
"""

import re
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class LegalTextCleaner:
    """Класс для очистки текста правовых документов от служебной информации"""
    
    def __init__(self):
        # Паттерны для удаления служебной информации
        self.service_patterns = [
            # Даты редакций
            r'недействующая на \d{2}\.\d{2}\.\d{4}',
            r'не вступившая в силу редакция на \d{2}\.\d{2}\.\d{4}',
            r'актуальная, есть не вступившие в силу редакции на \d{2}\.\d{2}\.\d{4}',
            r'редакция на \d{2}\.\d{2}\.\d{4}',
            r'с \d{2}\.\d{2}\.\d{4}',
            r'на \d{2}\.\d{2}\.\d{4}',
            
            # Элементы навигации
            r'печать текста полностью',
            r'печать выделенного фрагмента',
            r'a- a\+',
            r'a\+ a-',
            r'фон документа',
            r'размер шрифта',
            r'стандарт',
            r'наименование',
            r'опубликование',
            r'входящие связи',
            
            # Служебные команды
            r'закрыть',
            r'открыть',
            r'справка',
            r'помощь',
        ]
        
        # Ключевые слова для удаления строк (полное совпадение)
        self.service_keywords = [
            'cookie',
            'javascript',
            'css',
            'script',
            'style',
            'навигация',
            'меню',
            'footer',
            'header',
            'sidebar',
            'закрыть',
            'открыть',
            'a-',
            'a+',
            'фон документа',
            'белый',
            'серый',
            'размер шрифта',
            'стандарт',
            'свидетельство о регистрации',
            'печать текста полностью',
            'печать выделенного фрагмента',
        ]
        
        # Паттерны для метаинформации в начале файла
        self.metadata_patterns = [
            r'Действует с изменениями.*?печать текста полностью',
            r'Кодекс Российской Федерации от.*?печать текста полностью',
            r'Федеральный закон.*?печать текста полностью',
        ]
        
        # Компилируем паттерны для производительности
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                                 for pattern in self.service_patterns]
        self.compiled_metadata_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                                          for pattern in self.metadata_patterns]
    
    def is_service_line(self, line: str) -> bool:
        """Проверяет, является ли строка служебной"""
        if not line or len(line.strip()) < 2:
            return True
        
        line_lower = line.lower().strip()
        
        # Проверяем полное совпадение с ключевыми словами
        if line_lower in self.service_keywords:
            return True
        
        # Проверяем короткие строки на наличие служебных слов
        if len(line) < 20:
            for keyword in self.service_keywords:
                if keyword in line_lower:
                    return True
        
        # Проверяем паттерны
        for pattern in self.compiled_patterns:
            if pattern.search(line):
                return True
        
        return False
    
    def remove_metadata_header(self, text: str) -> str:
        """Удаляет метаинформацию из начала файла"""
        lines = text.split('\n')
        cleaned_lines = []
        skip_until_content = True
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Пропускаем пустые строки в начале
            if skip_until_content and not line_stripped:
                continue
            
            # Проверяем, является ли строка метаинформацией
            is_metadata = False
            
            # Проверяем паттерны метаинформации
            for pattern in self.compiled_metadata_patterns:
                if pattern.search(line):
                    is_metadata = True
                    break
            
            # Проверяем длинные строки с датами (метаинформация о редакциях)
            if len(line_stripped) > 200 and any(
                'недействующая' in line_lower or 
                'редакция' in line_lower or 
                'актуальная' in line_lower
                for line_lower in [line_stripped.lower()]
            ):
                # Проверяем, что это не реальный текст кодекса
                if not any(keyword in line_stripped.lower() for keyword in 
                          ['статья', 'глава', 'раздел', 'часть', 'кодекс']):
                    is_metadata = True
            
            if is_metadata:
                continue
            
            # Если строка не метаинформация, начинаем сохранять контент
            if skip_until_content and line_stripped:
                skip_until_content = False
            
            if not skip_until_content:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def clean_line(self, line: str) -> Optional[str]:
        """Очищает одну строку от служебной информации"""
        if not line:
            return None
        
        line_stripped = line.strip()
        
        # Пропускаем пустые строки
        if not line_stripped:
            return None
        
        # Пропускаем очень короткие строки (менее 2 символов)
        if len(line_stripped) < 2:
            return None
        
        # Пропускаем служебные строки
        if self.is_service_line(line_stripped):
            return None
        
        return line_stripped
    
    def clean_text(self, text: str, aggressive: bool = True) -> str:
        """
        Очищает текст от служебной информации
        
        Args:
            text: Исходный текст
            aggressive: Если True, использует агрессивную очистку (удаляет метаинформацию из начала)
        
        Returns:
            Очищенный текст
        """
        if not text:
            return ""
        
        original_length = len(text)
        
        # ШАГ 1: Удаляем метаинформацию из начала файла
        if aggressive:
            text = self.remove_metadata_header(text)
        
        # ШАГ 2: Разбиваем на строки и очищаем каждую
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            cleaned_line = self.clean_line(line)
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
        
        # ШАГ 3: Объединяем обратно
        cleaned_text = '\n'.join(cleaned_lines)
        
        # ШАГ 4: Удаляем множественные пустые строки (оставляем максимум 2 подряд)
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        
        # ШАГ 5: Удаляем пробелы в начале и конце
        cleaned_text = cleaned_text.strip()
        
        final_length = len(cleaned_text)
        removed_chars = original_length - final_length
        
        if removed_chars > 0:
            logger.info(f"🧹 Очистка текста: удалено {removed_chars} символов ({removed_chars/original_length*100:.1f}%)")
        
        return cleaned_text
    
    def clean_file(self, file_path: str, output_path: Optional[str] = None, aggressive: bool = True) -> str:
        """
        Очищает текстовый файл и сохраняет результат
        
        Args:
            file_path: Путь к исходному файлу
            output_path: Путь для сохранения (если None, перезаписывает исходный)
            aggressive: Использовать агрессивную очистку
        
        Returns:
            Путь к очищенному файлу
        """
        from pathlib import Path
        
        input_path = Path(file_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        # Читаем файл
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except UnicodeDecodeError:
            # Пробуем другие кодировки
            for encoding in ['windows-1251', 'cp1251', 'iso-8859-1']:
                try:
                    with open(input_path, 'r', encoding=encoding) as f:
                        text = f.read()
                    break
                except:
                    continue
            else:
                raise ValueError(f"Не удалось прочитать файл {file_path}")
        
        # Очищаем текст
        cleaned_text = self.clean_text(text, aggressive=aggressive)
        
        # Определяем путь для сохранения
        if output_path:
            output_path_obj = Path(output_path)
        else:
            output_path_obj = input_path
        
        # Сохраняем
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path_obj, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
        
        logger.info(f"✅ Файл очищен: {output_path_obj}")
        
        return str(output_path_obj)
    
    def clean_directory(self, directory: str, pattern: str = "*.txt", aggressive: bool = True) -> List[str]:
        """
        Очищает все текстовые файлы в директории
        
        Args:
            directory: Путь к директории
            pattern: Шаблон для поиска файлов (по умолчанию *.txt)
            aggressive: Использовать агрессивную очистку
        
        Returns:
            Список путей к очищенным файлам
        """
        from pathlib import Path
        
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"Директория не найдена: {directory}")
        
        cleaned_files = []
        files = list(dir_path.glob(pattern))
        
        logger.info(f"🧹 Найдено файлов для очистки: {len(files)}")
        
        for file_path in files:
            try:
                cleaned_path = self.clean_file(str(file_path), aggressive=aggressive)
                cleaned_files.append(cleaned_path)
            except Exception as e:
                logger.error(f"❌ Ошибка очистки {file_path.name}: {e}")
        
        logger.info(f"✅ Очищено файлов: {len(cleaned_files)}/{len(files)}")
        
        return cleaned_files


# Глобальный экземпляр для удобства использования
legal_text_cleaner = LegalTextCleaner()


def clean_legal_text(text: str, aggressive: bool = True) -> str:
    """
    Удобная функция для быстрой очистки текста
    
    Args:
        text: Исходный текст
        aggressive: Использовать агрессивную очистку
    
    Returns:
        Очищенный текст
    """
    return legal_text_cleaner.clean_text(text, aggressive=aggressive)


def clean_legal_file(file_path: str, output_path: Optional[str] = None, aggressive: bool = True) -> str:
    """
    Удобная функция для очистки файла
    
    Args:
        file_path: Путь к исходному файлу
        output_path: Путь для сохранения (если None, перезаписывает исходный)
        aggressive: Использовать агрессивную очистку
    
    Returns:
        Путь к очищенному файлу
    """
    return legal_text_cleaner.clean_file(file_path, output_path, aggressive)


def clean_legal_directory(directory: str, pattern: str = "*.txt", aggressive: bool = True) -> List[str]:
    """
    Удобная функция для очистки всех файлов в директории
    
    Args:
        directory: Путь к директории
        pattern: Шаблон для поиска файлов
        aggressive: Использовать агрессивную очистку
    
    Returns:
        Список путей к очищенным файлам
    """
    return legal_text_cleaner.clean_directory(directory, pattern, aggressive)

