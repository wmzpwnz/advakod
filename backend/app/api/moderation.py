"""
API для модерации ответов ИИ
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from ..core.database import get_db
from ..models.user import User
from ..services.auth_service import AuthService
from ..services.moderation_service import moderation_service
from ..services.rbac_service import rbac_service
from ..schemas.feedback import (
    ModerationReviewCreate,
    ModerationReviewUpdate,
    ModerationReviewResponse,
    QueueFilters,
    ProblemCategoryResponse,
    ModeratorStatsResponse,
    ModerationAnalytics
)

router = APIRouter()
auth_service = AuthService()


def check_moderator_permission(current_user: User, db: Session):
    """Проверка прав модератора (совместимость с текущей схемой прав).

    Принимаем следующие варианты:
    - явное право chats.moderate (если настроено)
    - права из текущей матрицы: manage_moderation или moderate_content
    - роли moderator/admin/super_admin
    - любой is_admin (как безопасный дефолт для админ-панели)
    """
    role = getattr(current_user, 'role', None)
    has_access = (
        getattr(current_user, 'is_admin', False) or
        current_user.has_permission("chats.moderate") or
        current_user.has_permission("manage_moderation") or
        current_user.has_permission("moderate_content") or
        role in ("moderator", "admin", "super_admin")
    )
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator permission required"
        )


@router.get("/queue")
async def get_moderation_queue(
    priority: Optional[str] = Query(None, pattern="^(high|medium|low)$"),
    status_filter: Optional[str] = Query(None, alias="status", pattern="^(pending|in_review|completed)$"),
    assigned_to_me: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получение очереди модерации
    
    Требуется право: chats.moderate
    
    Фильтры:
    - **priority**: high/medium/low
    - **status**: pending/in_review/completed
    - **assigned_to_me**: показать только назначенные мне
    - **page**: номер страницы
    - **page_size**: размер страницы (1-100)
    """
    check_moderator_permission(current_user, db)
    
    # Формируем фильтры
    filters = QueueFilters(
        priority=priority,
        status=status_filter,
        assigned_to_me=assigned_to_me
    )
    
    queue, total = await moderation_service.get_moderation_queue(
        db=db,
        moderator_id=current_user.id,
        filters=filters,
        page=page,
        page_size=page_size
    )
    
    return {
        "items": queue,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.post("/review", response_model=ModerationReviewResponse, status_code=status.HTTP_201_CREATED)
async def submit_review(
    review_data: ModerationReviewCreate,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Отправка оценки модератора
    
    Требуется право: chats.moderate
    
    - **message_id**: ID сообщения для оценки
    - **star_rating**: оценка от 1 до 10
    - **problem_categories**: список категорий проблем
    - **comment**: комментарий (обязательно, мин. 10 символов)
    - **suggested_fix**: предложенное исправление (опционально)
    - **priority**: приоритет (high/medium/low)
    """
    check_moderator_permission(current_user, db)
    
    try:
        review = await moderation_service.submit_review(
            db=db,
            moderator_id=current_user.id,
            review_data=review_data
        )
        
        return review
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit review"
        )


@router.put("/review/{review_id}", response_model=ModerationReviewResponse)
async def update_review(
    review_id: int,
    update_data: ModerationReviewUpdate,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Обновление оценки модератора
    
    Требуется право: chats.moderate
    
    Можно обновить только свою оценку
    """
    check_moderator_permission(current_user, db)
    
    try:
        review = await moderation_service.update_review(
            db=db,
            review_id=review_id,
            moderator_id=current_user.id,
            update_data=update_data
        )
        
        return review
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update review"
        )


@router.get("/categories", response_model=List[ProblemCategoryResponse])
async def get_problem_categories(
    active_only: bool = True,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получение списка категорий проблем
    
    Требуется право: chats.moderate
    """
    check_moderator_permission(current_user, db)
    
    categories = await moderation_service.get_problem_categories(
        db=db,
        active_only=active_only
    )
    
    return categories


@router.get("/my-stats", response_model=ModeratorStatsResponse)
async def get_my_stats(
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получение статистики текущего модератора
    
    Требуется право: chats.moderate
    """
    check_moderator_permission(current_user, db)
    
    stats = await moderation_service.get_moderator_stats(
        db=db,
        moderator_id=current_user.id
    )
    
    if not stats:
        # Возвращаем пустую статистику
        return {
            "moderator_id": current_user.id,
            "total_reviews": 0,
            "points": 0,
            "badges": [],
            "rank": "novice",
            "average_rating": None,
            "category_stats": {}
        }
    
    return stats


@router.get("/leaderboard")
async def get_leaderboard(
    period: str = Query("all_time", pattern="^(all_time|month|week)$"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Рейтинг модераторов
    
    Требуется право: chats.moderate
    
    - **period**: all_time/month/week
    - **limit**: количество модераторов (1-50)
    """
    check_moderator_permission(current_user, db)
    
    leaderboard = await moderation_service.get_leaderboard(
        db=db,
        period=period,
        limit=limit
    )
    
    return {
        "period": period,
        "leaderboard": leaderboard
    }


@router.get("/analytics")
async def get_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Аналитика модерации
    
    Требуется право: chats.moderate или analytics.read
    """
    # Проверяем права
    if not (current_user.has_permission("chats.moderate") or 
            current_user.has_permission("analytics.read")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission required: chats.moderate or analytics.read"
        )
    
    date_from = datetime.utcnow() - timedelta(days=days)
    
    analytics = await moderation_service.get_analytics(
        db=db,
        date_from=date_from
    )
    
    return analytics
