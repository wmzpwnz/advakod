"""
Схемы для админ панели
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    legal_form: Optional[str] = None
    inn: Optional[str] = None
    ogrn: Optional[str] = None
    is_active: Optional[bool] = None
    is_premium: Optional[bool] = None
    subscription_type: Optional[str] = None

class UserStats(BaseModel):
    """Статистика пользователей"""
    total: int
    active: int
    premium: int
    admins: int
    new_last_30d: int

class ChatStats(BaseModel):
    """Статистика чатов"""
    total_sessions: int
    total_messages: int

class SystemStatus(BaseModel):
    """Статус системы"""
    rag_status: Dict[str, Any]
    vector_store_status: Dict[str, Any]
    timestamp: str

class AdminDashboard(BaseModel):
    """Дашборд администратора"""
    users: UserStats
    chats: ChatStats
    system: SystemStatus

class DocumentInfo(BaseModel):
    """Информация о документе"""
    id: str
    content: str
    metadata: Dict[str, Any]
    length: int

class DocumentList(BaseModel):
    """Список документов"""
    documents: List[DocumentInfo]
    total: int
    skip: int
    limit: int

class DocumentSearchResult(BaseModel):
    """Результат поиска документов"""
    id: str
    content: str
    metadata: Dict[str, Any]
    similarity: float
    distance: float

class DocumentSearchResponse(BaseModel):
    """Ответ на поиск документов"""
    query: str
    documents: List[DocumentSearchResult]
    total_found: int

class AuditLogEntry(BaseModel):
    """Запись лога аудита"""
    id: int
    user_id: Optional[int]
    action: str
    resource: Optional[str]
    resource_id: Optional[str]
    description: Optional[str]
    severity: Optional[str]
    ip_address: Optional[str]
    created_at: str
    details: Optional[Dict[str, Any]]

class AuditLogsResponse(BaseModel):
    """Ответ с логами аудита"""
    logs: List[AuditLogEntry]
    total: int
    skip: int
    limit: int

class UserAnalytics(BaseModel):
    """Аналитика пользователей"""
    period: Dict[str, str]
    daily_registrations: List[Dict[str, Any]]
    subscription_distribution: List[Dict[str, Any]]

class FileUploadResponse(BaseModel):
    """Ответ на загрузку файла"""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
