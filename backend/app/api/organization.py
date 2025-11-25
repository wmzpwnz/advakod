"""
API endpoints для получения данных организаций и банков по ИНН и БИК
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
import logging

logger = logging.getLogger(__name__)

from ..core.database import get_db
from ..models.user import User
from ..services.auth_service import AuthService
from ..services.organization_service import organization_service

router = APIRouter(prefix="/organization", tags=["organization"])
auth_service = AuthService()


@router.get("")
async def get_organization_by_inn(
    inn: str = Query(..., description="ИНН организации (10 или 12 цифр)", min_length=10, max_length=12),
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить данные организации по ИНН
    
    Args:
        inn: ИНН организации (10 или 12 цифр)
        current_user: Текущий авторизованный пользователь
        db: Сессия БД
        
    Returns:
        Данные организации
    """
    # Валидация ИНН
    if not inn.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ИНН должен содержать только цифры"
        )
    
    if len(inn) not in [10, 12]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ИНН должен содержать 10 или 12 цифр"
        )
    
    try:
        result = await organization_service.get_organization_by_inn(inn, db)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Организация с таким ИНН не найдена"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения данных организации по ИНН {inn}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера при получении данных организации"
        )


@router.get("/bank")
async def get_bank_by_bik(
    bik: str = Query(..., description="БИК банка (9 цифр)", min_length=9, max_length=9),
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить данные банка по БИК
    
    Args:
        bik: БИК банка (9 цифр)
        current_user: Текущий авторизованный пользователь
        db: Сессия БД
        
    Returns:
        Данные банка
    """
    # Валидация БИК
    if not bik.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="БИК должен содержать только цифры"
        )
    
    if len(bik) != 9:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="БИК должен содержать 9 цифр"
        )
    
    try:
        result = await organization_service.get_bank_by_bik(bik, db)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Банк с таким БИК не найден"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения данных банка по БИК {bik}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера при получении данных банка"
        )

