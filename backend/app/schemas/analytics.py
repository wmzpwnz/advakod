"""
Схемы для продвинутой аналитики и отчетности
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum


class WidgetType(str, Enum):
    """Типы виджетов"""
    METRIC = "metric"
    CHART = "chart"
    TABLE = "table"
    CUSTOM = "custom"


class ChartType(str, Enum):
    """Типы графиков"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    FUNNEL = "funnel"


class MetricFormat(str, Enum):
    """Форматы метрик"""
    NUMBER = "number"
    PERCENTAGE = "percentage"
    CURRENCY = "currency"
    TIME = "time"


class AlertCondition(str, Enum):
    """Условия алертов"""
    GT = "gt"  # больше
    LT = "lt"  # меньше
    EQ = "eq"  # равно
    GTE = "gte"  # больше или равно
    LTE = "lte"  # меньше или равно


# Dashboard Schemas
class DashboardWidgetPosition(BaseModel):
    """Позиция виджета в grid layout"""
    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    w: int = Field(..., ge=1, le=12)
    h: int = Field(..., ge=1, le=12)
    minW: Optional[int] = Field(1, ge=1)
    minH: Optional[int] = Field(1, ge=1)
    maxW: Optional[int] = Field(12, le=12)
    maxH: Optional[int] = Field(12, le=12)


class DashboardWidgetConfig(BaseModel):
    """Конфигурация виджета"""
    chart_type: Optional[ChartType] = None
    data_source: str
    filters: Optional[Dict[str, Any]] = {}
    aggregation: Optional[str] = None
    time_range: Optional[str] = "24h"
    refresh_interval: Optional[int] = 300
    color_scheme: Optional[str] = "default"
    show_legend: Optional[bool] = True
    show_grid: Optional[bool] = True
    custom_options: Optional[Dict[str, Any]] = {}


class DashboardWidgetCreate(BaseModel):
    """Создание виджета дашборда"""
    widget_type: WidgetType
    title: str = Field(..., min_length=1, max_length=255)
    config: DashboardWidgetConfig
    position: DashboardWidgetPosition
    data_source: str
    refresh_interval: Optional[int] = Field(300, ge=30, le=3600)


class DashboardWidgetUpdate(BaseModel):
    """Обновление виджета дашборда"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    config: Optional[DashboardWidgetConfig] = None
    position: Optional[DashboardWidgetPosition] = None
    refresh_interval: Optional[int] = Field(None, ge=30, le=3600)
    is_active: Optional[bool] = None


class DashboardWidget(BaseModel):
    """Виджет дашборда"""
    id: int
    dashboard_id: int
    widget_type: WidgetType
    title: str
    config: Dict[str, Any]
    position: Dict[str, Any]
    data_source: str
    refresh_interval: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DashboardCreate(BaseModel):
    """Создание дашборда"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    layout: Optional[Dict[str, Any]] = {}
    is_public: Optional[bool] = False
    is_default: Optional[bool] = False


class DashboardUpdate(BaseModel):
    """Обновление дашборда"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    layout: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    is_default: Optional[bool] = None


class Dashboard(BaseModel):
    """Дашборд"""
    id: int
    name: str
    description: Optional[str]
    user_id: int
    layout: Dict[str, Any]
    is_public: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime
    widgets: List[DashboardWidget] = []

    class Config:
        from_attributes = True


# Custom Metrics Schemas
class CustomMetricCreate(BaseModel):
    """Создание пользовательской метрики"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    formula: str = Field(..., min_length=1)
    unit: Optional[str] = Field(None, max_length=50)
    format_type: MetricFormat = MetricFormat.NUMBER
    is_public: Optional[bool] = False
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = []

    @validator('formula')
    def validate_formula(cls, v):
        # Базовая валидация формулы
        if not v.strip():
            raise ValueError('Formula cannot be empty')
        return v


class CustomMetricUpdate(BaseModel):
    """Обновление пользовательской метрики"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    formula: Optional[str] = Field(None, min_length=1)
    unit: Optional[str] = Field(None, max_length=50)
    format_type: Optional[MetricFormat] = None
    is_public: Optional[bool] = None
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None


class CustomMetric(BaseModel):
    """Пользовательская метрика"""
    id: int
    name: str
    description: Optional[str]
    formula: str
    unit: Optional[str]
    format_type: str
    user_id: int
    is_public: bool
    category: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Metric Alert Schemas
class MetricAlertCreate(BaseModel):
    """Создание алерта метрики"""
    metric_id: int
    name: str = Field(..., min_length=1, max_length=255)
    condition: AlertCondition
    threshold: float
    notification_channels: List[str] = []
    is_active: Optional[bool] = True


class MetricAlertUpdate(BaseModel):
    """Обновление алерта метрики"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    condition: Optional[AlertCondition] = None
    threshold: Optional[float] = None
    notification_channels: Optional[List[str]] = None
    is_active: Optional[bool] = None


class MetricAlert(BaseModel):
    """Алерт метрики"""
    id: int
    metric_id: int
    name: str
    condition: str
    threshold: float
    is_active: bool
    notification_channels: List[str]
    user_id: int
    last_triggered: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Cohort Analysis Schemas
class CohortAnalysisCreate(BaseModel):
    """Создание когортного анализа"""
    name: str = Field(..., min_length=1, max_length=255)
    cohort_type: str = Field(..., min_length=1, max_length=50)
    period_type: str = Field(..., min_length=1, max_length=50)
    start_date: datetime
    end_date: datetime

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class CohortAnalysis(BaseModel):
    """Когортный анализ"""
    id: int
    name: str
    cohort_type: str
    period_type: str
    start_date: datetime
    end_date: datetime
    data: Dict[str, Any]
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# User Segment Schemas
class UserSegmentCriteria(BaseModel):
    """Критерии сегментации пользователей"""
    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, in, not_in, contains
    value: Union[str, int, float, List[Union[str, int, float]]]


class UserSegmentCreate(BaseModel):
    """Создание сегмента пользователей"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    criteria: List[UserSegmentCriteria]
    is_dynamic: Optional[bool] = True


class UserSegmentUpdate(BaseModel):
    """Обновление сегмента пользователей"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    criteria: Optional[List[UserSegmentCriteria]] = None
    is_dynamic: Optional[bool] = None


class UserSegment(BaseModel):
    """Сегмент пользователей"""
    id: int
    name: str
    description: Optional[str]
    criteria: List[Dict[str, Any]]
    user_count: int
    is_dynamic: bool
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ML Prediction Schemas
class MLPrediction(BaseModel):
    """ML прогноз"""
    id: int
    model_name: str
    prediction_type: str
    target_user_id: Optional[int]
    prediction_value: Optional[float]
    confidence_score: Optional[float]
    features: Dict[str, Any]
    model_version: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


# Report Template Schemas
class ReportTemplateCreate(BaseModel):
    """Создание шаблона отчета"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    template_type: str = Field(..., min_length=1, max_length=100)
    config: Dict[str, Any]
    schedule: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = True


class ReportTemplateUpdate(BaseModel):
    """Обновление шаблона отчета"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    schedule: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ReportTemplate(BaseModel):
    """Шаблон отчета"""
    id: int
    name: str
    description: Optional[str]
    template_type: str
    config: Dict[str, Any]
    schedule: Optional[Dict[str, Any]]
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReportExecution(BaseModel):
    """Выполнение отчета"""
    id: int
    template_id: int
    status: str
    result_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    execution_time: Optional[float]
    file_path: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# Data Source Schemas
class DataSourceInfo(BaseModel):
    """Информация об источнике данных"""
    id: str
    name: str
    description: str
    fields: List[Dict[str, Any]]
    sample_data: Optional[Dict[str, Any]] = None


class WidgetData(BaseModel):
    """Данные виджета"""
    labels: List[str] = []
    datasets: List[Dict[str, Any]] = []
    metadata: Optional[Dict[str, Any]] = {}


# Dashboard Builder Response Schemas
class DashboardBuilderResponse(BaseModel):
    """Ответ конструктора дашбордов"""
    dashboards: List[Dashboard]
    data_sources: List[DataSourceInfo]
    widget_templates: List[Dict[str, Any]]
    total: int