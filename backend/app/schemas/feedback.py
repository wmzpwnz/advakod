"""
Schemas для системы обратной связи и модерации
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class FeedbackRating(str, Enum):
    """Типы оценок"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class FeedbackReason(str, Enum):
    """Причины негативной оценки"""
    NOT_ANSWERED = "not_answered"
    INACCURATE = "inaccurate"
    HARD_TO_UNDERSTAND = "hard_to_understand"
    OTHER = "other"


class ModerationStatus(str, Enum):
    """Статусы модерации"""
    PENDING = "pending"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"


class ModerationPriority(str, Enum):
    """Приоритеты модерации"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class QueueStatus(str, Enum):
    """Статусы очереди"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"


# ============= User Feedback Schemas =============

class FeedbackCreate(BaseModel):
    """Создание feedback от пользователя"""
    message_id: int = Field(..., description="ID сообщения")
    rating: FeedbackRating = Field(..., description="Оценка: positive/negative/neutral")
    reason: Optional[FeedbackReason] = Field(None, description="Причина (для negative)")
    comment: Optional[str] = Field(None, max_length=1000, description="Комментарий пользователя")

    @validator('reason')
    def validate_reason(cls, v, values):
        if values.get('rating') == FeedbackRating.NEGATIVE and not v:
            raise ValueError('Reason is required for negative feedback')
        return v


class FeedbackResponse(BaseModel):
    """Ответ с feedback"""
    id: int
    message_id: int
    user_id: int
    rating: str
    reason: Optional[str]
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============= Moderation Schemas =============

class ModerationReviewCreate(BaseModel):
    """Создание оценки модератора"""
    message_id: int = Field(..., description="ID сообщения")
    star_rating: int = Field(..., ge=1, le=10, description="Оценка от 1 до 10")
    problem_categories: List[str] = Field(default=[], description="Категории проблем")
    comment: str = Field(..., min_length=10, max_length=5000, description="Комментарий модератора")
    suggested_fix: Optional[str] = Field(None, max_length=10000, description="Предложенное исправление")
    priority: ModerationPriority = Field(default=ModerationPriority.MEDIUM, description="Приоритет")

    @validator('comment')
    def validate_comment(cls, v, values):
        if values.get('star_rating', 11) < 5 and len(v) < 20:
            raise ValueError('Detailed comment required for ratings below 5')
        return v


class ModerationReviewUpdate(BaseModel):
    """Обновление оценки модератора"""
    star_rating: Optional[int] = Field(None, ge=1, le=10)
    problem_categories: Optional[List[str]] = None
    comment: Optional[str] = Field(None, min_length=10, max_length=5000)
    suggested_fix: Optional[str] = Field(None, max_length=10000)
    status: Optional[ModerationStatus] = None
    priority: Optional[ModerationPriority] = None


class ModerationReviewResponse(BaseModel):
    """Ответ с оценкой модератора"""
    id: int
    message_id: int
    moderator_id: int
    star_rating: int
    problem_categories: List[str]
    comment: str
    suggested_fix: Optional[str]
    status: str
    priority: str
    original_confidence: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class MessageWithReview(BaseModel):
    """Сообщение с информацией для модерации"""
    message_id: int
    session_id: int
    user_question: str
    ai_response: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]]
    
    # Feedback пользователя
    user_feedback: Optional[FeedbackResponse]
    
    # Существующая оценка модератора
    existing_review: Optional[ModerationReviewResponse]
    
    # Информация из очереди
    queue_priority: str
    queue_reason: Optional[str]
    confidence_score: Optional[float]


# ============= Problem Category Schemas =============

class ProblemCategoryResponse(BaseModel):
    """Категория проблемы"""
    id: int
    name: str
    display_name: str
    description: Optional[str]
    severity: int
    icon: Optional[str]
    display_order: int
    is_active: bool

    class Config:
        from_attributes = True


# ============= Moderation Queue Schemas =============

class QueueFilters(BaseModel):
    """Фильтры для очереди модерации"""
    priority: Optional[ModerationPriority] = None
    status: Optional[QueueStatus] = None
    assigned_to_me: bool = False
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class QueueItemResponse(BaseModel):
    """Элемент очереди модерации"""
    id: int
    message_id: int
    priority: str
    reason: Optional[str]
    status: str
    confidence_score: Optional[float]
    created_at: datetime
    assigned_to: Optional[int]
    assigned_at: Optional[datetime]
    
    # Информация о сообщении
    message: MessageWithReview

    class Config:
        from_attributes = True


# ============= Statistics Schemas =============

class ModeratorStatsResponse(BaseModel):
    """Статистика модератора"""
    moderator_id: int
    total_reviews: int
    points: int
    badges: List[str]
    rank: str
    average_rating: Optional[float]
    category_stats: Dict[str, int]

    class Config:
        from_attributes = True


class ModerationAnalytics(BaseModel):
    """Аналитика модерации"""
    total_reviews: int
    average_rating: float
    rating_distribution: Dict[int, int]  # {1: 5, 2: 10, ...}
    top_problems: List[Dict[str, Any]]  # [{category: "outdated_data", count: 23}, ...]
    reviews_by_date: List[Dict[str, Any]]  # [{date: "2024-10-21", count: 15}, ...]
    moderator_leaderboard: List[Dict[str, Any]]  # [{moderator_id: 1, name: "...", points: 500}, ...]
    quality_trend: List[Dict[str, Any]]  # [{date: "2024-10-21", avg_rating: 7.5}, ...]


class AdminDashboard(BaseModel):
    """Дашборд для администратора"""
    analytics: ModerationAnalytics
    queue_stats: Dict[str, int]  # {pending: 50, in_review: 10, completed: 200}
    recent_reviews: List[ModerationReviewResponse]
    alerts: List[Dict[str, Any]]  # [{type: "low_quality", message: "...", severity: "high"}]


# ============= Training Dataset Schemas =============

class TrainingDatasetCreate(BaseModel):
    """Создание записи для обучения"""
    version: str
    question: str
    bad_answer: str
    good_answer: str
    review_id: Optional[int]
    metadata: Optional[Dict[str, Any]]


class TrainingDatasetResponse(BaseModel):
    """Запись датасета"""
    id: int
    version: str
    question: str
    bad_answer: str
    good_answer: str
    review_id: Optional[int]
    used_in_training: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetExportRequest(BaseModel):
    """Запрос на экспорт датасета"""
    version: str
    min_rating: int = Field(default=7, ge=1, le=10)
    include_categories: Optional[List[str]] = None
    exclude_categories: Optional[List[str]] = None
    format: str = Field(default="jsonl", pattern="^(jsonl|csv|json)$")


class TrainingJobRequest(BaseModel):
    """Запрос на запуск обучения"""
    dataset_version: str
    model_name: str = Field(default="saiga-mistral-7b")
    lora_config: Optional[Dict[str, Any]] = None
    canary_percentage: float = Field(default=0.1, ge=0.0, le=1.0)


class TrainingJobStatus(BaseModel):
    """Статус задачи обучения"""
    job_id: str
    status: str  # pending, running, completed, failed
    progress: float  # 0.0 - 1.0
    dataset_version: str
    model_name: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error: Optional[str]
    metrics: Optional[Dict[str, Any]]
