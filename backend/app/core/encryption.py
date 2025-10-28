"""
Сервис шифрования данных для защиты чувствительной информации
"""
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Union, Optional
from ..core.config import settings

logger = logging.getLogger(__name__)


class EncryptionService:
    """Сервис шифрования данных"""
    
    def __init__(self):
        self._fernet = None
        self._initialize_fernet()
    
    def _initialize_fernet(self):
        """Инициализация Fernet для шифрования"""
        try:
            # Создаем ключ из ENCRYPTION_KEY
            key = settings.ENCRYPTION_KEY.encode()
            
            # Используем PBKDF2 для создания ключа из пароля
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'advakod_salt_2024',  # Фиксированная соль для консистентности
                iterations=100000,
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(key))
            
            self._fernet = Fernet(derived_key)
            logger.info("✅ Encryption service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize encryption service: {e}")
            raise
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """
        Шифрует данные
        
        Args:
            data: Данные для шифрования (строка или байты)
            
        Returns:
            Зашифрованные данные в base64 формате
        """
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            encrypted_data = self._fernet.encrypt(data)
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"❌ Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Расшифровывает данные
        
        Args:
            encrypted_data: Зашифрованные данные в base64 формате
            
        Returns:
            Расшифрованные данные в виде строки
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self._fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"❌ Decryption failed: {e}")
            raise
    
    def encrypt_file(self, file_path: str, output_path: Optional[str] = None) -> str:
        """
        Шифрует файл
        
        Args:
            file_path: Путь к файлу для шифрования
            output_path: Путь для сохранения зашифрованного файла
            
        Returns:
            Путь к зашифрованному файлу
        """
        try:
            with open(file_path, 'rb') as file:
                file_data = file.read()
            
            encrypted_data = self.encrypt(file_data)
            
            if output_path is None:
                output_path = file_path + '.encrypted'
            
            with open(output_path, 'w') as file:
                file.write(encrypted_data)
            
            logger.info(f"✅ File encrypted: {file_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ File encryption failed: {e}")
            raise
    
    def decrypt_file(self, encrypted_file_path: str, output_path: Optional[str] = None) -> str:
        """
        Расшифровывает файл
        
        Args:
            encrypted_file_path: Путь к зашифрованному файлу
            output_path: Путь для сохранения расшифрованного файла
            
        Returns:
            Путь к расшифрованному файлу
        """
        try:
            with open(encrypted_file_path, 'r') as file:
                encrypted_data = file.read()
            
            decrypted_data = self.decrypt(encrypted_data)
            
            if output_path is None:
                output_path = encrypted_file_path.replace('.encrypted', '')
            
            with open(output_path, 'wb') as file:
                file.write(decrypted_data.encode('utf-8'))
            
            logger.info(f"✅ File decrypted: {encrypted_file_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ File decryption failed: {e}")
            raise
    
    def hash_sensitive_data(self, data: str) -> str:
        """
        Создает хеш для чувствительных данных (необратимый)
        
        Args:
            data: Данные для хеширования
            
        Returns:
            SHA-256 хеш данных
        """
        try:
            import hashlib
            return hashlib.sha256(data.encode('utf-8')).hexdigest()
            
        except Exception as e:
            logger.error(f"❌ Hashing failed: {e}")
            raise


# Глобальный экземпляр сервиса шифрования
encryption_service = EncryptionService()