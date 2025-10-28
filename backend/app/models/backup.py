"""
Модели для системы резервного копирования
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from enum import Enum

from ..core.database import Base


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


class BackupRecord(Base):
    """Запись о резервном копировании"""
    __tablename__ = "backup_records"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    backup_type = Column(String(50), nullable=False, default=BackupType.MANUAL)
    status = Column(String(50), nullable=False, default=BackupStatus.PENDING)
    
    # Пути и размеры
    backup_path = Column(String(500), nullable=True)
    total_size = Column(Integer, nullable=True)  # в байтах
    
    # Компоненты бэкапа
    components = Column(JSON, nullable=True)  # {"main_db": {...}, "vector_db": {...}, "config": {...}}
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Метаданные
    created_by = Column(Integer, nullable=True)  # ID пользователя
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # ["daily", "before_update", etc.]
    
    # Результаты и ошибки
    success = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    warnings = Column(JSON, nullable=True)  # Список предупреждений
    
    # Настройки
    retention_days = Column(Integer, default=30)  # Сколько дней хранить
    compression_enabled = Column(Boolean, default=True)
    encryption_enabled = Column(Boolean, default=False)
    
    # Статистика
    duration_seconds = Column(Float, nullable=True)
    files_count = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<BackupRecord(id={self.id}, name='{self.name}', status='{self.status}')>"


class BackupSchedule(Base):
    """Расписание автоматического резервного копирования"""
    __tablename__ = "backup_schedules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Настройки расписания
    enabled = Column(Boolean, default=True)
    cron_expression = Column(String(100), nullable=False)  # "0 2 * * *" для ежедневно в 2:00
    timezone = Column(String(50), default="UTC")
    
    # Настройки бэкапа
    backup_components = Column(JSON, nullable=False)  # ["main_db", "vector_db", "config", "uploads"]
    retention_days = Column(Integer, default=30)
    compression_enabled = Column(Boolean, default=True)
    encryption_enabled = Column(Boolean, default=False)
    
    # Уведомления
    notify_on_success = Column(Boolean, default=False)
    notify_on_failure = Column(Boolean, default=True)
    notification_channels = Column(JSON, nullable=True)  # ["email", "slack", "telegram"]
    notification_recipients = Column(JSON, nullable=True)  # Список получателей
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, nullable=True)
    
    # Статистика
    last_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(String(50), nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)

    def __repr__(self):
        return f"<BackupSchedule(id={self.id}, name='{self.name}', enabled={self.enabled})>"


class RestoreRecord(Base):
    """Запись о восстановлении данных"""
    __tablename__ = "restore_records"

    id = Column(Integer, primary_key=True, index=True)
    backup_record_id = Column(Integer, nullable=False, index=True)
    
    # Основная информация
    name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default=RestoreStatus.PENDING)
    
    # Компоненты для восстановления
    components_to_restore = Column(JSON, nullable=False)  # ["main_db", "vector_db", "config"]
    restore_options = Column(JSON, nullable=True)  # Дополнительные опции
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Метаданные
    created_by = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    
    # Результаты
    success = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    warnings = Column(JSON, nullable=True)
    restored_components = Column(JSON, nullable=True)  # Что было восстановлено
    
    # Статистика
    duration_seconds = Column(Float, nullable=True)
    files_restored = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<RestoreRecord(id={self.id}, name='{self.name}', status='{self.status}')>"


class BackupIntegrityCheck(Base):
    """Проверка целостности резервных копий"""
    __tablename__ = "backup_integrity_checks"

    id = Column(Integer, primary_key=True, index=True)
    backup_record_id = Column(Integer, nullable=False, index=True)
    
    # Результаты проверки
    status = Column(String(50), nullable=False)  # "passed", "failed", "warning"
    check_type = Column(String(100), nullable=False)  # "file_integrity", "database_integrity", "size_check"
    
    # Детали проверки
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    check_duration_seconds = Column(Float, nullable=True)
    
    # Результаты
    passed = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    warnings = Column(JSON, nullable=True)
    details = Column(JSON, nullable=True)  # Подробная информация о проверке
    
    # Метрики
    files_checked = Column(Integer, nullable=True)
    size_verified = Column(Integer, nullable=True)  # в байтах
    checksum_verified = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<BackupIntegrityCheck(id={self.id}, backup_id={self.backup_record_id}, status='{self.status}')>"