"""
Pydantic схемы для системы уведомлений админ-панели
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class AdminNotificationBase(BaseModel):
    """Базовая схема уведомления"""
    type: str = Field(..., max_length=50)
    title: str = Field(..., max_length=200)
    message: str
    data: Optional[Dict[str, Any]] = None
    priority: str = Field("normal", regex="^(low|normal|high|critical)$")
    channels: Optional[List[str]] = ["websocket"]


class AdminNotificationCreate(AdminNotificationBase):
    """Схема для создания уведомления"""
    user_id: int


class AdminNotificationResponse(AdminNotificationBase):
    """Схема ответа уведомления"""
    id: int
    user_id: int
    read: bool = False
    read_at: Optional[datetime] = None
    delivery_status: Optional[Dict[str, str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SystemAlertCreate(BaseModel):
    """Схема для создания системного алерта"""
    title: str = Field(..., max_length=200)
    message: str
    severity: str = Field("info", regex="^(info|warning|error|critical)$")
    data: Optional[Dict[str, Any]] = None
    target_roles: Optional[List[str]] = None


class NotificationStatsResponse(BaseModel):
    """Схема статистики уведомлений"""
    unread_count: int
    total_count: int


class NotificationTemplateBase(BaseModel):
    """Базовая схема шаблона уведомления"""
    name: str = Field(..., max_length=100)
    type: str = Field(..., max_length=50)
    title_template: str = Field(..., max_length=200)
    message_template: str
    email_template: Optional[str] = None
    slack_template: Optional[str] = None
    default_channels: Optional[List[str]] = ["websocket"]
    default_priority: str = Field("normal", regex="^(low|normal|high|critical)$")
    trigger_conditions: Optional[Dict[str, Any]] = None
    active: bool = True


class NotificationTemplateCreate(NotificationTemplateBase):
    """Схема для создания шаблона"""
    pass


class NotificationTemplateResponse(NotificationTemplateBase):
    """Схема ответа шаблона"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationHistoryResponse(BaseModel):
    """Схема истории доставки уведомлений"""
    id: int
    notification_id: int
    channel: str
    status: str
    delivery_details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WebSocketConnectionStats(BaseModel):
    """Статистика WebSocket соединений"""
    total_connections: int
    active_admins: int
    connections_by_role: Dict[str, int]
    active_channels: int
    last_activity: Dict[int, float]  # user_id -> seconds since last activity


class AdminWebSocketMessage(BaseModel):
    """Схема WebSocket сообщения"""
    type: str
    payload: Dict[str, Any]
    timestamp: Optional[float] = None
    user_id: Optional[int] = None


class AdminWebSocketSubscription(BaseModel):
    """Схема подписки на канал"""
    channel: str
    options: Optional[Dict[str, Any]] = None


class AdminWebSocketResponse(BaseModel):
    """Схема ответа WebSocket"""
    type: str
    payload: Dict[str, Any]
    timestamp: float
    sender_id: Optional[int] = None