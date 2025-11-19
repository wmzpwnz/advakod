"""Валидаторы для входных данных"""
import re
import json
from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class ValidationError(HTTPException):
    """Кастомная ошибка валидации"""
    def __init__(self, detail: str, field: str = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": detail,
                "field": field,
                "error_code": "VALIDATION_ERROR"
            }
        )


def validate_email(email: str) -> str:
    """Валидация email адреса"""
    if not email or len(email.strip()) == 0:
        raise ValidationError("Email обязателен для заполнения", "email")
    
    email = email.strip().lower()
    
    # Простая проверка формата email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationError("Некорректный формат email", "email")
    
    if len(email) > 255:
        raise ValidationError("Email слишком длинный (максимум 255 символов)", "email")
    
    return email


def validate_password(password: str) -> str:
    """Валидация пароля с усиленными требованиями безопасности"""
    if not password:
        raise ValidationError("Пароль обязателен для заполнения", "password")
    
    # Увеличиваем минимальную длину до 12 символов
    if len(password) < 12:
        raise ValidationError("Пароль должен содержать минимум 12 символов", "password")
    
    if len(password) > 128:
        raise ValidationError("Пароль слишком длинный (максимум 128 символов)", "password")
    
    # Проверка на наличие букв
    if not re.search(r'[a-zA-Zа-яА-Я]', password):
        raise ValidationError("Пароль должен содержать хотя бы одну букву", "password")
    
    # Проверка на наличие цифр
    if not re.search(r'\d', password):
        raise ValidationError("Пароль должен содержать хотя бы одну цифру", "password")
    
    # Проверка на наличие специальных символов
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\/?]', password):
        raise ValidationError("Пароль должен содержать хотя бы один специальный символ (!@#$%^&*()_+-=[]{}|;':\",./<>?)", "password")
    
    # Проверка на наличие заглавных букв
    if not re.search(r'[A-ZА-Я]', password):
        raise ValidationError("Пароль должен содержать хотя бы одну заглавную букву", "password")
    
    # Проверка на наличие строчных букв
    if not re.search(r'[a-zа-я]', password):
        raise ValidationError("Пароль должен содержать хотя бы одну строчную букву", "password")
    
    # Проверка на простые пароли (словарные атаки)
    common_passwords = [
        'password', '123456', '123456789', 'qwerty', 'abc123', 
        'password123', 'admin', 'letmein', 'welcome', 'monkey',
        'пароль', '1234567890', 'password1', 'qwerty123'
    ]
    
    if password.lower() in common_passwords:
        raise ValidationError("Пароль слишком простой. Используйте более сложный пароль", "password")
    
    # Проверка на повторяющиеся символы
    if re.search(r'(.)\1{2,}', password):
        raise ValidationError("Пароль не должен содержать более 2 одинаковых символов подряд", "password")
    
    return password


def validate_username(username: str) -> str:
    """Валидация имени пользователя"""
    if not username or len(username.strip()) == 0:
        raise ValidationError("Имя пользователя обязательно для заполнения", "username")
    
    username = username.strip()
    
    if len(username) < 3:
        raise ValidationError("Имя пользователя должно содержать минимум 3 символа", "username")
    
    if len(username) > 50:
        raise ValidationError("Имя пользователя слишком длинное (максимум 50 символов)", "username")
    
    # Разрешаем только буквы, цифры, дефисы и подчеркивания
    if not re.match(r'^[a-zA-Zа-яА-Я0-9_-]+$', username):
        raise ValidationError("Имя пользователя может содержать только буквы, цифры, дефисы и подчеркивания", "username")
    
    return username


def validate_chat_message(message: str) -> str:
    """Валидация сообщения чата с улучшенными проверками"""
    if not message or len(message.strip()) == 0:
        raise ValidationError("Сообщение не может быть пустым", "message")
    
    message = message.strip()
    
    if len(message) > 4000:
        raise ValidationError("Сообщение слишком длинное (максимум 4000 символов)", "message")
    
    # Проверка на спам (расширенная)
    spam_patterns = [
        r'(.)\1{10,}',  # Повторяющиеся символы
        r'[A-Z]{20,}',  # Слишком много заглавных букв подряд
        r'(.)\1{5,}',   # Повторяющиеся символы (более мягкая проверка)
        r'[!@#$%^&*()]{10,}',  # Слишком много специальных символов
        r'(.)\1{3,}.*(.)\2{3,}.*(.)\3{3,}',  # Множественные повторения
    ]
    
    for pattern in spam_patterns:
        if re.search(pattern, message):
            raise ValidationError("Сообщение выглядит как спам", "message")
    
    # Проверка на потенциально опасный контент
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',  # JavaScript
        r'javascript:',  # JavaScript URL
        r'data:text/html',  # HTML data URL
        r'<iframe[^>]*>',  # iframe
        r'<object[^>]*>',  # object
        r'<embed[^>]*>',  # embed
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, message, re.IGNORECASE):
            raise ValidationError("Сообщение содержит потенциально опасный контент", "message")
    
    # Проверка на SQL injection (базовая)
    sql_patterns = [
        r'union\s+select',
        r'drop\s+table',
        r'delete\s+from',
        r'insert\s+into',
        r'update\s+set',
        r'--',  # SQL комментарии
        r'/\*.*\*/',  # SQL комментарии
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, message, re.IGNORECASE):
            raise ValidationError("Сообщение содержит подозрительные SQL конструкции", "message")
    
    return message


def validate_full_name(full_name: Optional[str]) -> Optional[str]:
    """Валидация полного имени"""
    if not full_name:
        return None
    
    full_name = full_name.strip()
    
    if len(full_name) == 0:
        return None
    
    if len(full_name) > 100:
        raise ValidationError("Полное имя слишком длинное (максимум 100 символов)", "full_name")
    
    # Разрешаем буквы, цифры, пробелы, дефисы и апострофы
    if not re.match(r'^[a-zA-Zа-яА-ЯёЁ0-9\s\'-]+$', full_name):
        raise ValidationError("Полное имя может содержать только буквы, цифры, пробелы, дефисы и апострофы", "full_name")
    
    return full_name


def validate_company_name(company_name: Optional[str]) -> Optional[str]:
    """Валидация названия компании"""
    if not company_name:
        return None
    
    company_name = company_name.strip()
    
    if len(company_name) == 0:
        return None
    
    if len(company_name) > 255:
        raise ValidationError("Название компании слишком длинное (максимум 255 символов)", "company_name")
    
    return company_name


def validate_inn(inn: Optional[str]) -> Optional[str]:
    """Валидация ИНН"""
    if not inn:
        return None
    
    inn = inn.strip().replace(' ', '').replace('-', '')
    
    if len(inn) == 0:
        return None
    
    # ИНН может быть 10 или 12 цифр
    if not re.match(r'^\d{10}$|^\d{12}$', inn):
        raise ValidationError("ИНН должен содержать 10 или 12 цифр", "inn")
    
    return inn


def sanitize_html_input(text: str) -> str:
    """Очистка HTML тегов из пользовательского ввода"""
    if not text:
        return text
    
    # Удаляем HTML теги
    text = re.sub(r'<[^>]+>', '', text)
    
    # Удаляем потенциально опасные символы
    text = re.sub(r'[<>&"\'`]', '', text)
    
    return text.strip()


def validate_json_input(data: str) -> str:
    """Валидация JSON входных данных"""
    if not data or len(data.strip()) == 0:
        raise ValidationError("JSON данные не могут быть пустыми", "json")
    
    data = data.strip()
    
    # Проверяем размер
    if len(data) > 100000:  # 100KB
        raise ValidationError("JSON данные слишком большие (максимум 100KB)", "json")
    
    # Проверяем на потенциально опасные конструкции
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',  # JavaScript
        r'javascript:',  # JavaScript URL
        r'eval\s*\(',  # eval function
        r'Function\s*\(',  # Function constructor
        r'setTimeout\s*\(',  # setTimeout
        r'setInterval\s*\(',  # setInterval
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, data, re.IGNORECASE):
            raise ValidationError("JSON содержит потенциально опасные конструкции", "json")
    
    return data


def validate_api_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Валидация входных данных API"""
    if not isinstance(data, dict):
        raise ValidationError("Входные данные должны быть словарем", "data")
    
    # Проверяем размер
    json_str = json.dumps(data)
    if len(json_str) > 50000:  # 50KB
        raise ValidationError("Входные данные слишком большие (максимум 50KB)", "data")
    
    # Проверяем на подозрительные ключи
    suspicious_keys = [
        '__proto__', 'constructor', 'prototype', 'eval', 'function',
        'script', 'javascript', 'vbscript', 'onload', 'onerror'
    ]
    
    for key in data.keys():
        if any(suspicious in key.lower() for suspicious in suspicious_keys):
            raise ValidationError(f"Подозрительный ключ: {key}", "data")
    
    # Проверяем значения на XSS
    for key, value in data.items():
        if isinstance(value, str):
            if re.search(r'<script[^>]*>.*?</script>', value, re.IGNORECASE):
                raise ValidationError(f"Потенциально опасное содержимое в поле {key}", "data")
    
    return data


def validate_file_upload(filename: str, content_type: str, file_size: int) -> None:
    """Валидация загружаемого файла с усиленными проверками безопасности"""
    # Разрешенные типы файлов
    allowed_types = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword',
        'text/plain',
        'text/markdown'
    }
    
    # Разрешенные расширения
    allowed_extensions = {'.pdf', '.docx', '.doc', '.txt', '.md'}
    
    # Проверяем тип файла
    if content_type not in allowed_types:
        raise ValidationError(f"Неподдерживаемый тип файла: {content_type}", "file")
    
    # Проверяем расширение файла
    file_extension = None
    if '.' in filename:
        file_extension = '.' + filename.rsplit('.', 1)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise ValidationError(f"Неподдерживаемое расширение файла: {file_extension}", "file")
    
    # Проверяем размер файла (максимум 10 МБ)
    max_size = 10 * 1024 * 1024  # 10 MB
    if file_size > max_size:
        raise ValidationError(f"Файл слишком большой. Максимальный размер: {max_size // (1024*1024)} МБ", "file")
    
    # Проверяем минимальный размер файла (защита от пустых файлов)
    min_size = 1  # 1 байт
    if file_size < min_size:
        raise ValidationError("Файл не может быть пустым", "file")
    
    # Проверяем имя файла на безопасность
    if not re.match(r'^[a-zA-Zа-яА-Я0-9._\-\s]+$', filename):
        raise ValidationError("Имя файла содержит недопустимые символы", "file")
    
    # Проверяем длину имени файла
    if len(filename) > 255:
        raise ValidationError("Имя файла слишком длинное (максимум 255 символов)", "file")
    
    # Проверяем на потенциально опасные имена файлов
    dangerous_names = [
        '..', '.', '...', 'con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3', 'com4', 'com5',
        'com6', 'com7', 'com8', 'com9', 'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6',
        'lpt7', 'lpt8', 'lpt9'
    ]
    
    base_name = filename.split('.')[0].lower()
    if base_name in dangerous_names:
        raise ValidationError("Имя файла зарезервировано системой", "file")
    
    # Проверяем на двойные расширения (потенциально опасные)
    if filename.count('.') > 1:
        # Разрешаем только один знак точки (расширение)
        if not re.match(r'^[^.]+\.[^.]+$', filename):
            raise ValidationError("Недопустимое имя файла с множественными расширениями", "file")
