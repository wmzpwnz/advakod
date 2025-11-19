from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import enum

class ActionType(str, enum.Enum):
    """Типы действий для аудит логов"""
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    CHAT_MESSAGE = "chat_message"
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    PROFILE_UPDATE = "profile_update"
    PASSWORD_CHANGE = "password_change"
    TWO_FACTOR_ENABLE = "two_factor_enable"
    TWO_FACTOR_DISABLE = "two_factor_disable"
    API_ACCESS = "api_access"
    PAYMENT = "payment"
    SUBSCRIPTION_CHANGE = "subscription_change"
    DATA_EXPORT = "data_export"
    DATA_DELETE = "data_delete"
    ADMIN_ACTION = "admin_action"
    ADMIN_LOGIN = "admin_login"  # Добавлено для админ логина
    ADMIN_LOGOUT = "admin_logout"  # Добавлено для админ логаута

class SeverityLevel(str, enum.Enum):
    """Уровни серьезности для аудит логов"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AuditLog(Base):
    """Модель для аудит логов"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Пользователь
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    user = relationship("User", foreign_keys=[user_id])
    
    # Детали действия
    action = Column(Enum(ActionType), nullable=False, index=True)
    resource = Column(String(255), nullable=True)  # Ресурс, с которым взаимодействовали
    resource_id = Column(String(255), nullable=True)  # ID ресурса
    
    # Контекст
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True, index=True)
    
    # Детали
    description = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)  # Дополнительные детали в JSON
    
    # Метаданные
    severity = Column(Enum(SeverityLevel), default=SeverityLevel.LOW, index=True)
    status = Column(String(50), default="success")  # success, failed, error
    error_message = Column(Text, nullable=True)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Дополнительные поля для аналитики
    request_id = Column(String(255), nullable=True, index=True)  # Для трейсинга запросов
    duration_ms = Column(Integer, nullable=True)  # Время выполнения в миллисекундах
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action={self.action}, created_at={self.created_at})>"

class SecurityEvent(Base):
    """Модель для событий безопасности"""
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    
    # Пользователь (может быть null для анонимных событий)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    user = relationship("User", foreign_keys=[user_id])
    
    # Тип события
    event_type = Column(String(100), nullable=False, index=True)  # failed_login, suspicious_activity, etc.
    
    # Детали
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    
    # Уровень угрозы
    threat_level = Column(Enum(SeverityLevel), default=SeverityLevel.MEDIUM, index=True)
    
    # Статус обработки
    status = Column(String(50), default="new")  # new, investigating, resolved, false_positive
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_by_user = relationship("User", foreign_keys=[resolved_by])
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<SecurityEvent(id={self.id}, event_type={self.event_type}, threat_level={self.threat_level})>"
