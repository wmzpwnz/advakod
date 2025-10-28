from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связь с пользователем
    user = relationship("User")
    # Связь с сообщениями
    messages = relationship("ChatMessage", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON, nullable=True)  # Дополнительные данные (источники, время обработки и т.д.)
    
    # Поля для голосовых сообщений
    audio_url = Column(String(500), nullable=True)  # URL аудио файла
    audio_duration = Column(Integer, nullable=True)  # Длительность в секундах
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связь с сессией
    session = relationship("ChatSession", back_populates="messages", overlaps="messages")
    
    # Связи с системой обратной связи
    feedback = relationship("ResponseFeedback", back_populates="message", cascade="all, delete-orphan")
    moderation_reviews = relationship("ModerationReview", back_populates="message", cascade="all, delete-orphan")


class DocumentAnalysis(Base):
    __tablename__ = "document_analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt
    analysis_result = Column(Text, nullable=False)
    risks_found = Column(JSON, nullable=True)  # Список найденных рисков
    recommendations = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связь с пользователем
    user = relationship("User")
