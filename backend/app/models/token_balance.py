from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class TokenBalance(Base):
    """Модель баланса токенов пользователя"""
    __tablename__ = "token_balances"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    balance = Column(Integer, default=1000, nullable=False)  # Начальный баланс 1000 токенов
    total_earned = Column(Integer, default=0, nullable=False)  # Всего заработано
    total_spent = Column(Integer, default=0, nullable=False)   # Всего потрачено
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь с пользователем (временно отключена)
    # user = relationship("User", back_populates="token_balance")


class TokenTransaction(Base):
    """Модель транзакций токенов"""
    __tablename__ = "token_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)  # Положительное - пополнение, отрицательное - списание
    transaction_type = Column(String(50), nullable=False)  # 'chat_message', 'bonus', 'purchase', 'refund'
    description = Column(Text, nullable=True)
    chat_session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=True)
    chat_message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    user = relationship("User")
    chat_session = relationship("ChatSession")
    chat_message = relationship("ChatMessage")
