"""
Модели для системы уведомлений админ-панели
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class AdminNotification(Base):
    """Модель уведомлений для админ-панели"""
    __tablename__ = "admin_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Получатель уведомления
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Тип уведомления
    type = Column(String(50), nullable=False, index=True)  # system_alert, user_action, backup_status, etc.
    
    # Заголовок и содержание
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Дополнительные данные в JSON формате
    data = Column(JSON, nullable=True)
    
    # Приоритет уведомления
    priority = Column(String(20), default="normal", index=True)  # low, normal, high, critical
    
    # Статус уведомления
    read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime, nullable=True)
    
    # Каналы доставки
    channels = Column(JSON, nullable=True)  # ["websocket", "email", "slack"]
    
    # Статус доставки
    delivery_status = Column(JSON, nullable=True)  # {"websocket": "delivered", "email": "pending"}
    
    # Временные метки
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Связи
    # user = relationship("User", back_populates="admin_notifications")  # Временно отключено
    
    def __repr__(self):
        return f"<AdminNotification(id={self.id}, type={self.type}, user_id={self.user_id})>"
    
    def to_dict(self):
        """Преобразование в словарь для JSON сериализации"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "priority": self.priority,
            "read": self.read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "channels": self.channels,
            "delivery_status": self.delivery_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class NotificationTemplate(Base):
    """Шаблоны уведомлений"""
    __tablename__ = "notification_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Название и тип шаблона
    name = Column(String(100), nullable=False, unique=True, index=True)
    type = Column(String(50), nullable=False, index=True)
    
    # Шаблоны для разных каналов
    title_template = Column(String(200), nullable=False)
    message_template = Column(Text, nullable=False)
    email_template = Column(Text, nullable=True)
    slack_template = Column(Text, nullable=True)
    
    # Настройки
    default_channels = Column(JSON, nullable=True)  # ["websocket", "email"]
    default_priority = Column(String(20), default="normal")
    
    # Условия срабатывания
    trigger_conditions = Column(JSON, nullable=True)
    
    # Статус шаблона
    active = Column(Boolean, default=True, index=True)
    
    # Временные метки
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<NotificationTemplate(id={self.id}, name={self.name}, type={self.type})>"


class NotificationHistory(Base):
    """История отправки уведомлений"""
    __tablename__ = "notification_history"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Связь с уведомлением
    notification_id = Column(Integer, ForeignKey("admin_notifications.id"), nullable=False, index=True)
    
    # Канал доставки
    channel = Column(String(50), nullable=False, index=True)  # websocket, email, slack, telegram
    
    # Статус доставки
    status = Column(String(20), nullable=False, index=True)  # pending, sent, delivered, failed
    
    # Детали доставки
    delivery_details = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Временные метки
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Связи
    notification = relationship("AdminNotification")
    
    def __repr__(self):
        return f"<NotificationHistory(id={self.id}, channel={self.channel}, status={self.status})>"