"""
Улучшенный сервис двухфакторной аутентификации
"""
import pyotp
import qrcode
import io
import base64
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models.user import User
from ..core.encryption import encryption_service

logger = logging.getLogger(__name__)


class Enhanced2FAService:
    """Улучшенный сервис двухфакторной аутентификации"""
    
    def __init__(self):
        self.issuer_name = "АДВАКОД - ИИ-Юрист"
        self.backup_codes_count = 10
    
    def generate_secret(self, user: User) -> str:
        """
        Генерирует секретный ключ для 2FA
        
        Args:
            user: Пользователь
            
        Returns:
            Секретный ключ в base32 формате
        """
        try:
            secret = pyotp.random_base32()
            logger.info(f"✅ Generated 2FA secret for user {user.id}")
            return secret
            
        except Exception as e:
            logger.error(f"❌ Failed to generate 2FA secret: {e}")
            raise
    
    def generate_qr_code(self, user: User, secret: str) -> str:
        """
        Генерирует QR код для настройки 2FA
        
        Args:
            user: Пользователь
            secret: Секретный ключ
            
        Returns:
            Base64 закодированный QR код
        """
        try:
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user.email,
                issuer_name=self.issuer_name
            )
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Конвертируем в base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            logger.info(f"✅ Generated QR code for user {user.id}")
            return img_str
            
        except Exception as e:
            logger.error(f"❌ Failed to generate QR code: {e}")
            raise
    
    def generate_backup_codes(self) -> List[str]:
        """
        Генерирует резервные коды для восстановления
        
        Returns:
            Список резервных кодов
        """
        try:
            import secrets
            import string
            
            codes = []
            for _ in range(self.backup_codes_count):
                code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
                codes.append(code)
            
            logger.info(f"✅ Generated {len(codes)} backup codes")
            return codes
            
        except Exception as e:
            logger.error(f"❌ Failed to generate backup codes: {e}")
            raise
    
    def verify_totp(self, secret: str, token: str) -> bool:
        """
        Проверяет TOTP токен
        
        Args:
            secret: Секретный ключ
            token: Токен для проверки
            
        Returns:
            True если токен валиден
        """
        try:
            totp = pyotp.TOTP(secret)
            is_valid = totp.verify(token, valid_window=1)  # Разрешаем отклонение в 1 период
            
            if is_valid:
                logger.info("✅ TOTP token verified successfully")
            else:
                logger.warning("❌ Invalid TOTP token")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"❌ TOTP verification failed: {e}")
            return False
    
    def verify_backup_code(self, user: User, code: str) -> bool:
        """
        Проверяет резервный код
        
        Args:
            user: Пользователь
            code: Резервный код
            
        Returns:
            True если код валиден
        """
        try:
            if not user.backup_codes:
                return False
            
            # Расшифровываем резервные коды
            decrypted_codes = encryption_service.decrypt(user.backup_codes)
            backup_codes = decrypted_codes.split(',')
            
            if code in backup_codes:
                # Удаляем использованный код
                backup_codes.remove(code)
                updated_codes = ','.join(backup_codes)
                user.backup_codes = encryption_service.encrypt(updated_codes)
                
                logger.info(f"✅ Backup code verified for user {user.id}")
                return True
            else:
                logger.warning(f"❌ Invalid backup code for user {user.id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Backup code verification failed: {e}")
            return False
    
    def setup_2fa(self, user: User) -> Dict[str, Any]:
        """
        Настраивает 2FA для пользователя
        
        Args:
            user: Пользователь
            
        Returns:
            Данные для настройки 2FA
        """
        try:
            secret = self.generate_secret(user)
            qr_code = self.generate_qr_code(user, secret)
            backup_codes = self.generate_backup_codes()
            
            # Шифруем секрет и резервные коды
            encrypted_secret = encryption_service.encrypt(secret)
            encrypted_backup_codes = encryption_service.encrypt(','.join(backup_codes))
            
            # Сохраняем в пользователе
            user.two_factor_secret = encrypted_secret
            user.backup_codes = encrypted_backup_codes
            
            logger.info(f"✅ 2FA setup completed for user {user.id}")
            
            return {
                "secret": secret,  # Возвращаем незашифрованный для QR кода
                "qr_code": qr_code,
                "backup_codes": backup_codes,
                "manual_entry_key": secret
            }
            
        except Exception as e:
            logger.error(f"❌ 2FA setup failed: {e}")
            raise
    
    def enable_2fa(self, user: User, verification_token: str) -> bool:
        """
        Включает 2FA после верификации
        
        Args:
            user: Пользователь
            verification_token: Токен для верификации
            
        Returns:
            True если 2FA успешно включен
        """
        try:
            if not user.two_factor_secret:
                return False
            
            # Расшифровываем секрет
            secret = encryption_service.decrypt(user.two_factor_secret)
            
            # Проверяем токен
            if self.verify_totp(secret, verification_token):
                user.two_factor_enabled = True
                logger.info(f"✅ 2FA enabled for user {user.id}")
                return True
            else:
                logger.warning(f"❌ Failed to enable 2FA for user {user.id} - invalid token")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to enable 2FA: {e}")
            return False
    
    def disable_2fa(self, user: User, verification_token: str) -> bool:
        """
        Отключает 2FA
        
        Args:
            user: Пользователь
            verification_token: Токен для верификации
            
        Returns:
            True если 2FA успешно отключен
        """
        try:
            if not user.two_factor_enabled or not user.two_factor_secret:
                return False
            
            # Расшифровываем секрет
            secret = encryption_service.decrypt(user.two_factor_secret)
            
            # Проверяем токен
            if self.verify_totp(secret, verification_token):
                user.two_factor_enabled = False
                user.two_factor_secret = None
                user.backup_codes = None
                logger.info(f"✅ 2FA disabled for user {user.id}")
                return True
            else:
                logger.warning(f"❌ Failed to disable 2FA for user {user.id} - invalid token")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to disable 2FA: {e}")
            return False
    
    def verify_2fa(self, user: User, token: str) -> bool:
        """
        Проверяет 2FA токен (TOTP или резервный код)
        
        Args:
            user: Пользователь
            token: Токен для проверки
            
        Returns:
            True если токен валиден
        """
        try:
            if not user.two_factor_enabled:
                return True  # 2FA не включен
            
            # Сначала пробуем TOTP
            if user.two_factor_secret:
                secret = encryption_service.decrypt(user.two_factor_secret)
                if self.verify_totp(secret, token):
                    return True
            
            # Затем пробуем резервный код
            if user.backup_codes:
                if self.verify_backup_code(user, token):
                    return True
            
            logger.warning(f"❌ 2FA verification failed for user {user.id}")
            return False
            
        except Exception as e:
            logger.error(f"❌ 2FA verification failed: {e}")
            return False
    
    def is_2fa_required(self, user: User) -> bool:
        """
        Проверяет, требуется ли 2FA для пользователя
        
        Args:
            user: Пользователь
            
        Returns:
            True если требуется 2FA
        """
        return user.is_admin or user.two_factor_enabled


# Глобальный экземпляр сервиса 2FA
enhanced_2fa_service = Enhanced2FAService()
