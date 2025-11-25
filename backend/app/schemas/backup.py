"""
Схемы для системы резервного копирования
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class BackupStatus(str, Enum):
    """Статусы резервного копирования"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BackupType(str, Enum):
    """Типы резервного копирования"""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    AUTOMATIC = "automatic"


class RestoreStatus(str, Enum):
    """Статусы восстановления"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BackupComponent(str, Enum):
    """Компоненты для резервного копирования"""
    MAIN_DB = "main_db"
    VECTOR_DB = "vector_db"
    CONFIG = "config"
    UPLOADS = "uploads"
    LOGS = "logs"


# Базовые схемы для создания
class BackupCreate(BaseModel):
    """Схема для создания резервной копии"""
    name: str = Field(..., min_length=1, max_length=255, description="Название резервной копии")
    description: Optional[str] = Field(None, max_length=1000, description="Описание")
    components: List[BackupComponent] = Field(default=[BackupComponent.MAIN_DB, BackupComponent.VECTOR_DB], description="Компоненты для резервного копирования")
    tags: Optional[List[str]] = Field(default=[], description="Теги для категоризации")
    retention_days: int = Field(default=30, ge=1, le=365, description="Количество дней для хранения")
    compression_enabled: bool = Field(default=True, description="Включить сжатие")
    encryption_enabled: bool = Field(default=False, description="Включить шифрование")

    @validator('tags')
    def validate_tags(cls, v):
        if v and len(v) > 10:
            raise ValueError('Максимум 10 тегов')
        return v


class BackupScheduleCreate(BaseModel):
    """Схема для создания расписания резервного копирования"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    cron_expression: str = Field(..., description="Cron выражение для расписания")
    timezone: str = Field(default="UTC", description="Часовой пояс")
    backup_components: List[BackupComponent] = Field(default=[BackupComponent.MAIN_DB, BackupComponent.VECTOR_DB])
    retention_days: int = Field(default=30, ge=1, le=365)
    compression_enabled: bool = Field(default=True)
    encryption_enabled: bool = Field(default=False)
    notify_on_success: bool = Field(default=False)
    notify_on_failure: bool = Field(default=True)
    notification_channels: Optional[List[str]] = Field(default=["email"])
    notification_recipients: Optional[List[str]] = Field(default=[])

    @validator('cron_expression')
    def validate_cron(cls, v):
        # Простая валидация cron выражения
        parts = v.split()
        if len(parts) != 5:
            raise ValueError('Cron выражение должно содержать 5 частей')
        return v


class RestoreCreate(BaseModel):
    """Схема для создания задачи восстановления"""
    backup_record_id: int = Field(..., description="ID резервной копии для восстановления")
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    components_to_restore: List[BackupComponent] = Field(..., description="Компоненты для восстановления")
    restore_options: Optional[Dict[str, Any]] = Field(default={}, description="Дополнительные опции восстановления")


# Схемы для обновления
class BackupScheduleUpdate(BaseModel):
    """Схема для обновления расписания"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    enabled: Optional[bool] = None
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    backup_components: Optional[List[BackupComponent]] = None
    retention_days: Optional[int] = Field(None, ge=1, le=365)
    compression_enabled: Optional[bool] = None
    encryption_enabled: Optional[bool] = None
    notify_on_success: Optional[bool] = None
    notify_on_failure: Optional[bool] = None
    notification_channels: Optional[List[str]] = None
    notification_recipients: Optional[List[str]] = None


# Схемы для ответов
class BackupRecordResponse(BaseModel):
    """Схема ответа для записи резервной копии"""
    id: int
    name: str
    backup_type: BackupType
    status: BackupStatus
    backup_path: Optional[str]
    total_size: Optional[int]
    components: Optional[Dict[str, Any]]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: Optional[int]
    description: Optional[str]
    tags: Optional[List[str]]
    success: bool
    error_message: Optional[str]
    warnings: Optional[List[str]]
    retention_days: int
    compression_enabled: bool
    encryption_enabled: bool
    duration_seconds: Optional[float]
    files_count: Optional[int]

    class Config:
        from_attributes = True


class BackupScheduleResponse(BaseModel):
    """Схема ответа для расписания резервного копирования"""
    id: int
    name: str
    description: Optional[str]
    enabled: bool
    cron_expression: str
    timezone: str
    backup_components: List[str]
    retention_days: int
    compression_enabled: bool
    encryption_enabled: bool
    notify_on_success: bool
    notify_on_failure: bool
    notification_channels: Optional[List[str]]
    notification_recipients: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]
    last_run_at: Optional[datetime]
    last_run_status: Optional[str]
    next_run_at: Optional[datetime]
    total_runs: int
    successful_runs: int
    failed_runs: int

    class Config:
        from_attributes = True


class RestoreRecordResponse(BaseModel):
    """Схема ответа для записи восстановления"""
    id: int
    backup_record_id: int
    name: str
    status: RestoreStatus
    components_to_restore: List[str]
    restore_options: Optional[Dict[str, Any]]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: int
    description: Optional[str]
    success: bool
    error_message: Optional[str]
    warnings: Optional[List[str]]
    restored_components: Optional[List[str]]
    duration_seconds: Optional[float]
    files_restored: Optional[int]

    class Config:
        from_attributes = True


class BackupIntegrityCheckResponse(BaseModel):
    """Схема ответа для проверки целостности"""
    id: int
    backup_record_id: int
    status: str
    check_type: str
    checked_at: datetime
    check_duration_seconds: Optional[float]
    passed: bool
    error_message: Optional[str]
    warnings: Optional[List[str]]
    details: Optional[Dict[str, Any]]
    files_checked: Optional[int]
    size_verified: Optional[int]
    checksum_verified: bool

    class Config:
        from_attributes = True


# Схемы для статистики и дашборда
class BackupStats(BaseModel):
    """Статистика резервного копирования"""
    total_backups: int
    successful_backups: int
    failed_backups: int
    total_size: int  # в байтах
    average_backup_time: Optional[float]  # в секундах
    last_backup_date: Optional[datetime]
    next_scheduled_backup: Optional[datetime]
    active_schedules: int
    storage_usage_percent: Optional[float]


class BackupSystemStatus(BaseModel):
    """Статус системы резервного копирования"""
    status: str  # "healthy", "warning", "error"
    backup_service_running: bool
    scheduler_running: bool
    storage_available: bool
    last_successful_backup: Optional[datetime]
    pending_backups: int
    failed_backups_last_24h: int
    warnings: List[str]
    recommendations: List[str]


class BackupListResponse(BaseModel):
    """Схема для списка резервных копий"""
    backups: List[BackupRecordResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_prev: bool


class BackupPreview(BaseModel):
    """Предварительный просмотр содержимого резервной копии"""
    backup_id: int
    manifest: Dict[str, Any]
    components: Dict[str, Any]
    file_structure: Dict[str, Any]
    estimated_restore_time: Optional[float]
    compatibility_check: Dict[str, Any]


# Схемы для операций
class BackupOperation(BaseModel):
    """Операция с резервной копией"""
    operation_id: str
    operation_type: str  # "backup", "restore", "integrity_check"
    status: str
    progress: float  # 0.0 - 1.0
    message: str
    started_at: datetime
    estimated_completion: Optional[datetime]


class BackupValidationResult(BaseModel):
    """Результат валидации резервной копии"""
    backup_id: int
    is_valid: bool
    validation_errors: List[str]
    validation_warnings: List[str]
    components_status: Dict[str, str]
    file_integrity: Dict[str, bool]
    size_verification: Dict[str, bool]
    recommendations: List[str]