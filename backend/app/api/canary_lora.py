"""
API для Canary-релизов и улучшенного LoRA
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import logging
from jose import JWTError, jwt

from ..core.database import get_db
from ..core.config import settings
from ..services.canary_service import canary_service, ModelVersion, CanaryMetrics
from ..services.enhanced_lora_service import enhanced_lora_service, LoRAMetrics
from ..models.user import User
from ..services.auth_service import AuthService, oauth2_scheme

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/canary-lora", tags=["canary-lora"])
auth_service = AuthService()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Получение текущего пользователя"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ===== CANARY-РЕЛИЗЫ =====

@router.post("/canary/deploy")
async def deploy_canary(
    model_name: str,
    version: str,
    canary_percentage: float = 10.0,
    rollback_threshold: float = 0.7,
    evaluation_period_hours: int = 24,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Развертывание Canary-версии модели"""
    try:
        # Проверяем права администратора
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Требуются права администратора"
            )
        
        model_id = await canary_service.deploy_canary(
            model_name=model_name,
            version=version,
            canary_percentage=canary_percentage,
            rollback_threshold=rollback_threshold,
            evaluation_period_hours=evaluation_period_hours
        )
        
        return {
            "success": True,
            "model_id": model_id,
            "message": f"Canary-версия {model_name} v{version} развернута ({canary_percentage}% трафика)"
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка развертывания Canary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка развертывания: {str(e)}"
        )

@router.post("/canary/promote/{model_id}")
async def promote_canary(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Продвижение Canary-версии в активную"""
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Требуются права администратора"
            )
        
        success = await canary_service.promote_canary(model_id)
        
        if success:
            return {
                "success": True,
                "message": f"Модель {model_id} успешно продвинута в активную"
            }
        else:
            return {
                "success": False,
                "message": f"Модель {model_id} не прошла критерии продвижения"
            }
        
    except Exception as e:
        logger.error(f"❌ Ошибка продвижения Canary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка продвижения: {str(e)}"
        )

@router.post("/canary/rollback/{model_id}")
async def rollback_canary(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Откат Canary-версии"""
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Требуются права администратора"
            )
        
        success = await canary_service.rollback_canary(model_id)
        
        return {
            "success": success,
            "message": f"Canary-версия {model_id} {'откачена' if success else 'не найдена'}"
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка отката Canary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка отката: {str(e)}"
        )

@router.get("/canary/status")
async def get_canary_status(
    current_user: User = Depends(get_current_user)
):
    """Получение статуса Canary-системы"""
    try:
        status = canary_service.get_status()
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса Canary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения статуса: {str(e)}"
        )

@router.post("/canary/metrics/{model_id}")
async def record_canary_metrics(
    model_id: str,
    success: bool,
    response_time: float,
    quality_score: Optional[float] = None,
    citation_accuracy: Optional[float] = None,
    hallucination_rate: Optional[float] = None,
    current_user: User = Depends(get_current_user)
):
    """Запись метрик для Canary-модели"""
    try:
        await canary_service.record_metrics(
            model_id=model_id,
            success=success,
            response_time=response_time,
            quality_score=quality_score,
            citation_accuracy=citation_accuracy,
            hallucination_rate=hallucination_rate
        )
        
        return {
            "success": True,
            "message": "Метрики записаны"
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка записи метрик: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка записи метрик: {str(e)}"
        )

# ===== LORA УЛУЧШЕНИЯ =====

@router.post("/lora/add-example")
async def add_training_example(
    query: str,
    response: str,
    sources: List[Dict[str, Any]],
    metrics: Dict[str, float],
    user_satisfaction: Optional[float] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Добавление примера для обучения LoRA с метриками"""
    try:
        # Создаем объект метрик
        lora_metrics = LoRAMetrics(
            citation_recall=metrics.get("citation_recall", 0.0),
            support_coverage=metrics.get("support_coverage", 0.0),
            hallucination_score=metrics.get("hallucination_score", 0.0),
            legal_consistency=metrics.get("legal_consistency", 0.0),
            overall_quality=metrics.get("overall_quality", 0.0),
            response_time=metrics.get("response_time", 0.0),
            user_satisfaction=user_satisfaction or metrics.get("user_satisfaction", 0.0),
            complexity_score=metrics.get("complexity_score", 0.0)
        )
        
        example_id = await enhanced_lora_service.add_training_example(
            query=query,
            response=response,
            sources=sources,
            metrics=lora_metrics,
            user_satisfaction=user_satisfaction
        )
        
        return {
            "success": True,
            "example_id": example_id,
            "message": "Пример добавлен для обучения"
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка добавления примера: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка добавления примера: {str(e)}"
        )

@router.get("/lora/training-batch")
async def get_training_batch(
    batch_size: int = 100,
    min_quality: float = 0.6,
    include_unapproved: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение батча примеров для обучения LoRA"""
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Требуются права администратора"
            )
        
        batch = await enhanced_lora_service.get_training_batch(
            batch_size=batch_size,
            min_quality=min_quality,
            include_unapproved=include_unapproved
        )
        
        # Конвертируем в JSON-сериализуемый формат
        batch_data = []
        for example in batch:
            batch_data.append({
                "id": example.id,
                "query": example.query,
                "response": example.response,
                "sources": example.sources,
                "metrics": {
                    "citation_recall": example.metrics.citation_recall,
                    "support_coverage": example.metrics.support_coverage,
                    "hallucination_score": example.metrics.hallucination_score,
                    "legal_consistency": example.metrics.legal_consistency,
                    "overall_quality": example.metrics.overall_quality,
                    "user_satisfaction": example.metrics.user_satisfaction,
                    "complexity_score": example.metrics.complexity_score
                },
                "is_approved": example.is_approved,
                "priority": example.priority,
                "created_at": example.created_at.isoformat() if example.created_at else None
            })
        
        return {
            "success": True,
            "batch": batch_data,
            "count": len(batch_data)
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения батча: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения батча: {str(e)}"
        )

@router.get("/lora/priority-examples")
async def get_priority_examples(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение приоритетных примеров для обучения"""
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Требуются права администратора"
            )
        
        examples = await enhanced_lora_service.get_priority_examples(limit=limit)
        
        # Конвертируем в JSON-сериализуемый формат
        examples_data = []
        for example in examples:
            examples_data.append({
                "id": example.id,
                "query": example.query,
                "response": example.response,
                "priority": example.priority,
                "is_approved": example.is_approved,
                "metrics": {
                    "overall_quality": example.metrics.overall_quality,
                    "citation_recall": example.metrics.citation_recall,
                    "user_satisfaction": example.metrics.user_satisfaction
                }
            })
        
        return {
            "success": True,
            "examples": examples_data,
            "count": len(examples_data)
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения приоритетных примеров: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения примеров: {str(e)}"
        )

@router.get("/lora/quality-statistics")
async def get_quality_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение статистики качества примеров"""
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Требуются права администратора"
            )
        
        stats = await enhanced_lora_service.get_quality_statistics()
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения статистики: {str(e)}"
        )

@router.post("/lora/update-thresholds")
async def update_quality_thresholds(
    thresholds: Dict[str, float],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление пороговых значений качества"""
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Требуются права администратора"
            )
        
        await enhanced_lora_service.update_quality_thresholds(thresholds)
        
        return {
            "success": True,
            "message": "Пороговые значения обновлены"
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка обновления порогов: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обновления порогов: {str(e)}"
        )

@router.get("/lora/export-data")
async def export_training_data(
    format: str = "json",
    include_metrics: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Экспорт данных для обучения"""
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Требуются права администратора"
            )
        
        data = await enhanced_lora_service.export_training_data(
            format=format,
            include_metrics=include_metrics
        )
        
        return {
            "success": True,
            "data": data,
            "format": format
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка экспорта данных: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка экспорта: {str(e)}"
        )

@router.get("/lora/status")
async def get_lora_status(
    current_user: User = Depends(get_current_user)
):
    """Получение статуса LoRA сервиса"""
    try:
        status = enhanced_lora_service.get_status()
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса LoRA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения статуса: {str(e)}"
        )
