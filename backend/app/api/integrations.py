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

class IntegrationRequest(BaseModel):
    service_name: str = Field(..., description="Название сервиса")
    api_key: str = Field(..., description="API ключ")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Конфигурация")

class IntegrationResponse(BaseModel):
    id: str
    user_id: int
    service_name: str
    status: str
    created_at: datetime
    last_sync: Optional[datetime]
    configuration: Dict[str, Any]

# Имитация базы данных интеграций
user_integrations = {}

@router.post("/connect", response_model=IntegrationResponse)
async def connect_integration(
    request: IntegrationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Подключение интеграции"""
    try:
        integration_id = f"int_{current_user.id}_{int(datetime.now().timestamp())}"
        
        integration = {
            "id": integration_id,
            "user_id": current_user.id,
            "service_name": request.service_name,
            "status": "connected",
            "created_at": datetime.now(),
            "last_sync": None,
            "configuration": request.configuration or {}
        }
        
        if current_user.id not in user_integrations:
            user_integrations[current_user.id] = []
        
        user_integrations[current_user.id].append(integration)
        
        return IntegrationResponse(**integration)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[IntegrationResponse])
async def get_integrations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение интеграций пользователя"""
    try:
        integrations = user_integrations.get(current_user.id, [])
        return [IntegrationResponse(**intg) for intg in integrations]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{integration_id}")
async def disconnect_integration(
    integration_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Отключение интеграции"""
    try:
        if current_user.id in user_integrations:
            user_integrations[current_user.id] = [
                i for i in user_integrations[current_user.id] 
                if i["id"] != integration_id
            ]
        
        return {"message": "Integration disconnected"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available")
async def get_available_integrations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение доступных интеграций"""
    try:
        return {
            "integrations": [
                {
                    "name": "Google Drive",
                    "description": "Синхронизация с Google Drive",
                    "icon": "google-drive",
                    "category": "storage"
                },
                {
                    "name": "Dropbox",
                    "description": "Синхронизация с Dropbox",
                    "icon": "dropbox",
                    "category": "storage"
                },
                {
                    "name": "Slack",
                    "description": "Уведомления в Slack",
                    "icon": "slack",
                    "category": "communication"
                },
                {
                    "name": "Microsoft Teams",
                    "description": "Интеграция с Microsoft Teams",
                    "icon": "teams",
                    "category": "communication"
                }
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
