"""
Модели для системы обратной связи и модерации
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class ResponseFeedback(Base):
    """Обратная связь пользователей на ответы ИИ"""
    __tablename__ = "response_feedback"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey('chat_messages.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Оценка: positive, negative, neutral
    rating = Column(String(20), nullable=False, index=True)
    
    # Причина негативной оценки
    reason = Column(String(100), nullable=True)  # not_answered, inaccurate, hard_to_understand, other
    
    # Комментарий пользователя
    comment = Column(Text, nullable=True)
    
    # Метаданные (переименовано из metadata чтобы избежать конфликта с SQLAlchemy)
    feedback_metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Связи
    message = relationship("ChatMessage", back_populates="feedback")
    user = relationship("User")
    
    def __repr__(self):
        return f"<ResponseFeedback(id={self.id}, message_id={self.message_id}, rating={self.rating})>"


class ModerationReview(Base):
    """Оценки модераторов"""
    __tablename__ = "moderation_reviews"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey('chat_messages.id', ondelete='CASCADE'), nullable=False, index=True)
    moderator_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Оценка от 1 до 10 звезд
    star_rating = Column(Integer, nullable=False)
    
    # Категории проблем (JSON array)
    problem_categories = Column(JSON, nullable=True)
    
    # Комментарий модератора
    comment = Column(Text, nullable=False)
    
    # Предложенное исправление
    suggested_fix = Column(Text, nullable=True)
    
    # Статус: pending, reviewed, approved, rejected
    status = Column(String(20), nullable=False, default='reviewed', index=True)
    
    # Приоритет: high, medium, low
    priority = Column(String(20), nullable=False, default='medium', index=True)
    
    # Confidence score оригинального ответа
    original_confidence = Column(Float, nullable=True)
    
    # Метаданные (переименовано из metadata чтобы избежать конфликта с SQLAlchemy)
    review_metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    message = relationship("ChatMessage", back_populates="moderation_reviews")
    moderator = relationship("User", foreign_keys=[moderator_id])
    
    def __repr__(self):
        return f"<ModerationReview(id={self.id}, message_id={self.message_id}, rating={self.star_rating})>"


class ProblemCategory(Base):
    """Категории проблем в ответах"""
    __tablename__ = "problem_categories"

    id = Column(Integer, primary_key=True, index=True)
    
    # Системное имя
    name = Column(String(50), unique=True, nullable=False, index=True)
    
    # Отображаемое имя
    display_name = Column(String(100), nullable=False)
    
    # Описание
    description = Column(Text, nullable=True)
    
    # Серьезность (1-5)
    severity = Column(Integer, nullable=False, default=3)
    
    # Активна ли категория
    is_active = Column(Boolean, default=True, index=True)
    
    # Иконка/эмодзи
    icon = Column(String(10), nullable=True)
    
    # Порядок отображения
    display_order = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ProblemCategory(id={self.id}, name={self.name})>"


class TrainingDataset(Base):
    """Датасет для обучения модели"""
    __tablename__ = "training_datasets"

    id = Column(Integer, primary_key=True, index=True)
    
    # Версия датасета
    version = Column(String(20), nullable=False, index=True)
    
    # Вопрос пользователя
    question = Column(Text, nullable=False)
    
    # Плохой ответ (оригинальный)
    bad_answer = Column(Text, nullable=False)
    
    # Хороший ответ (исправленный)
    good_answer = Column(Text, nullable=False)
    
    # Ссылка на review
    review_id = Column(Integer, ForeignKey('moderation_reviews.id', ondelete='SET NULL'), nullable=True)
    
    # Метаданные (переименовано из metadata чтобы избежать конфликта с SQLAlchemy)
    dataset_metadata = Column(JSON, nullable=True)
    
    # Использован ли в обучении
    used_in_training = Column(Boolean, default=False, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Связи
    review = relationship("ModerationReview")
    
    def __repr__(self):
        return f"<TrainingDataset(id={self.id}, version={self.version})>"


class ModeratorStats(Base):
    """Статистика модераторов"""
    __tablename__ = "moderator_stats"

    id = Column(Integer, primary_key=True, index=True)
    moderator_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    
    # Количество оценок
    total_reviews = Column(Integer, default=0)
    
    # Баллы
    points = Column(Integer, default=0, index=True)
    
    # Бейджи (JSON array)
    badges = Column(JSON, default=list)
    
    # Ранг: novice, expert, master, legend
    rank = Column(String(20), default='novice', index=True)
    
    # Средняя оценка, которую ставит модератор
    average_rating = Column(Float, nullable=True)
    
    # Статистика по категориям (JSON)
    category_stats = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    moderator = relationship("User")
    
    def __repr__(self):
        return f"<ModeratorStats(moderator_id={self.moderator_id}, rank={self.rank}, points={self.points})>"


class ModerationQueue(Base):
    """Очередь модерации"""
    __tablename__ = "moderation_queue"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey('chat_messages.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    
    # Приоритет: high, medium, low
    priority = Column(String(20), nullable=False, default='medium', index=True)
    
    # Причина добавления в очередь
    reason = Column(String(100), nullable=True)  # low_confidence, user_complaint, random_sample
    
    # Назначен ли модератор
    assigned_to = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Статус: pending, in_review, completed
    status = Column(String(20), nullable=False, default='pending', index=True)
    
    # Confidence score
    confidence_score = Column(Float, nullable=True)
    
    # Метаданные (переименовано из metadata чтобы избежать конфликта с SQLAlchemy)
    queue_metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Связи
    message = relationship("ChatMessage")
    assigned_moderator = relationship("User", foreign_keys=[assigned_to])
    
    def __repr__(self):
        return f"<ModerationQueue(id={self.id}, message_id={self.message_id}, priority={self.priority})>"


# Предустановленные категории проблем
DEFAULT_PROBLEM_CATEGORIES = [
    {
        "name": "inaccurate_info",
        "display_name": "Неточная информация",
        "description": "Ответ содержит фактические ошибки или неточности",
        "severity": 5,
        "icon": "❌",
        "display_order": 1
    },
    {
        "name": "outdated_data",
        "display_name": "Устаревшие данные",
        "description": "Информация устарела и не соответствует текущему законодательству",
        "severity": 4,
        "icon": "📅",
        "display_order": 2
    },
    {
        "name": "wrong_article",
        "display_name": "Неправильная статья закона",
        "description": "Указана неверная статья или номер закона",
        "severity": 5,
        "icon": "📜",
        "display_order": 3
    },
    {
        "name": "poor_structure",
        "display_name": "Плохая структура ответа",
        "description": "Ответ плохо структурирован, сложно читать",
        "severity": 2,
        "icon": "🏗️",
        "display_order": 4
    },
    {
        "name": "missing_sources",
        "display_name": "Отсутствие ссылок на источники",
        "description": "Нет ссылок на законы, статьи или судебную практику",
        "severity": 3,
        "icon": "🔗",
        "display_order": 5
    },
    {
        "name": "hallucination",
        "display_name": "Галлюцинации",
        "description": "Выдуманные факты, несуществующие законы или статьи",
        "severity": 5,
        "icon": "🌀",
        "display_order": 6
    },
    {
        "name": "incomplete_answer",
        "display_name": "Неполный ответ",
        "description": "Ответ не раскрывает вопрос полностью",
        "severity": 3,
        "icon": "📝",
        "display_order": 7
    },
    {
        "name": "other",
        "display_name": "Другое",
        "description": "Другие проблемы, не входящие в категории выше",
        "severity": 2,
        "icon": "⚠️",
        "display_order": 8
    }
]
