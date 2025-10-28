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

class FavoriteRequest(BaseModel):
    item_type: str = Field(..., description="Тип элемента")
    item_id: str = Field(..., description="ID элемента")
    title: str = Field(..., description="Название")
    description: Optional[str] = Field(None, description="Описание")
    tags: Optional[List[str]] = Field(None, description="Теги")

class FavoriteResponse(BaseModel):
    id: str
    user_id: int
    item_type: str
    item_id: str
    title: str
    description: Optional[str]
    tags: List[str]
    created_at: datetime

# Имитация базы данных избранного
user_favorites = {}

@router.post("/add", response_model=FavoriteResponse)
async def add_to_favorites(
    request: FavoriteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Добавление в избранное"""
    try:
        favorite_id = f"fav_{current_user.id}_{int(datetime.now().timestamp())}"
        
        favorite = {
            "id": favorite_id,
            "user_id": current_user.id,
            "item_type": request.item_type,
            "item_id": request.item_id,
            "title": request.title,
            "description": request.description,
            "tags": request.tags or [],
            "created_at": datetime.now()
        }
        
        if current_user.id not in user_favorites:
            user_favorites[current_user.id] = []
        
        user_favorites[current_user.id].append(favorite)
        
        return FavoriteResponse(**favorite)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[FavoriteResponse])
async def get_favorites(
    item_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение избранного"""
    try:
        favorites = user_favorites.get(current_user.id, [])
        
        if item_type:
            favorites = [f for f in favorites if f["item_type"] == item_type]
        
        return [FavoriteResponse(**fav) for fav in favorites]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{favorite_id}")
async def remove_from_favorites(
    favorite_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удаление из избранного"""
    try:
        if current_user.id in user_favorites:
            user_favorites[current_user.id] = [
                f for f in user_favorites[current_user.id] 
                if f["id"] != favorite_id
            ]
        
        return {"message": "Removed from favorites"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
