from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from ..models.audit_log import ActionType, SeverityLevel

class AuditLogBase(BaseModel):
    """Базовая схема для аудит лога"""
    action: ActionType
    resource: Optional[str] = None
    resource_id: Optional[str] = None
    description: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    severity: SeverityLevel = SeverityLevel.LOW
    status: str = "success"
    error_message: Optional[str] = None

class AuditLogCreate(AuditLogBase):
    """Схема для создания аудит лога"""
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    duration_ms: Optional[int] = None

class AuditLogResponse(AuditLogBase):
    """Схема для ответа с аудит логом"""
    id: int
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    duration_ms: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class SecurityEventBase(BaseModel):
    """Базовая схема для события безопасности"""
    event_type: str
    description: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    threat_level: SeverityLevel = SeverityLevel.MEDIUM

class SecurityEventCreate(SecurityEventBase):
    """Схема для создания события безопасности"""
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class SecurityEventResponse(SecurityEventBase):
    """Схема для ответа с событием безопасности"""
    id: int
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str = "new"
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class AuditStatisticsResponse(BaseModel):
    """Схема для статистики аудит логов"""
    total_actions: int
    action_breakdown: Dict[str, int]
    status_breakdown: Dict[str, int]
    severity_breakdown: Dict[str, int]
    period_days: int

class AuditLogFilter(BaseModel):
    """Схема для фильтрации аудит логов"""
    action: Optional[ActionType] = None
    severity: Optional[SeverityLevel] = None
    user_id: Optional[int] = None
    resource: Optional[str] = None
    status: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)

class AuditDashboardResponse(BaseModel):
    """Схема для дашборда аудит логов"""
    week_statistics: AuditStatisticsResponse
    month_statistics: AuditStatisticsResponse
    recent_security_events: List[SecurityEventResponse]
    recent_audit_logs: List[AuditLogResponse]
    user: Dict[str, Any]

class SecurityEventResolution(BaseModel):
    """Схема для разрешения события безопасности"""
    resolution: str = Field(..., description="Описание разрешения")
    status: str = Field("resolved", description="Новый статус события")

class AuditLogExportRequest(BaseModel):
    """Схема для запроса экспорта аудит логов"""
    format: str = Field("json", pattern="^(json|csv)$")
    user_id: Optional[int] = None
    days: int = Field(30, ge=1, le=365)
    include_details: bool = Field(True, description="Включать детали в экспорт")

class AuditLogSummary(BaseModel):
    """Схема для краткой сводки аудит лога"""
    id: int
    action: ActionType
    description: Optional[str] = None
    severity: SeverityLevel
    status: str
    created_at: datetime
    user_id: Optional[int] = None

class SecurityEventSummary(BaseModel):
    """Схема для краткой сводки события безопасности"""
    id: int
    event_type: str
    threat_level: SeverityLevel
    status: str
    created_at: datetime
    user_id: Optional[int] = None

class AuditMetrics(BaseModel):
    """Схема для метрик аудит логов"""
    total_logs: int
    success_rate: float
    error_rate: float
    high_severity_count: int
    unique_users: int
    most_common_actions: List[Dict[str, Any]]
    security_events_count: int
    unresolved_security_events: int
