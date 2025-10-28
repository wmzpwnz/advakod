"""
API для управления LoRA обучением
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.database import get_db
from ..models.training_data import TrainingData, ModelVersion, TrainingJob, DataCollectionLog
from ..models.user import User
from ..schemas.lora_training import (
    TrainingDataResponse, TrainingDataCreate, TrainingDataUpdate,
    ModelVersionResponse, ModelVersionCreate,
    TrainingJobResponse, TrainingJobCreate,
    DataCollectionRequest, DataCollectionResponse,
    BatchApprovalRequest, BatchApprovalResponse,
    QualityEvaluationRequest, QualityEvaluationResponse,
    TrainingStatsResponse, ModelTestRequest, ModelTestResponse,
    TrainingHyperparameters
)
from ..services.data_collection_service import DataCollectionService
from ..services.ai_categorization_service import AICategorizationService
from ..services.lora_training_service import LoRATrainingService
from ..core.admin_security import get_secure_admin
from ..core.optimized_lora_config import OptimizedLoRAConfig
from ..middleware.ml_rate_limit import training_rate_limit

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/lora", tags=["lora-training"])


# ==================== СБОР ДАННЫХ ====================

@router.post("/data/collect", response_model=DataCollectionResponse)
async def collect_training_data(
    request: DataCollectionRequest,
    background_tasks: BackgroundTasks,
    current_admin: User = Depends(get_secure_admin),
    db: Session = Depends(get_db)
):
    """Сбор данных для обучения из чатов"""
    try:
        collection_service = DataCollectionService(db)
        
        # Запускаем сбор в фоне
        result = collection_service.collect_chat_data(
            limit=request.limit,
            days_back=request.days_back,
            collection_type=request.collection_type
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return DataCollectionResponse(**result)
        
    except Exception as e:
        logger.error(f"Ошибка сбора данных: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/stats", response_model=TrainingStatsResponse)
async def get_training_stats(
    days: int = Query(7, ge=1, le=365),
    current_admin: User = Depends(get_secure_admin),
    db: Session = Depends(get_db)
):
    """Получить статистику обучения"""
    try:
        collection_service = DataCollectionService(db)
        stats = collection_service.get_collection_stats(days)
        
        # Добавляем информацию об активных задачах
        active_jobs = db.query(TrainingJob).filter(
            TrainingJob.status.in_(["pending", "running"])
        ).count()
        stats["active_training_jobs"] = active_jobs
        
        return TrainingStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== УПРАВЛЕНИЕ ДАННЫМИ ====================

@router.get("/data", response_model=List[TrainingDataResponse])
async def get_training_data(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    complexity: Optional[str] = Query(None),
    approved_only: bool = Query(False),
    current_admin: User = Depends(get_secure_admin),
    db: Session = Depends(get_db)
):
    """Получить данные для обучения"""
    try:
        query = db.query(TrainingData)
        
        if complexity:
            query = query.filter(TrainingData.complexity == complexity)
        
        if approved_only:
            query = query.filter(TrainingData.is_approved == True)
        
        data = query.order_by(TrainingData.created_at.desc()).offset(offset).limit(limit).all()
        
        return [TrainingDataResponse.from_orm(item) for item in data]
        
    except Exception as e:
        logger.error(f"Ошибка получения данных: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/{data_id}", response_model=TrainingDataResponse)
async def get_training_data_by_id(
    data_id: int,
    current_admin: User = Depends(get_secure_admin),
    db: Session = Depends(get_db)
):
    """Получить конкретные данные обучения"""
    try:
        data = db.query(TrainingData).filter(TrainingData.id == data_id).first()
        
        if not data:
            raise HTTPException(status_code=404, detail="Данные не найдены")
        
        return TrainingDataResponse.from_orm(data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения данных: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/data/{data_id}", response_model=TrainingDataResponse)
async def update_training_data(
    data_id: int,
    update_data: TrainingDataUpdate,
    current_admin: User = Depends(get_secure_admin),
    db: Session = Depends(get_db)
):
    """Обновить данные обучения"""
    try:
        data = db.query(TrainingData).filter(TrainingData.id == data_id).first()
        
        if not data:
            raise HTTPException(status_code=404, detail="Данные не найдены")
        
        # Обновляем поля
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(data, field, value)
        
        data.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(data)
        
        return TrainingDataResponse.from_orm(data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обновления данных: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data/{data_id}/approve")
async def approve_training_data(
    data_id: int,
    current_admin: User = Depends(get_secure_admin),
    db: Session = Depends(get_db)
):
    """Одобрить данные для обучения"""
    try:
        collection_service = DataCollectionService(db)
        success = collection_service.approve_training_data(data_id, current_admin.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Данные не найдены")
        
        return {"message": "Данные одобрены для обучения"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка одобрения данных: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data/{data_id}/reject")
async def reject_training_data(
    data_id: int,
    reason: str = "Не соответствует требованиям",
    current_admin: User = Depends(get_secure_admin),
    db: Session = Depends(get_db)
):
    """Отклонить данные для обучения"""
    try:
        collection_service = DataCollectionService(db)
        success = collection_service.reject_training_data(data_id, reason)
        
        if not success:
            raise HTTPException(status_code=404, detail="Данные не найдены")
        
        return {"message": "Данные отклонены"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка отклонения данных: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ПАКЕТНЫЕ ОПЕРАЦИИ ====================

@router.post("/data/batch-approve", response_model=BatchApprovalResponse)
async def batch_approve_data(
    request: BatchApprovalRequest,
    current_admin: User = Depends(get_secure_admin),
    db: Session = Depends(get_db)
):
    """Пакетное одобрение/отклонение данных"""
    try:
        collection_service = DataCollectionService(db)
        
        processed = 0
        approved = 0
        rejected = 0
        errors = 0
        
        for data_id in request.data_ids:
            try:
                if request.approve:
                    success = collection_service.approve_training_data(data_id, current_admin.id)
                    if success:
                        approved += 1
                    else:
                        errors += 1
                else:
                    success = collection_service.reject_training_data(data_id, "Пакетное отклонение")
                    if success:
                        rejected += 1
                    else:
                        errors += 1
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Ошибка обработки данных {data_id}: {e}")
                errors += 1
        
        return BatchApprovalResponse(
            processed=processed,
            approved=approved,
            rejected=rejected,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Ошибка пакетной обработки: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data/evaluate-quality", response_model=QualityEvaluationResponse)
async def evaluate_quality(
    request: QualityEvaluationRequest,
    background_tasks: BackgroundTasks,
    current_admin: User = Depends(get_secure_admin),
    db: Session = Depends(get_db)
):
    """Оценка качества данных"""
    try:
        categorization_service = AICategorizationService(db)
        
        # Запускаем оценку в фоне
        result = categorization_service.process_batch_categorization(request.data_ids)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return QualityEvaluationResponse(**result)
        
    except Exception as e:
        logger.error(f"Ошибка оценки качества: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== УПРАВЛЕНИЕ ОБУЧЕНИЕМ ====================

@router.post("/training/start", response_model=TrainingJobResponse)
async def start_training(
    job_data: TrainingJobCreate,
    hyperparameters: TrainingHyperparameters,
    background_tasks: BackgroundTasks,
    current_admin: User = Depends(get_secure_admin),
    db: Session = Depends(get_db)
):
    """Запуск обучения LoRA"""
    try:
        # Создаем задачу обучения
        training_job = TrainingJob(
            job_name=job_data.job_name,
            hyperparameters=hyperparameters.dict(),
            created_by=current_admin.id
        )
        db.add(training_job)
        db.commit()
        db.refresh(training_job)
        
        # Запускаем обучение в фоне
        training_service = LoRATrainingService(db)
        background_tasks.add_task(
            training_service.run_training,
            training_job.id
        )
        
        return TrainingJobResponse.from_orm(training_job)
        
    except Exception as e:
        logger.error(f"Ошибка запуска обучения: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/training/jobs", response_model=List[TrainingJobResponse])
async def get_training_jobs(
    limit: int = Query(20, ge=1, le=100),
    current_admin: User = Depends(get_secure_admin),
    db: Session = Depends(get_db)
):
    """Получить список задач обучения"""
    try:
        jobs = db.query(TrainingJob).order_by(
            TrainingJob.created_at.desc()
        ).limit(limit).all()
        
        return [TrainingJobResponse.from_orm(job) for job in jobs]
        
    except Exception as e:
        logger.error(f"Ошибка получения задач: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/training/jobs/{job_id}", response_model=TrainingJobResponse)
async def get_training_job(
    job_id: int,
    current_admin: User = Depends(get_secure_admin),
    db: Session = Depends(get_db)
):
    """Получить конкретную задачу обучения"""
    try:
        job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        
        return TrainingJobResponse.from_orm(job)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения задачи: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/training/jobs/{job_id}/cancel")
async def cancel_training_job(
    job_id: int,
    current_admin: User = Depends(get_secure_admin),
    db: Session = Depends(get_db)
):
    """Отменить задачу обучения"""
    try:
        job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        
        if job.status not in ["pending", "running"]:
            raise HTTPException(status_code=400, detail="Задача не может быть отменена")
        
        job.status = "cancelled"
        job.completed_at = datetime.utcnow()
        db.commit()
        
        return {"message": "Задача отменена"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка отмены задачи: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== УПРАВЛЕНИЕ МОДЕЛЯМИ ====================

@router.get("/models", response_model=List[ModelVersionResponse])
async def get_model_versions(
    current_admin: User = Depends(get_secure_admin),
    db: Session = Depends(get_db)
):
    """Получить список версий моделей"""
    try:
        models = db.query(ModelVersion).order_by(
            ModelVersion.created_at.desc()
        ).all()
        
        return [ModelVersionResponse.from_orm(model) for model in models]
        
    except Exception as e:
        logger.error(f"Ошибка получения моделей: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models", response_model=ModelVersionResponse)
async def create_model_version(
    model_data: ModelVersionCreate,
    current_admin: User = Depends(get_secure_admin),
    db: Session = Depends(get_db)
):
    """Создать новую версию модели"""
    try:
        # Проверяем, что версия уникальна
        existing = db.query(ModelVersion).filter(
            ModelVersion.version == model_data.version
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Версия уже существует")
        
        model = ModelVersion(
            version=model_data.version,
            base_model=model_data.base_model,
            lora_config=model_data.lora_config,
            created_by=current_admin.id
        )
        
        db.add(model)
        db.commit()
        db.refresh(model)
        
        return ModelVersionResponse.from_orm(model)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка создания модели: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/{model_id}/activate")
async def activate_model(
    model_id: int,
    current_admin: User = Depends(get_secure_admin),
    db: Session = Depends(get_db)
):
    """Активировать модель"""
    try:
        # Деактивируем все модели
        db.query(ModelVersion).update({"is_active": False})
        
        # Активируем выбранную
        model = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
        
        if not model:
            raise HTTPException(status_code=404, detail="Модель не найдена")
        
        model.is_active = True
        db.commit()
        
        return {"message": f"Модель {model.version} активирована"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка активации модели: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ТЕСТИРОВАНИЕ МОДЕЛИ ====================

@router.post("/models/test", response_model=ModelTestResponse)
async def test_model(
    test_request: ModelTestRequest,
    current_admin: User = Depends(get_secure_admin),
    db: Session = Depends(get_db)
):
    """Тестирование модели"""
    try:
        # Здесь будет логика тестирования модели
        # Пока возвращаем заглушку
        
        test_results = []
        for question in test_request.test_questions:
            test_results.append({
                "question": question,
                "answer": f"Тестовый ответ на: {question}",
                "quality_score": 4.0,
                "response_time": 0.5
            })
        
        return ModelTestResponse(
            model_version=test_request.model_version or "latest",
            test_results=test_results,
            average_quality=4.0,
            test_duration=1.0
        )
        
    except Exception as e:
        logger.error(f"Ошибка тестирования модели: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ОПТИМИЗИРОВАННЫЕ КОНФИГУРАЦИИ ====================

@router.get("/config/recommended")
async def get_recommended_lora_config(
    model_size: str = Query("medium", pattern="^(small|medium|large)$"),
    task_type: str = Query("legal_qa"),
    dataset_size: int = Query(1000, ge=100, le=100000),
    current_admin: User = Depends(get_secure_admin),
    db: Session = Depends(get_db)
):
    """Получить рекомендуемую оптимизированную конфигурацию LoRA"""
    try:
        recommendation = LoRATrainingService.get_recommended_config(
            model_size=model_size,
            task_type=task_type,
            dataset_size=dataset_size
        )
        
        return recommendation
        
    except Exception as e:
        logger.error(f"Ошибка генерации рекомендации: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/tasks")
async def get_available_legal_tasks(
    current_admin: User = Depends(get_secure_admin)
):
    """Получить список доступных юридических задач для LoRA"""
    try:
        tasks = OptimizedLoRAConfig.get_available_legal_tasks()
        
        return {
            "legal_tasks": tasks,
            "model_sizes": {
                "small": "Маленькие модели (<1B параметров)",
                "medium": "Средние модели (1B-7B параметров)",
                "large": "Большие модели (>7B параметров)"
            },
            "complexity_levels": {
                "simple": "Простые задачи (классификация, простые QA)",
                "moderate": "Умеренные задачи (генерация средней сложности)",
                "complex": "Сложные задачи (сложная юридическая генерация)"
            }
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения списка задач: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/validate")
async def validate_lora_config(
    config: Dict[str, Any],
    current_admin: User = Depends(get_secure_admin)
):
    """Валидация конфигурации LoRA"""
    try:
        warnings = OptimizedLoRAConfig.validate_config(config)
        
        return {
            "valid": len(warnings) == 0,
            "warnings": warnings,
            "recommendations": [
                "Используйте /config/recommended для получения оптимальных параметров",
                "Учитывайте размер модели и сложность задачи",
                "Мониторьте метрики во время обучения"
            ] if warnings else []
        }
        
    except Exception as e:
        logger.error(f"Ошибка валидации: {e}")
        raise HTTPException(status_code=500, detail=str(e))
