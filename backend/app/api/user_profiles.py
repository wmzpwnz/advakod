from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..core.database import get_db
from ..models.user import User
from ..services.auth_service import AuthService
from ..core.database import get_db
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
auth_service = AuthService()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return auth_service.get_current_user(token, db)

router = APIRouter()

class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, description="Имя")
    last_name: Optional[str] = Field(None, description="Фамилия")
    bio: Optional[str] = Field(None, description="Биография")
    company: Optional[str] = Field(None, description="Компания")
    position: Optional[str] = Field(None, description="Должность")
    phone: Optional[str] = Field(None, description="Телефон")
    website: Optional[str] = Field(None, description="Веб-сайт")
    location: Optional[str] = Field(None, description="Местоположение")
    timezone: Optional[str] = Field(None, description="Часовой пояс")
    language: Optional[str] = Field(None, description="Язык")
    preferences: Optional[Dict[str, Any]] = Field(None, description="Настройки")

class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    bio: Optional[str]
    company: Optional[str]
    position: Optional[str]
    phone: Optional[str]
    website: Optional[str]
    location: Optional[str]
    timezone: Optional[str]
    language: Optional[str]
    preferences: Dict[str, Any]
    created_at: datetime
    last_login: Optional[datetime]
    is_premium: bool

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение профиля пользователя"""
    return UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        first_name=getattr(current_user, 'first_name', None),
        last_name=getattr(current_user, 'last_name', None),
        bio=getattr(current_user, 'bio', None),
        company=getattr(current_user, 'company', None),
        position=getattr(current_user, 'position', None),
        phone=getattr(current_user, 'phone', None),
        website=getattr(current_user, 'website', None),
        location=getattr(current_user, 'location', None),
        timezone=getattr(current_user, 'timezone', None),
        language=getattr(current_user, 'language', None),
        preferences=getattr(current_user, 'preferences', {}),
        created_at=current_user.created_at,
        last_login=getattr(current_user, 'last_login', None),
        is_premium=current_user.is_premium
    )

@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление профиля пользователя"""
    try:
        # Обновляем поля профиля
        for field, value in profile_data.dict(exclude_unset=True).items():
            if hasattr(current_user, field):
                setattr(current_user, field, value)
        
        db.commit()
        db.refresh(current_user)
        
        return UserProfileResponse(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            first_name=getattr(current_user, 'first_name', None),
            last_name=getattr(current_user, 'last_name', None),
            bio=getattr(current_user, 'bio', None),
            company=getattr(current_user, 'company', None),
            position=getattr(current_user, 'position', None),
            phone=getattr(current_user, 'phone', None),
            website=getattr(current_user, 'website', None),
            location=getattr(current_user, 'location', None),
            timezone=getattr(current_user, 'timezone', None),
            language=getattr(current_user, 'language', None),
            preferences=getattr(current_user, 'preferences', {}),
            created_at=current_user.created_at,
            last_login=getattr(current_user, 'last_login', None),
            is_premium=current_user.is_premium
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
