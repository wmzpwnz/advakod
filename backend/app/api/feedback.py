"""
API для обратной связи пользователей
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from ..core.database import get_db
from ..models.user import User
from ..services.auth_service import AuthService
from ..services.feedback_service import feedback_service
from ..schemas.feedback import (
    FeedbackCreate,
    FeedbackResponse
)

router = APIRouter()
auth_service = AuthService()


@router.post("/rate", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback_data: FeedbackCreate,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Отправка feedback на ответ ИИ
    
    - **message_id**: ID сообщения для оценки
    - **rating**: positive/negative/neutral
    - **reason**: причина (обязательна для negative)
    - **comment**: комментарий (опционально)
    """
    try:
        feedback = await feedback_service.submit_feedback(
            db=db,
            user_id=current_user.id,
            feedback_data=feedback_data
        )
        
        return feedback
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )


@router.get("/message/{message_id}", response_model=Optional[FeedbackResponse])
async def get_message_feedback(
    message_id: int,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получение feedback для конкретного сообщения
    """
    feedback = await feedback_service.get_message_feedback(
        db=db,
        message_id=message_id
    )
    
    return feedback


@router.get("/my-history", response_model=List[FeedbackResponse])
async def get_my_feedback_history(
    limit: int = 50,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    История feedback текущего пользователя
    """
    history = await feedback_service.get_user_feedback_history(
        db=db,
        user_id=current_user.id,
        limit=limit
    )
    
    return history


@router.get("/stats")
async def get_feedback_stats(
    days: int = 30,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Статистика по feedback (доступно всем пользователям)
    """
    date_from = datetime.utcnow() - timedelta(days=days)
    
    stats = await feedback_service.get_feedback_stats(
        db=db,
        date_from=date_from
    )
    
    return stats
