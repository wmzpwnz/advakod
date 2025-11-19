"""
Модели для продвинутой аналитики и отчетности
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Dict, Any, List, Optional

from .user import Base


class Dashboard(Base):
    """Пользовательский дашборд"""
    __tablename__ = "dashboards"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    layout = Column(JSON)  # Конфигурация layout для react-grid-layout
    is_public = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # user = relationship("User", back_populates="dashboards")  # Временно отключено
    widgets = relationship("DashboardWidget", back_populates="dashboard", cascade="all, delete-orphan")


class DashboardWidget(Base):
    """Виджет дашборда"""
    __tablename__ = "dashboard_widgets"
    
    id = Column(Integer, primary_key=True, index=True)
    dashboard_id = Column(Integer, ForeignKey("dashboards.id"), nullable=False)
    widget_type = Column(String(100), nullable=False)  # metric, chart, table, custom
    title = Column(String(255), nullable=False)
    config = Column(JSON)  # Конфигурация виджета
    position = Column(JSON)  # Позиция и размер в grid layout
    data_source = Column(String(255))  # Источник данных
    refresh_interval = Column(Integer, default=300)  # Интервал обновления в секундах
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    dashboard = relationship("Dashboard", back_populates="widgets")


class CustomMetric(Base):
    """Пользовательская метрика"""
    __tablename__ = "custom_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    formula = Column(Text, nullable=False)  # SQL-подобная формула для вычисления
    unit = Column(String(50))  # Единица измерения
    format_type = Column(String(50), default="number")  # number, percentage, currency, time
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False)
    category = Column(String(100))  # Категория метрики
    tags = Column(JSON)  # Теги для поиска
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    alerts = relationship("MetricAlert", back_populates="metric", cascade="all, delete-orphan")


class MetricAlert(Base):
    """Алерт на основе метрики"""
    __tablename__ = "metric_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("custom_metrics.id"), nullable=False)
    name = Column(String(255), nullable=False)
    condition = Column(String(50), nullable=False)  # gt, lt, eq, gte, lte
    threshold = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    notification_channels = Column(JSON)  # Каналы уведомлений
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    last_triggered = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    metric = relationship("CustomMetric", back_populates="alerts")
    user = relationship("User")


class CohortAnalysis(Base):
    """Когортный анализ"""
    __tablename__ = "cohort_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    cohort_type = Column(String(50), nullable=False)  # registration, first_purchase, etc.
    period_type = Column(String(50), nullable=False)  # daily, weekly, monthly
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    data = Column(JSON)  # Данные когорт
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")


class UserSegment(Base):
    """Сегмент пользователей"""
    __tablename__ = "user_segments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    criteria = Column(JSON, nullable=False)  # Критерии сегментации
    user_count = Column(Integer, default=0)
    is_dynamic = Column(Boolean, default=True)  # Динамический или статический сегмент
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")


class MLPrediction(Base):
    """ML прогноз"""
    __tablename__ = "ml_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(255), nullable=False)
    prediction_type = Column(String(100), nullable=False)  # ltv, churn, conversion, etc.
    target_user_id = Column(Integer, ForeignKey("users.id"))
    prediction_value = Column(Float)
    confidence_score = Column(Float)
    features = Column(JSON)  # Признаки, использованные для прогноза
    model_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # Когда прогноз устаревает
    
    # Relationships
    target_user = relationship("User")


class ReportTemplate(Base):
    """Шаблон отчета"""
    __tablename__ = "report_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    template_type = Column(String(100), nullable=False)  # dashboard, export, email
    config = Column(JSON, nullable=False)  # Конфигурация шаблона
    schedule = Column(JSON)  # Расписание автоматической генерации
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    executions = relationship("ReportExecution", back_populates="template", cascade="all, delete-orphan")


class ReportExecution(Base):
    """Выполнение отчета"""
    __tablename__ = "report_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("report_templates.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    result_data = Column(JSON)  # Результат выполнения
    error_message = Column(Text)
    execution_time = Column(Float)  # Время выполнения в секундах
    file_path = Column(String(500))  # Путь к сгенерированному файлу
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    template = relationship("ReportTemplate", back_populates="executions")