"""
Улучшенная система аутентификации с повышенной безопасностью
"""

import secrets
import string
import hashlib
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SecurePasswordManager:
    """Менеджер безопасных паролей"""
    
    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """Генерирует безопасный пароль"""
        # Используем криптографически стойкий генератор
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Валидирует силу пароля"""
        issues = []
        score = 0
        
        # Проверка длины
        if len(password) < 8:
            issues.append("Пароль должен содержать минимум 8 символов")
        elif len(password) >= 12:
            score += 2
        else:
            score += 1
        
        # Проверка наличия различных типов символов
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        if has_lower:
            score += 1
        else:
            issues.append("Пароль должен содержать строчные буквы")
        
        if has_upper:
            score += 1
        else:
            issues.append("Пароль должен содержать заглавные буквы")
        
        if has_digit:
            score += 1
        else:
            issues.append("Пароль должен содержать цифры")
        
        if has_special:
            score += 1
        else:
            issues.append("Пароль должен содержать специальные символы")
        
        # Проверка на простые пароли
        common_passwords = [
            "password", "123456", "admin", "qwerty", "letmein",
            "welcome", "monkey", "dragon", "master", "hello"
        ]
        
        if password.lower() in common_passwords:
            issues.append("Пароль слишком простой")
            score = 0
        
        # Определяем уровень безопасности
        if score >= 6:
            security_level = "high"
        elif score >= 4:
            security_level = "medium"
        else:
            security_level = "low"
        
        return {
            "is_valid": len(issues) == 0,
            "score": score,
            "security_level": security_level,
            "issues": issues
        }
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Хеширует пароль с солью"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Используем PBKDF2 для хеширования
        import hashlib
        import os
        
        # Генерируем хеш с PBKDF2
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 100,000 итераций
        )
        
        return password_hash.hex(), salt
    
    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """Проверяет пароль"""
        password_hash, _ = SecurePasswordManager.hash_password(password, salt)
        return password_hash == stored_hash


class SessionManager:
    """Менеджер сессий с повышенной безопасностью"""
    
    def __init__(self):
        self.active_sessions = {}
        self.session_timeout = 1800  # 30 минут
    
    def create_session(self, user_id: str, ip_address: str) -> str:
        """Создает новую сессию"""
        session_id = secrets.token_urlsafe(32)
        
        session_data = {
            "user_id": user_id,
            "ip_address": ip_address,
            "created_at": time.time(),
            "last_activity": time.time(),
            "is_active": True
        }
        
        self.active_sessions[session_id] = session_data
        
        # Логируем создание сессии
        logger.info(f"Session created for user {user_id} from {ip_address}")
        
        return session_id
    
    def validate_session(self, session_id: str, ip_address: str) -> bool:
        """Валидирует сессию"""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        
        # Проверяем активность сессии
        if not session["is_active"]:
            return False
        
        # Проверяем IP адрес
        if session["ip_address"] != ip_address:
            logger.warning(f"Session IP mismatch for session {session_id}")
            return False
        
        # Проверяем время жизни сессии
        if time.time() - session["last_activity"] > self.session_timeout:
            self.invalidate_session(session_id)
            return False
        
        # Обновляем время последней активности
        session["last_activity"] = time.time()
        
        return True
    
    def invalidate_session(self, session_id: str):
        """Инвалидирует сессию"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["is_active"] = False
            logger.info(f"Session {session_id} invalidated")
    
    def cleanup_expired_sessions(self):
        """Очищает истекшие сессии"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            if (current_time - session["last_activity"] > self.session_timeout or
                not session["is_active"]):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")


class RateLimiter:
    """Улучшенный rate limiter с защитой от брутфорса"""
    
    def __init__(self):
        self.attempts = {}
        self.blocked_ips = {}
        self.max_attempts = 5
        self.block_duration = 3600  # 1 час
    
    def is_allowed(self, ip_address: str, user_id: Optional[str] = None) -> bool:
        """Проверяет, разрешен ли запрос"""
        current_time = time.time()
        
        # Проверяем, не заблокирован ли IP
        if ip_address in self.blocked_ips:
            if current_time < self.blocked_ips[ip_address]:
                return False
            else:
                del self.blocked_ips[ip_address]
        
        # Проверяем количество попыток
        key = f"{ip_address}:{user_id}" if user_id else ip_address
        
        if key not in self.attempts:
            self.attempts[key] = []
        
        # Очищаем старые попытки (старше 1 часа)
        self.attempts[key] = [
            attempt_time for attempt_time in self.attempts[key]
            if current_time - attempt_time < 3600
        ]
        
        # Если превышен лимит, блокируем IP
        if len(self.attempts[key]) >= self.max_attempts:
            self.blocked_ips[ip_address] = current_time + self.block_duration
            logger.warning(f"IP {ip_address} blocked due to too many attempts")
            return False
        
        return True
    
    def record_attempt(self, ip_address: str, user_id: Optional[str] = None, success: bool = True):
        """Записывает попытку входа"""
        if not success:
            key = f"{ip_address}:{user_id}" if user_id else ip_address
            current_time = time.time()
            
            if key not in self.attempts:
                self.attempts[key] = []
            
            self.attempts[key].append(current_time)
            
            logger.warning(f"Failed login attempt from {ip_address} for user {user_id}")


# Глобальные экземпляры
secure_password_manager = SecurePasswordManager()
session_manager = SessionManager()
rate_limiter = RateLimiter()


def create_secure_admin_user():
    """Создает безопасного администратора"""
    # Генерируем безопасный пароль
    password = secure_password_manager.generate_secure_password(20)
    
    # Валидируем пароль
    validation = secure_password_manager.validate_password_strength(password)
    
    if not validation["is_valid"]:
        raise ValueError(f"Generated password is not secure: {validation['issues']}")
    
    # Хешируем пароль
    password_hash, salt = secure_password_manager.hash_password(password)
    
    admin_data = {
        "username": "admin",
        "email": "admin@ai-lawyer.ru",
        "password": password,  # Только для отображения
        "password_hash": password_hash,
        "salt": salt,
        "full_name": "Системный администратор",
        "is_admin": True,
        "is_premium": True,
        "is_active": True,
        "subscription_type": "enterprise"
    }
    
    return admin_data


def validate_login_attempt(email: str, password: str, ip_address: str) -> Dict[str, Any]:
    """Валидирует попытку входа с повышенной безопасностью"""
    # Проверяем rate limit
    if not rate_limiter.is_allowed(ip_address):
        return {
            "success": False,
            "error": "Too many failed attempts. IP blocked.",
            "blocked_until": rate_limiter.blocked_ips.get(ip_address)
        }
    
    # Валидируем входные данные
    if not email or not password:
        rate_limiter.record_attempt(ip_address, success=False)
        return {
            "success": False,
            "error": "Email and password are required"
        }
    
    # Проверяем формат email
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        rate_limiter.record_attempt(ip_address, success=False)
        return {
            "success": False,
            "error": "Invalid email format"
        }
    
    return {
        "success": True,
        "email": email,
        "password": password,
        "ip_address": ip_address
    }


def get_current_admin_user():
    """Заглушка для получения текущего администратора"""
    # Возвращаем None для совместимости
    return None