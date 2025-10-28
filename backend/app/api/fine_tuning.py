from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time
from datetime import datetime

from ..core.database import get_db
from ..models.user import User
from ..core.fine_tuning import (
    get_fine_tuning_manager,
    LegalDataProcessor,
    TrainingData,
    ModelMetrics,
    FineTuningJob
)
from ..services.auth_service import AuthService
from ..core.database import get_db
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
auth_service = AuthService()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return auth_service.get_current_user(token, db)

router = APIRouter()

class TrainingDataCreate(BaseModel):
    prompt: str = Field(..., description="Промпт для обучения")
    completion: str = Field(..., description="Ожидаемый ответ")
    category: str = Field(..., description="Категория права")
    confidence: float = Field(default=1.0, description="Уверенность в данных")
    source: str = Field(default="manual", description="Источник данных")

class Hyperparameters(BaseModel):
    n_epochs: int = Field(default=3, description="Количество эпох")
    batch_size: int = Field(default=1, description="Размер батча")
    learning_rate_multiplier: float = Field(default=0.1, description="Множитель learning rate")
    prompt_loss_weight: float = Field(default=0.01, description="Вес потерь промпта")

class FineTuningJobCreate(BaseModel):
    model_name: str = Field(..., description="Название модели")
    training_data: List[TrainingDataCreate] = Field(..., description="Данные для обучения")
    hyperparameters: Optional[Hyperparameters] = Field(None, description="Гиперпараметры")

class FineTuningJobResponse(BaseModel):
    job_id: str
    model_name: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    metrics: Optional[Dict[str, float]]
    error_message: Optional[str]

class ModelEvaluationRequest(BaseModel):
    model_name: str = Field(..., description="Название модели для оценки")
    test_data: List[TrainingDataCreate] = Field(..., description="Тестовые данные")

class LegalDocumentProcess(BaseModel):
    documents: List[Dict[str, Any]] = Field(..., description="Юридические документы")
    conversations: List[Dict[str, Any]] = Field(default=[], description="Диалоги")

@router.post("/fine-tuning/jobs", response_model=FineTuningJobResponse)
async def create_fine_tuning_job(
    job_data: FineTuningJobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание задачи fine-tuning"""
    try:
        # Проверяем права пользователя (только админы могут создавать fine-tuning)
        if not current_user.is_premium:
            raise HTTPException(
                status_code=403, 
                detail="Fine-tuning доступен только для премиум пользователей"
            )
        
        # Конвертируем данные
        training_data = [
            TrainingData(
                prompt=data.prompt,
                completion=data.completion,
                category=data.category,
                confidence=data.confidence,
                source=data.source
            )
            for data in job_data.training_data
        ]
        
        # Создаем задачу fine-tuning
        fine_tuning_manager = get_fine_tuning_manager()
        job = await fine_tuning_manager.create_fine_tuning_job(
            model_name=job_data.model_name,
            training_data=training_data,
            hyperparameters=job_data.hyperparameters.dict() if job_data.hyperparameters else None
        )
        
        return FineTuningJobResponse(
            job_id=job.job_id,
            model_name=job.model_name,
            status=job.status,
            created_at=job.created_at,
            completed_at=job.completed_at,
            metrics=job.metrics.__dict__ if job.metrics else None,
            error_message=job.error_message
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fine-tuning/jobs", response_model=List[FineTuningJobResponse])
async def list_fine_tuning_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Список задач fine-tuning"""
    try:
        fine_tuning_manager = get_fine_tuning_manager()
        jobs = await fine_tuning_manager.list_jobs()
        
        return [
            FineTuningJobResponse(
                job_id=job.job_id,
                model_name=job.model_name,
                status=job.status,
                created_at=job.created_at,
                completed_at=job.completed_at,
                metrics=job.metrics.__dict__ if job.metrics else None,
                error_message=job.error_message
            )
            for job in jobs
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fine-tuning/jobs/{job_id}", response_model=FineTuningJobResponse)
async def get_fine_tuning_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение задачи fine-tuning по ID"""
    try:
        fine_tuning_manager = get_fine_tuning_manager()
        job = await fine_tuning_manager.get_job_status(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Fine-tuning job not found")
        
        return FineTuningJobResponse(
            job_id=job.job_id,
            model_name=job.model_name,
            status=job.status,
            created_at=job.created_at,
            completed_at=job.completed_at,
            metrics=job.metrics.__dict__ if job.metrics else None,
            error_message=job.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/fine-tuning/jobs/{job_id}")
async def cancel_fine_tuning_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Отмена задачи fine-tuning"""
    try:
        fine_tuning_manager = get_fine_tuning_manager()
        success = await fine_tuning_manager.cancel_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Fine-tuning job not found or cannot be cancelled")
        
        return {"message": "Fine-tuning job cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fine-tuning/process-legal-data")
async def process_legal_documents(
    data: LegalDocumentProcess,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обработка юридических документов для создания обучающих данных"""
    try:
        processor = LegalDataProcessor()
        
        # Обрабатываем документы
        document_data = processor.process_legal_documents(data.documents)
        
        # Обрабатываем диалоги
        conversation_data = processor.create_conversation_data(data.conversations)
        
        # Объединяем данные
        all_training_data = document_data + conversation_data
        
        return {
            "total_examples": len(all_training_data),
            "document_examples": len(document_data),
            "conversation_examples": len(conversation_data),
            "categories": list(set(data.category for data in all_training_data)),
            "training_data": [
                {
                    "prompt": data.prompt,
                    "completion": data.completion,
                    "category": data.category,
                    "confidence": data.confidence,
                    "source": data.source
                }
                for data in all_training_data[:10]  # Показываем первые 10 примеров
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fine-tuning/evaluate")
async def evaluate_model(
    evaluation_data: ModelEvaluationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Оценка качества модели"""
    try:
        if not current_user.is_premium:
            raise HTTPException(
                status_code=403, 
                detail="Оценка моделей доступна только для премиум пользователей"
            )
        
        # Конвертируем тестовые данные
        test_data = [
            TrainingData(
                prompt=data.prompt,
                completion=data.completion,
                category=data.category,
                confidence=data.confidence,
                source=data.source
            )
            for data in evaluation_data.test_data
        ]
        
        fine_tuning_manager = get_fine_tuning_manager()
        metrics = await fine_tuning_manager.evaluate_model(
            evaluation_data.model_name,
            test_data
        )
        
        return {
            "model_name": evaluation_data.model_name,
            "metrics": {
                "accuracy": metrics.accuracy,
                "precision": metrics.precision,
                "recall": metrics.recall,
                "f1_score": metrics.f1_score,
                "loss": metrics.loss,
                "perplexity": metrics.perplexity
            },
            "evaluation_date": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fine-tuning/deploy/{job_id}")
async def deploy_model(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Развертывание обученной модели"""
    try:
        if not current_user.is_premium:
            raise HTTPException(
                status_code=403, 
                detail="Развертывание моделей доступно только для премиум пользователей"
            )
        
        fine_tuning_manager = get_fine_tuning_manager()
        success = await fine_tuning_manager.deploy_model(job_id)
        
        if not success:
            raise HTTPException(
                status_code=400, 
                detail="Model deployment failed. Check if the job is completed."
            )
        
        return {"message": "Model deployed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fine-tuning/categories")
async def get_legal_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение списка юридических категорий"""
    try:
        processor = LegalDataProcessor()
        
        categories = []
        for category, keywords in processor.legal_categories.items():
            categories.append({
                "name": category,
                "display_name": category.replace("_", " ").title(),
                "keywords": keywords,
                "description": f"Вопросы по {category.replace('_', ' ')}"
            })
        
        return {"categories": categories}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fine-tuning/stats")
async def get_fine_tuning_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение статистики fine-tuning"""
    try:
        fine_tuning_manager = get_fine_tuning_manager()
        jobs = await fine_tuning_manager.list_jobs()
        
        stats = {
            "total_jobs": len(jobs),
            "completed_jobs": len([j for j in jobs if j.status == "completed"]),
            "running_jobs": len([j for j in jobs if j.status == "running"]),
            "failed_jobs": len([j for j in jobs if j.status == "failed"]),
            "cancelled_jobs": len([j for j in jobs if j.status == "cancelled"]),
            "average_accuracy": 0.0,
            "best_model": None
        }
        
        # Вычисляем среднюю точность
        completed_jobs = [j for j in jobs if j.status == "completed" and j.metrics]
        if completed_jobs:
            stats["average_accuracy"] = sum(j.metrics.accuracy for j in completed_jobs) / len(completed_jobs)
            
            # Находим лучшую модель
            best_job = max(completed_jobs, key=lambda j: j.metrics.accuracy)
            stats["best_model"] = {
                "job_id": best_job.job_id,
                "model_name": best_job.model_name,
                "accuracy": best_job.metrics.accuracy
            }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
