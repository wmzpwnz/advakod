from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import time
import json

from ..core.database import get_db
from ..models.user import User
from ..models.encryption import EncryptionKey, EncryptedMessage
from ..core.encryption import get_encryption_manager
from ..services.auth_service import AuthService
from ..core.database import get_db
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
auth_service = AuthService()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return auth_service.get_current_user(token, db)

router = APIRouter()

class KeyPairResponse(BaseModel):
    public_key: str
    private_key: str
    key_id: str

class EncryptMessageRequest(BaseModel):
    message: str
    recipient_id: int
    chat_session_id: int
    message_type: str = "text"

class EncryptMessageResponse(BaseModel):
    encrypted_message: str
    algorithm: str
    message_hash: str
    message_id: int

class DecryptMessageRequest(BaseModel):
    message_id: int
    private_key_password: Optional[str] = None

class DecryptMessageResponse(BaseModel):
    decrypted_message: str
    sender_id: int
    created_at: float

@router.post("/generate-keys", response_model=KeyPairResponse)
async def generate_key_pair(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Генерация пары ключей для пользователя"""
    try:
        encryption_manager = get_encryption_manager()
        
        # Генерируем пару ключей
        private_key_pem, public_key_pem = encryption_manager.generate_key_pair()
        
        # Создаем уникальный ID для ключей
        key_id = encryption_manager.generate_session_key()
        
        # Сохраняем ключи в базе данных
        private_key_record = EncryptionKey(
            user_id=current_user.id,
            key_type="rsa_private",
            key_data=private_key_pem.decode(),
            created_at=time.time(),
            expires_at=time.time() + (365 * 24 * 60 * 60)  # 1 год
        )
        
        public_key_record = EncryptionKey(
            user_id=current_user.id,
            key_type="rsa_public",
            key_data=public_key_pem.decode(),
            created_at=time.time(),
            expires_at=time.time() + (365 * 24 * 60 * 60)  # 1 год
        )
        
        db.add(private_key_record)
        db.add(public_key_record)
        db.commit()
        
        return KeyPairResponse(
            public_key=public_key_pem.decode(),
            private_key=private_key_pem.decode(),
            key_id=key_id
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Key generation failed: {str(e)}")

@router.get("/public-key/{user_id}")
async def get_public_key(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение публичного ключа пользователя"""
    try:
        public_key = db.query(EncryptionKey).filter(
            EncryptionKey.user_id == user_id,
            EncryptionKey.key_type == "rsa_public",
            EncryptionKey.is_active == True
        ).first()
        
        if not public_key:
            raise HTTPException(status_code=404, detail="Public key not found")
        
        return {
            "user_id": user_id,
            "public_key": public_key.key_data,
            "created_at": public_key.created_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/encrypt", response_model=EncryptMessageResponse)
async def encrypt_message(
    request: EncryptMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Шифрование сообщения для отправки"""
    try:
        encryption_manager = get_encryption_manager()
        
        # Получаем публичный ключ получателя
        recipient_public_key = db.query(EncryptionKey).filter(
            EncryptionKey.user_id == request.recipient_id,
            EncryptionKey.key_type == "rsa_public",
            EncryptionKey.is_active == True
        ).first()
        
        if not recipient_public_key:
            raise HTTPException(status_code=404, detail="Recipient public key not found")
        
        # Шифруем сообщение
        encrypted_data = encryption_manager.encrypt_message(
            request.message,
            recipient_public_key.key_data.encode()
        )
        
        # Создаем хеш сообщения для проверки целостности
        message_hash = encryption_manager.hash_message(request.message)
        
        # Сохраняем зашифрованное сообщение
        encrypted_message = EncryptedMessage(
            chat_session_id=request.chat_session_id,
            sender_id=current_user.id,
            recipient_id=request.recipient_id,
            encrypted_content=json.dumps(encrypted_data),
            encryption_algorithm=encrypted_data["algorithm"],
            message_hash=message_hash,
            message_type=request.message_type,
            created_at=time.time()
        )
        
        db.add(encrypted_message)
        db.commit()
        
        return EncryptMessageResponse(
            encrypted_message=encrypted_data["encrypted_message"],
            algorithm=encrypted_data["algorithm"],
            message_hash=message_hash,
            message_id=encrypted_message.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Encryption failed: {str(e)}")

@router.post("/decrypt", response_model=DecryptMessageResponse)
async def decrypt_message(
    request: DecryptMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Расшифровка сообщения"""
    try:
        encryption_manager = get_encryption_manager()
        
        # Получаем зашифрованное сообщение
        encrypted_message = db.query(EncryptedMessage).filter(
            EncryptedMessage.id == request.message_id,
            EncryptedMessage.recipient_id == current_user.id
        ).first()
        
        if not encrypted_message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Получаем приватный ключ пользователя
        private_key = db.query(EncryptionKey).filter(
            EncryptionKey.user_id == current_user.id,
            EncryptionKey.key_type == "rsa_private",
            EncryptionKey.is_active == True
        ).first()
        
        if not private_key:
            raise HTTPException(status_code=404, detail="Private key not found")
        
        # Расшифровываем сообщение
        encrypted_data = json.loads(encrypted_message.encrypted_content)
        decrypted_message = encryption_manager.decrypt_message(
            encrypted_data,
            private_key.key_data.encode()
        )
        
        # Проверяем целостность сообщения
        if not encryption_manager.verify_message_integrity(
            decrypted_message, 
            encrypted_message.message_hash
        ):
            raise HTTPException(status_code=400, detail="Message integrity check failed")
        
        # Отмечаем сообщение как прочитанное
        encrypted_message.is_read = True
        db.commit()
        
        return DecryptMessageResponse(
            decrypted_message=decrypted_message,
            sender_id=encrypted_message.sender_id,
            created_at=encrypted_message.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decryption failed: {str(e)}")

@router.get("/messages/{chat_session_id}")
async def get_encrypted_messages(
    chat_session_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение списка зашифрованных сообщений в чате"""
    try:
        messages = db.query(EncryptedMessage).filter(
            EncryptedMessage.chat_session_id == chat_session_id,
            EncryptedMessage.recipient_id == current_user.id
        ).order_by(EncryptedMessage.created_at.desc()).offset(skip).limit(limit).all()
        
        return {
            "messages": [
                {
                    "id": msg.id,
                    "sender_id": msg.sender_id,
                    "encryption_algorithm": msg.encryption_algorithm,
                    "message_type": msg.message_type,
                    "is_read": msg.is_read,
                    "created_at": msg.created_at
                }
                for msg in messages
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/keys")
async def revoke_encryption_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Отзыв всех ключей шифрования пользователя"""
    try:
        # Деактивируем все ключи пользователя
        db.query(EncryptionKey).filter(
            EncryptionKey.user_id == current_user.id
        ).update({"is_active": False})
        
        db.commit()
        
        return {"message": "All encryption keys have been revoked"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/keys/status")
async def get_encryption_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение статуса ключей шифрования пользователя"""
    try:
        keys = db.query(EncryptionKey).filter(
            EncryptionKey.user_id == current_user.id,
            EncryptionKey.is_active == True
        ).all()
        
        has_private_key = any(key.key_type == "rsa_private" for key in keys)
        has_public_key = any(key.key_type == "rsa_public" for key in keys)
        
        return {
            "has_private_key": has_private_key,
            "has_public_key": has_public_key,
            "keys_count": len(keys),
            "encryption_enabled": has_private_key and has_public_key
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
