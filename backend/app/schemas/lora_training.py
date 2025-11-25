"""
Схемы данных для LoRA обучения
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class ComplexityLevel(str, Enum):
    """Уровни сложности"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class TrainingStatus(str, Enum):
    """Статусы обучения"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TrainingDataBase(BaseModel):
    """Базовая схема данных обучения"""
    instruction: str = Field(..., description="Вопрос пользователя")
    input: Optional[str] = Field(None, description="Контекст или дополнительные данные")
    output: str = Field(..., description="Ответ ИИ")
    source: str = Field(..., description="Источник данных")


class TrainingDataCreate(TrainingDataBase):
    """Схема для создания данных обучения"""
    pass


class TrainingDataResponse(TrainingDataBase):
    """Схема ответа для данных обучения"""
    id: int
    quality_score: Optional[float] = None
    complexity: Optional[ComplexityLevel] = None
    is_approved: bool = False
    is_used_for_training: bool = False
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TrainingDataUpdate(BaseModel):
    """Схема для обновления данных обучения"""
    quality_score: Optional[float] = Field(None, ge=1.0, le=5.0)
    complexity: Optional[ComplexityLevel] = None
    is_approved: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class ModelVersionBase(BaseModel):
    """Базовая схема версии модели"""
    version: str = Field(..., description="Версия модели (например, v1.0.0)")
    base_model: str = Field(..., description="Базовая модель")
    lora_config: Optional[Dict[str, Any]] = None


class ModelVersionCreate(ModelVersionBase):
    """Схема для создания версии модели"""
    pass


class ModelVersionResponse(ModelVersionBase):
    """Схема ответа для версии модели"""
    id: int
    training_data_count: int = 0
    performance_metrics: Optional[Dict[str, Any]] = None
    is_active: bool = False
    model_path: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TrainingJobBase(BaseModel):
    """Базовая схема задачи обучения"""
    job_name: str = Field(..., description="Название задачи")
    hyperparameters: Optional[Dict[str, Any]] = None


class TrainingJobCreate(TrainingJobBase):
    """Схема для создания задачи обучения"""
    pass


class TrainingJobResponse(TrainingJobBase):
    """Схема ответа для задачи обучения"""
    id: int
    status: TrainingStatus
    training_data_count: int = 0
    progress: float = Field(0.0, ge=0.0, le=100.0)
    current_epoch: int = 0
    total_epochs: int = 0
    loss: Optional[float] = None
    accuracy: Optional[float] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DataCollectionRequest(BaseModel):
    """Запрос на сбор данных"""
    limit: int = Field(1000, ge=1, le=10000, description="Максимальное количество диалогов")
    days_back: int = Field(30, ge=1, le=365, description="Количество дней назад для сбора")
    collection_type: str = Field("auto", description="Тип сбора данных")


class DataCollectionResponse(BaseModel):
    """Ответ на сбор данных"""
    total_found: int
    total_processed: int
    total_approved: int
    total_rejected: int
    collection_id: Optional[int] = None
    error: Optional[str] = None


class BatchApprovalRequest(BaseModel):
    """Запрос на пакетное одобрение"""
    data_ids: List[int] = Field(..., description="ID данных для одобрения")
    approve: bool = Field(True, description="Одобрить или отклонить")


class BatchApprovalResponse(BaseModel):
    """Ответ на пакетное одобрение"""
    processed: int
    approved: int
    rejected: int
    errors: int


class QualityEvaluationRequest(BaseModel):
    """Запрос на оценку качества"""
    data_ids: List[int] = Field(..., description="ID данных для оценки")
    force_re_evaluate: bool = Field(False, description="Принудительная переоценка")


class QualityEvaluationResponse(BaseModel):
    """Ответ на оценку качества"""
    processed: int
    simple: int
    medium: int
    complex: int
    errors: int


class TrainingStatsResponse(BaseModel):
    """Статистика обучения"""
    total_data: int
    approved_data: int
    pending_data: int
    simple_data: int
    medium_data: int
    complex_data: int
    approval_rate: float
    last_collection: Optional[datetime] = None
    active_training_jobs: int = 0


class ModelTestRequest(BaseModel):
    """Запрос на тестирование модели"""
    test_questions: List[str] = Field(..., description="Тестовые вопросы")
    model_version: Optional[str] = Field(None, description="Версия модели для тестирования")


class ModelTestResponse(BaseModel):
    """Ответ на тестирование модели"""
    model_version: str
    test_results: List[Dict[str, Any]]
    average_quality: float
    test_duration: float


class LoRAConfig(BaseModel):
    """Конфигурация LoRA"""
    r: int = Field(16, ge=1, le=64, description="Rank")
    lora_alpha: int = Field(32, ge=1, le=128, description="LoRA alpha")
    lora_dropout: float = Field(0.1, ge=0.0, le=0.5, description="LoRA dropout")
    target_modules: List[str] = Field(["q_proj", "v_proj"], description="Target modules")
    bias: str = Field("none", description="Bias type")
    task_type: str = Field("CAUSAL_LM", description="Task type")


class TrainingHyperparameters(BaseModel):
    """Гиперпараметры обучения"""
    learning_rate: float = Field(2e-4, ge=1e-6, le=1e-2, description="Learning rate")
    num_train_epochs: int = Field(3, ge=1, le=10, description="Number of epochs")
    per_device_train_batch_size: int = Field(1, ge=1, le=8, description="Batch size")
    gradient_accumulation_steps: int = Field(4, ge=1, le=16, description="Gradient accumulation steps")
    warmup_steps: int = Field(100, ge=0, le=1000, description="Warmup steps")
    logging_steps: int = Field(10, ge=1, le=100, description="Logging steps")
    save_steps: int = Field(500, ge=1, le=1000, description="Save steps")
    evaluation_strategy: str = Field("steps", description="Evaluation strategy")
    eval_steps: int = Field(500, ge=1, le=1000, description="Evaluation steps")
    lora_config: LoRAConfig = Field(default_factory=LoRAConfig, description="LoRA configuration")
