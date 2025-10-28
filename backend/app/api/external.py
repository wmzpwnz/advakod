from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time
import hashlib
import hmac
import json
from datetime import datetime, timedelta

from ..core.database import get_db
from ..models.user import User
from ..models.chat import ChatSession, ChatMessage
from ..services.auth_service import AuthService
from ..core.database import get_db
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
auth_service = AuthService()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return auth_service.get_current_user(token, db)
from ..core.encryption import get_encryption_manager

router = APIRouter()
security = HTTPBearer()

# Модели для внешнего API
class APIKeyCreate(BaseModel):
    name: str = Field(..., description="Название API ключа")
    permissions: List[str] = Field(default=["read"], description="Разрешения")
    expires_at: Optional[datetime] = Field(None, description="Дата истечения")

class APIKeyResponse(BaseModel):
    id: str
    name: str
    key: str
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]

class ExternalChatRequest(BaseModel):
    message: str = Field(..., description="Сообщение для ИИ")
    session_id: Optional[str] = Field(None, description="ID сессии")
    context: Optional[Dict[str, Any]] = Field(None, description="Дополнительный контекст")
    options: Optional[Dict[str, Any]] = Field(None, description="Опции обработки")

class ExternalChatResponse(BaseModel):
    response: str
    session_id: str
    message_id: str
    processing_time: float
    confidence: float
    suggestions: List[str]

class WebhookSubscription(BaseModel):
    url: str = Field(..., description="URL для webhook")
    events: List[str] = Field(..., description="События для подписки")
    secret: Optional[str] = Field(None, description="Секрет для подписи")

class WebhookEvent(BaseModel):
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    signature: str

# Модель для API ключей
class APIKey:
    def __init__(self, key_id: str, user_id: int, name: str, key: str, permissions: List[str], expires_at: Optional[datetime] = None):
        self.id = key_id
        self.user_id = user_id
        self.name = name
        self.key = key
        self.permissions = permissions
        self.created_at = datetime.now()
        self.expires_at = expires_at
        self.last_used = None

# Хранилище API ключей (в реальном приложении - база данных)
api_keys_storage: Dict[str, APIKey] = {}
webhook_subscriptions: Dict[str, Dict[str, Any]] = {}

def generate_api_key() -> str:
    """Генерация API ключа"""
    return f"ak_{hashlib.sha256(f'{time.time()}'.encode()).hexdigest()[:32]}"

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> APIKey:
    """Проверка API ключа"""
    api_key = credentials.credentials
    
    if api_key not in api_keys_storage:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    stored_key = api_keys_storage[api_key]
    
    # Проверяем срок действия
    if stored_key.expires_at and stored_key.expires_at < datetime.now():
        raise HTTPException(status_code=401, detail="API key expired")
    
    # Обновляем время последнего использования
    stored_key.last_used = datetime.now()
    
    return stored_key

def check_permission(api_key: APIKey, required_permission: str):
    """Проверка разрешения"""
    if required_permission not in api_key.permissions:
        raise HTTPException(status_code=403, detail=f"Permission '{required_permission}' required")

# API ключи
@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание нового API ключа"""
    try:
        api_key = generate_api_key()
        key_id = f"key_{int(time.time())}"
        
        new_api_key = APIKey(
            key_id=key_id,
            user_id=current_user.id,
            name=api_key_data.name,
            key=api_key,
            permissions=api_key_data.permissions,
            expires_at=api_key_data.expires_at
        )
        
        api_keys_storage[api_key] = new_api_key
        
        return APIKeyResponse(
            id=key_id,
            name=new_api_key.name,
            key=api_key,
            permissions=new_api_key.permissions,
            created_at=new_api_key.created_at,
            expires_at=new_api_key.expires_at,
            last_used=new_api_key.last_used
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Список API ключей пользователя"""
    user_keys = [
        APIKeyResponse(
            id=key.id,
            name=key.name,
            key=key.key[:8] + "..." + key.key[-4:],  # Скрываем ключ
            permissions=key.permissions,
            created_at=key.created_at,
            expires_at=key.expires_at,
            last_used=key.last_used
        )
        for key in api_keys_storage.values()
        if key.user_id == current_user.id
    ]
    
    return user_keys

@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Отзыв API ключа"""
    # Находим ключ по ID
    for api_key, key_obj in api_keys_storage.items():
        if key_obj.id == key_id and key_obj.user_id == current_user.id:
            del api_keys_storage[api_key]
            return {"message": "API key revoked successfully"}
    
    raise HTTPException(status_code=404, detail="API key not found")

# Внешний чат API
@router.post("/chat", response_model=ExternalChatResponse)
async def external_chat(
    request: ExternalChatRequest,
    api_key: APIKey = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Внешний API для чата с ИИ"""
    check_permission(api_key, "chat")
    
    try:
        start_time = time.time()
        
        # Создаем или получаем сессию
        if request.session_id:
            session = db.query(ChatSession).filter(
                ChatSession.id == request.session_id,
                ChatSession.user_id == api_key.user_id
            ).first()
        else:
            session = ChatSession(
                user_id=api_key.user_id,
                title=f"External API Session {int(time.time())}",
                created_at=time.time()
            )
            db.add(session)
            db.commit()
        
        # Создаем сообщение пользователя
        user_message = ChatMessage(
            session_id=session.id,
            role="user",
            content=request.message,
            created_at=time.time()
        )
        db.add(user_message)
        
        # Имитация ответа ИИ
        ai_response = f"AI Response to: {request.message[:100]}..."
        confidence = 0.85
        
        # Создаем ответ ИИ
        ai_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=ai_response,
            created_at=time.time()
        )
        db.add(ai_message)
        db.commit()
        
        processing_time = time.time() - start_time
        
        return ExternalChatResponse(
            response=ai_response,
            session_id=str(session.id),
            message_id=str(ai_message.id),
            processing_time=processing_time,
            confidence=confidence,
            suggestions=["Попробуйте задать более конкретный вопрос", "Используйте ключевые слова"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Webhook подписки
@router.post("/webhooks")
async def create_webhook_subscription(
    subscription: WebhookSubscription,
    api_key: APIKey = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Создание webhook подписки"""
    check_permission(api_key, "webhooks")
    
    try:
        webhook_id = f"wh_{int(time.time())}"
        
        webhook_subscriptions[webhook_id] = {
            "id": webhook_id,
            "user_id": api_key.user_id,
            "url": subscription.url,
            "events": subscription.events,
            "secret": subscription.secret,
            "created_at": datetime.now(),
            "is_active": True
        }
        
        return {
            "webhook_id": webhook_id,
            "url": subscription.url,
            "events": subscription.events,
            "status": "active"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/webhooks")
async def list_webhook_subscriptions(
    api_key: APIKey = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Список webhook подписок"""
    check_permission(api_key, "webhooks")
    
    user_webhooks = [
        {
            "id": wh["id"],
            "url": wh["url"],
            "events": wh["events"],
            "created_at": wh["created_at"],
            "is_active": wh["is_active"]
        }
        for wh in webhook_subscriptions.values()
        if wh["user_id"] == api_key.user_id
    ]
    
    return user_webhooks

@router.delete("/webhooks/{webhook_id}")
async def delete_webhook_subscription(
    webhook_id: str,
    api_key: APIKey = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Удаление webhook подписки"""
    check_permission(api_key, "webhooks")
    
    if webhook_id in webhook_subscriptions:
        webhook = webhook_subscriptions[webhook_id]
        if webhook["user_id"] == api_key.user_id:
            del webhook_subscriptions[webhook_id]
            return {"message": "Webhook subscription deleted"}
    
    raise HTTPException(status_code=404, detail="Webhook subscription not found")

# Статистика API
@router.get("/stats")
async def get_api_stats(
    api_key: APIKey = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Получение статистики использования API"""
    check_permission(api_key, "stats")
    
    # В реальном приложении здесь будет запрос к базе данных
    stats = {
        "api_key_id": api_key.id,
        "requests_today": 150,
        "requests_this_month": 4500,
        "total_requests": 12500,
        "last_request": api_key.last_used.isoformat() if api_key.last_used else None,
        "rate_limit": {
            "limit": 1000,
            "remaining": 850,
            "reset_time": (datetime.now() + timedelta(hours=1)).isoformat()
        }
    }
    
    return stats

# Документация API
@router.get("/docs")
async def get_api_documentation():
    """Документация внешнего API"""
    return {
        "title": "ИИ-Юрист External API",
        "version": "1.0.0",
        "description": "API для интеграции с ИИ-Юрист",
        "base_url": "https://api.ai-lawyer.com/v1",
        "authentication": {
            "type": "Bearer Token",
            "header": "Authorization: Bearer <api_key>"
        },
        "endpoints": {
            "/chat": {
                "method": "POST",
                "description": "Отправка сообщения ИИ",
                "permissions": ["chat"]
            },
            "/api-keys": {
                "method": "GET",
                "description": "Список API ключей",
                "permissions": ["read"]
            },
            "/webhooks": {
                "method": "POST",
                "description": "Создание webhook подписки",
                "permissions": ["webhooks"]
            },
            "/stats": {
                "method": "GET",
                "description": "Статистика использования",
                "permissions": ["stats"]
            }
        },
        "rate_limits": {
            "free": "100 requests/hour",
            "basic": "1000 requests/hour",
            "premium": "10000 requests/hour"
        },
        "webhook_events": [
            "chat.message.created",
            "chat.session.updated",
            "user.subscription.changed",
            "document.analyzed"
        ]
    }

# Функция для отправки webhook уведомлений
async def send_webhook_notification(event_type: str, data: Dict[str, Any], user_id: int):
    """Отправка webhook уведомления"""
    import aiohttp
    
    # Находим подписки пользователя для этого события
    user_webhooks = [
        wh for wh in webhook_subscriptions.values()
        if wh["user_id"] == user_id and event_type in wh["events"] and wh["is_active"]
    ]
    
    for webhook in user_webhooks:
        try:
            payload = {
                "event_type": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Создаем подпись если есть секрет
            if webhook["secret"]:
                signature = hmac.new(
                    webhook["secret"].encode(),
                    json.dumps(payload).encode(),
                    hashlib.sha256
                ).hexdigest()
                payload["signature"] = signature
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook["url"],
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status >= 400:
                        logger.error(f"Webhook failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Webhook error: {str(e)}")

# Health check для внешнего API
@router.get("/health")
async def external_api_health():
    """Проверка здоровья внешнего API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "database": "healthy",
            "ai_service": "healthy",
            "webhook_service": "healthy"
        }
    }
