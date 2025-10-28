from sqlalchemy import Column, Integer, String, Text, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base

class EncryptionKey(Base):
    __tablename__ = "encryption_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_type = Column(String(50), nullable=False)  # rsa_private, rsa_public, session
    key_data = Column(Text, nullable=False)  # Зашифрованный ключ
    is_active = Column(Boolean, default=True)
    created_at = Column(Float, nullable=False)
    expires_at = Column(Float, nullable=True)
    
    # Связь с пользователем
    user = relationship("User", )

class EncryptedMessage(Base):
    __tablename__ = "encrypted_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Зашифрованные данные
    encrypted_content = Column(Text, nullable=False)
    encryption_algorithm = Column(String(50), nullable=False)
    message_hash = Column(String(64), nullable=False)  # SHA256 хеш для проверки целостности
    
    # Метаданные
    message_type = Column(String(50), default="text")  # text, file, image
    is_read = Column(Boolean, default=False)
    created_at = Column(Float, nullable=False)
    
    # Связи
    chat_session = relationship("ChatSession", )
    sender = relationship("User", foreign_keys=[sender_id], )
    recipient = relationship("User", foreign_keys=[recipient_id], )
