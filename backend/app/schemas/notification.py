from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# Simple enums for notification system
class NotificationType(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Base schemas
class NotificationBase(BaseModel):
    title: str = Field(..., max_length=255)
    message: str
    type: str = "info"
    priority: str = "medium"
    channels: Optional[List[str]] = ["web"]
    data: Optional[Dict[str, Any]] = None


class NotificationCreate(NotificationBase):
    user_id: Optional[int] = None


class NotificationUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    message: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[str] = None
    read: Optional[bool] = None


class NotificationResponse(NotificationBase):
    id: int
    user_id: Optional[int] = None
    read: bool = False
    read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Template schemas
class NotificationTemplateBase(BaseModel):
    name: str = Field(..., max_length=100)
    type: str
    title_template: str = Field(..., max_length=200)
    message_template: str
    default_channels: Optional[List[str]] = ["web"]
    default_priority: str = "medium"


class NotificationTemplateCreate(NotificationTemplateBase):
    pass


class NotificationTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    type: Optional[str] = None
    title_template: Optional[str] = Field(None, max_length=200)
    message_template: Optional[str] = None
    default_channels: Optional[List[str]] = None
    default_priority: Optional[str] = None
    active: Optional[bool] = None


class NotificationTemplateResponse(NotificationTemplateBase):
    id: int
    active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# History schemas
class NotificationHistoryResponse(BaseModel):
    id: int
    notification_id: int
    channel: str
    status: str
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Request schemas
class SendNotificationRequest(BaseModel):
    title: str = Field(..., max_length=255)
    message: str
    type: str = "info"
    priority: str = "medium"
    channels: List[str] = ["web"]
    user_ids: Optional[List[int]] = None
    data: Optional[Dict[str, Any]] = None


class NotificationFilters(BaseModel):
    type: Optional[str] = None
    priority: Optional[str] = None
    read: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class NotificationCenterResponse(BaseModel):
    notifications: List[NotificationResponse]
    unread_count: int
    total_count: int
    has_more: bool = False


class MarkAsReadRequest(BaseModel):
    notification_ids: List[int]