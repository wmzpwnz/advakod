"""
Сервис двухфакторной аутентификации (2FA)
"""

import pyotp
import qrcode
import io
import base64
import secrets
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.user import User
from ..core.database import get_db

logger = logging.getLogger(__name__)


class TwoFactorService:
    """Сервис двухфакторной аутентификации"""
    
    def __init__(self):
        self.issuer_name = "АДВАКОД - ИИ-Юрист"
    
    def generate_secret(self, user_email: str) -> str:
        """Генерация секретного ключа для 2FA"""
        secret = pyotp.random_base32()
        logger.info(f"Generated 2FA secret for user: {user_email}")
        return secret
    
    def generate_qr_code(self, user_email: str, secret: str) -> str:
        """Генерация QR-кода для настройки 2FA"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=self.issuer_name
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Конвертируем в base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def generate_backup_codes(self, count: int = 10) -> list:
        """Генерация резервных кодов"""
        backup_codes = []
        for _ in range(count):
            code = secrets.token_urlsafe(8).upper()
            backup_codes.append(code)
        
        logger.info(f"Generated {count} backup codes")
        return backup_codes
    
    def verify_totp(self, secret: str, token: str) -> bool:
        """Проверка TOTP токена"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=1)
        except Exception as e:
            logger.error(f"TOTP verification failed: {e}")
            return False
    
    def verify_backup_code(self, user: User, code: str) -> bool:
        """Проверка резервного кода"""
        if not user.backup_codes:
            return False
        
        try:
            import json
            backup_codes = json.loads(user.backup_codes)
            
            if code in backup_codes:
                # Удаляем использованный код
                backup_codes.remove(code)
                user.backup_codes = json.dumps(backup_codes)
                return True
            
            return False
        except Exception as e:
            logger.error(f"Backup code verification failed: {e}")
            return False
    
    def setup_2fa(self, user: User, db: Session) -> Dict[str, Any]:
        """Настройка 2FA для пользователя"""
        if user.two_factor_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA уже настроена для этого пользователя"
            )
        
        # Генерируем секрет и резервные коды
        secret = self.generate_secret(user.email)
        backup_codes = self.generate_backup_codes()
        
        # Сохраняем секрет (временно, до подтверждения)
        user.two_factor_secret = secret
        user.backup_codes = json.dumps(backup_codes)
        
        # Генерируем QR-код
        qr_code = self.generate_qr_code(user.email, secret)
        
        db.commit()
        
        logger.info(f"2FA setup initiated for user: {user.email}")
        
        return {
            "secret": secret,
            "qr_code": qr_code,
            "backup_codes": backup_codes,
            "message": "Отсканируйте QR-код в приложении аутентификатора и введите код для подтверждения"
        }
    
    def confirm_2fa(self, user: User, token: str, db: Session) -> bool:
        """Подтверждение настройки 2FA"""
        if not user.two_factor_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA не была инициирована"
            )
        
        # Проверяем токен
        if not self.verify_totp(user.two_factor_secret, token):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный код подтверждения"
            )
        
        # Активируем 2FA
        user.two_factor_enabled = True
        db.commit()
        
        logger.info(f"2FA confirmed and enabled for user: {user.email}")
        return True
    
    def verify_2fa(self, user: User, token: str) -> bool:
        """Проверка 2FA при входе"""
        if not user.two_factor_enabled:
            return True  # 2FA не включена
        
        if not user.two_factor_secret:
            logger.error(f"2FA enabled but no secret for user: {user.email}")
            return False
        
        # Проверяем TOTP токен
        if self.verify_totp(user.two_factor_secret, token):
            return True
        
        # Проверяем резервный код
        if self.verify_backup_code(user, token):
            return True
        
        return False
    
    def disable_2fa(self, user: User, password: str, db: Session) -> bool:
        """Отключение 2FA"""
        # Проверяем пароль
        from .auth_service import auth_service
        if not auth_service.verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный пароль"
            )
        
        # Отключаем 2FA
        user.two_factor_enabled = False
        user.two_factor_secret = None
        user.backup_codes = None
        
        db.commit()
        
        logger.info(f"2FA disabled for user: {user.email}")
        return True
    
    def regenerate_backup_codes(self, user: User, db: Session) -> list:
        """Регенерация резервных кодов"""
        if not user.two_factor_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA не включена"
            )
        
        backup_codes = self.generate_backup_codes()
        user.backup_codes = json.dumps(backup_codes)
        
        db.commit()
        
        logger.info(f"Backup codes regenerated for user: {user.email}")
        return backup_codes


# Глобальный экземпляр
two_factor_service = TwoFactorService()