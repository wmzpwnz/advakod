"""
Модели данных для LoRA обучения
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class TrainingData(Base):
    """Данные для обучения LoRA"""
    __tablename__ = "training_data"
    
    id = Column(Integer, primary_key=True, index=True)
    instruction = Column(Text, nullable=False)  # Вопрос пользователя
    input = Column(Text, nullable=True)         # Контекст или дополнительные данные
    output = Column(Text, nullable=False)       # Ответ ИИ
    source = Column(String(50), nullable=False) # chat, manual, generated, rag
    quality_score = Column(Float, nullable=True) # 1-5 звезд (ИИ оценка)
    complexity = Column(String(20), nullable=True) # simple, medium, complex
    is_approved = Column(Boolean, default=False) # Одобрено модератором
    is_used_for_training = Column(Boolean, default=False) # Использовано в обучении
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True) # Кто одобрил
    approved_at = Column(DateTime(timezone=True), nullable=True) # Когда одобрили
    meta_data = Column(JSON, nullable=True)      # Дополнительные данные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    approver = relationship("User", foreign_keys=[approved_by])


class ModelVersion(Base):
    """Версии моделей LoRA"""
    __tablename__ = "model_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(20), nullable=False, unique=True) # v1.0.0
    base_model = Column(String(100), nullable=False) # Saiga Mistral 7B
    lora_config = Column(JSON, nullable=True)        # Конфигурация LoRA
    training_data_count = Column(Integer, default=0) # Количество данных
    performance_metrics = Column(JSON, nullable=True) # Метрики качества
    is_active = Column(Boolean, default=False)       # Активная версия
    model_path = Column(String(500), nullable=True)  # Путь к модели
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    creator = relationship("User", foreign_keys=[created_by])


class TrainingJob(Base):
    """Задачи обучения LoRA"""
    __tablename__ = "training_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String(100), nullable=False)
    status = Column(String(20), default="pending") # pending, running, completed, failed, cancelled
    training_data_count = Column(Integer, default=0)
    hyperparameters = Column(JSON, nullable=True) # Параметры обучения
    progress = Column(Float, default=0.0) # 0-100%
    current_epoch = Column(Integer, default=0)
    total_epochs = Column(Integer, default=0)
    loss = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    creator = relationship("User", foreign_keys=[created_by])


class DataCollectionLog(Base):
    """Лог сбора данных"""
    __tablename__ = "data_collection_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    collection_type = Column(String(50), nullable=False) # auto, manual, scheduled
    source = Column(String(50), nullable=False) # chats, documents, manual
    total_found = Column(Integer, default=0) # Найдено всего
    total_processed = Column(Integer, default=0) # Обработано
    total_approved = Column(Integer, default=0) # Одобрено
    total_rejected = Column(Integer, default=0) # Отклонено
    duration_seconds = Column(Integer, nullable=True) # Время выполнения
    error_message = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    creator = relationship("User", foreign_keys=[created_by])


class QualityEvaluation(Base):
    """Оценка качества данных"""
    __tablename__ = "quality_evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    training_data_id = Column(Integer, ForeignKey("training_data.id"), nullable=False)
    evaluation_type = Column(String(50), nullable=False) # auto, manual, hybrid
    score = Column(Float, nullable=False) # 1-5
    criteria = Column(JSON, nullable=True) # Критерии оценки
    evaluator_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Кто оценил
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    training_data = relationship("TrainingData")
    evaluator = relationship("User", foreign_keys=[evaluator_id])
