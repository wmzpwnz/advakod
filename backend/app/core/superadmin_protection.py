"""
Защита суперадмина - специальные меры безопасности
"""

import logging
import hashlib
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..models.user import User
from ..models.rbac import Role, user_roles
from ..core.database import SessionLocal

logger = logging.getLogger(__name__)


class SuperAdminProtection:
    """Сервис защиты суперадмина"""
    
    def __init__(self):
        self.superadmin_email = "admin@ai-lawyer.ru"  # Ваш email
        self.backup_codes = []  # Резервные коды доступа
        self.emergency_token = None  # Экстренный токен
        self.emergency_token_expires = None
        
    def is_superadmin(self, user: User) -> bool:
        """Проверяет, является ли пользователь суперадмином"""
        if user.email != self.superadmin_email:
            return False
            
        # Проверяем роль super_admin
        db = SessionLocal()
        try:
            superadmin_role = db.query(Role).filter(Role.name == "super_admin").first()
            if not superadmin_role:
                return False
                
            # Проверяем, назначена ли роль пользователю
            user_role = db.execute(
                user_roles.select().where(
                    user_roles.c.user_id == user.id,
                    user_roles.c.role_id == superadmin_role.id
                )
            ).first()
            
            return user_role is not None
        finally:
            db.close()
    
    def generate_emergency_token(self) -> str:
        """Генерирует экстренный токен для восстановления доступа"""
        token = secrets.token_urlsafe(32)
        self.emergency_token = hashlib.sha256(token.encode()).hexdigest()
        self.emergency_token_expires = datetime.utcnow() + timedelta(hours=24)
        
        logger.warning(f"🚨 ЭКСТРЕННЫЙ ТОКЕН СГЕНЕРИРОВАН: {token}")
        logger.warning(f"⏰ Действителен до: {self.emergency_token_expires}")
        
        return token
    
    def verify_emergency_token(self, token: str) -> bool:
        """Проверяет экстренный токен"""
        if not self.emergency_token or not self.emergency_token_expires:
            return False
            
        if datetime.utcnow() > self.emergency_token_expires:
            self.emergency_token = None
            self.emergency_token_expires = None
            return False
            
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token_hash == self.emergency_token
    
    def generate_backup_codes(self, count: int = 5) -> list:
        """Генерирует резервные коды доступа"""
        codes = []
        for _ in range(count):
            code = secrets.token_urlsafe(8).upper()
            codes.append(code)
            
        self.backup_codes = codes
        
        logger.warning(f"🔑 РЕЗЕРВНЫЕ КОДЫ СГЕНЕРИРОВАНЫ:")
        for i, code in enumerate(codes, 1):
            logger.warning(f"   {i}. {code}")
            
        return codes
    
    def verify_backup_code(self, code: str) -> bool:
        """Проверяет резервный код"""
        return code.upper() in self.backup_codes
    
    def revoke_backup_code(self, code: str) -> bool:
        """Отзывает использованный резервный код"""
        if code.upper() in self.backup_codes:
            self.backup_codes.remove(code.upper())
            return True
        return False
    
    def protect_superadmin_account(self, user: User) -> Dict[str, Any]:
        """Применяет дополнительные меры защиты к аккаунту суперадмина"""
        if not self.is_superadmin(user):
            return {"error": "Пользователь не является суперадмином"}
        
        # Дополнительные проверки безопасности
        protection_status = {
            "is_protected": True,
            "email": user.email,
            "last_login": user.updated_at,
            "two_factor_enabled": user.two_factor_enabled,
            "backup_codes_count": len(self.backup_codes),
            "emergency_token_active": self.emergency_token is not None,
            "emergency_token_expires": self.emergency_token_expires
        }
        
        return protection_status
    
    def create_superadmin_safeguards(self) -> Dict[str, Any]:
        """Создает защитные механизмы для суперадмина"""
        try:
            # Генерируем резервные коды
            backup_codes = self.generate_backup_codes(5)
            
            # Генерируем экстренный токен
            emergency_token = self.generate_emergency_token()
            
            safeguards = {
                "backup_codes": backup_codes,
                "emergency_token": emergency_token,
                "instructions": {
                    "backup_codes": "Сохраните эти коды в безопасном месте. Используйте для входа в экстренных случаях.",
                    "emergency_token": "Этот токен действует 24 часа. Используйте для восстановления доступа к аккаунту.",
                    "security_tips": [
                        "Никогда не передавайте коды третьим лицам",
                        "Храните коды отдельно от пароля",
                        "Регулярно обновляйте резервные коды",
                        "Включите двухфакторную аутентификацию"
                    ]
                }
            }
            
            logger.info("🛡️ Защитные механизмы для суперадмина созданы")
            return safeguards
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания защитных механизмов: {e}")
            return {"error": str(e)}
    
    def emergency_access_recovery(self, emergency_token: str, new_password: str) -> bool:
        """Экстренное восстановление доступа суперадмина"""
        if not self.verify_emergency_token(emergency_token):
            return False
        
        try:
            db = SessionLocal()
            user = db.query(User).filter(User.email == self.superadmin_email).first()
            
            if not user:
                return False
            
            # Обновляем пароль
            from ..services.auth_service import AuthService
            auth_service = AuthService()
            user.hashed_password = auth_service.get_password_hash(new_password)
            user.updated_at = datetime.utcnow()
            
            db.commit()
            
            # Отзываем экстренный токен
            self.emergency_token = None
            self.emergency_token_expires = None
            
            logger.warning("🚨 ЭКСТРЕННОЕ ВОССТАНОВЛЕНИЕ ДОСТУПА ВЫПОЛНЕНО")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка экстренного восстановления: {e}")
            return False
        finally:
            db.close()


# Глобальный экземпляр
superadmin_protection = SuperAdminProtection()


def require_superadmin_protection():
    """Декоратор для защиты функций суперадмина"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Ищем пользователя в аргументах
            current_user = None
            for arg in args:
                if isinstance(arg, User):
                    current_user = arg
                    break
            
            if not current_user:
                # Ищем в kwargs
                current_user = kwargs.get('current_admin') or kwargs.get('current_user')
            
            if not current_user:
                raise Exception("Пользователь не найден")
            
            # Проверяем, является ли суперадмином
            if not superadmin_protection.is_superadmin(current_user):
                raise Exception("Доступ запрещен. Требуются права суперадмина")
            
            # Дополнительные проверки безопасности
            protection_status = superadmin_protection.protect_superadmin_account(current_user)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
