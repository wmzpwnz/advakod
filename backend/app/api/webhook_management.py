from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time
import uuid
from datetime import datetime

from ..core.database import get_db
from ..models.user import User
from ..core.webhooks import (
    get_webhook_manager, 
    WebhookEventType, 
    WebhookSubscription,
    create_chat_message_event,
    create_user_subscription_event,
    create_document_analyzed_event,
    create_user_registered_event,
    create_payment_completed_event
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

class WebhookSubscriptionCreate(BaseModel):
    url: str = Field(..., description="URL для webhook")
    events: List[str] = Field(..., description="Список событий для подписки")
    secret: Optional[str] = Field(None, description="Секрет для подписи")

class WebhookSubscriptionResponse(BaseModel):
    id: str
    url: str
    events: List[str]
    is_active: bool
    created_at: datetime
    last_triggered: Optional[datetime]
    failure_count: int

class WebhookTestRequest(BaseModel):
    event_type: str = Field(..., description="Тип события для тестирования")
    test_data: Optional[Dict[str, Any]] = Field(None, description="Тестовые данные")

class WebhookStatsResponse(BaseModel):
    total_subscriptions: int
    active_subscriptions: int
    inactive_subscriptions: int
    queue_size: int
    event_counts: Dict[str, int]
    subscriptions_by_user: Dict[str, int]

@router.post("/webhooks", response_model=WebhookSubscriptionResponse)
async def create_webhook_subscription(
    subscription_data: WebhookSubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание webhook подписки"""
    try:
        # Валидация событий
        valid_events = []
        for event_str in subscription_data.events:
            try:
                event_type = WebhookEventType(event_str)
                valid_events.append(event_type)
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid event type: {event_str}"
                )
        
        # Создание подписки
        subscription_id = f"wh_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        subscription = WebhookSubscription(
            id=subscription_id,
            user_id=current_user.id,
            url=subscription_data.url,
            events=valid_events,
            secret=subscription_data.secret,
            is_active=True,
            created_at=datetime.now()
        )
        
        # Добавляем в менеджер
        webhook_manager = get_webhook_manager()
        webhook_manager.add_subscription(subscription)
        
        # Триггерим событие создания подписки
        event = create_user_registered_event(
            current_user.id,
            {
                "subscription_id": subscription_id,
                "url": subscription_data.url,
                "events": subscription_data.events
            }
        )
        await webhook_manager.trigger_event(event)
        
        return WebhookSubscriptionResponse(
            id=subscription.id,
            url=subscription.url,
            events=[e.value for e in subscription.events],
            is_active=subscription.is_active,
            created_at=subscription.created_at,
            last_triggered=subscription.last_triggered,
            failure_count=subscription.failure_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/webhooks", response_model=List[WebhookSubscriptionResponse])
async def list_webhook_subscriptions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Список webhook подписок пользователя"""
    try:
        webhook_manager = get_webhook_manager()
        subscriptions = webhook_manager.get_user_subscriptions(current_user.id)
        
        return [
            WebhookSubscriptionResponse(
                id=sub.id,
                url=sub.url,
                events=[e.value for e in sub.events],
                is_active=sub.is_active,
                created_at=sub.created_at,
                last_triggered=sub.last_triggered,
                failure_count=sub.failure_count
            )
            for sub in subscriptions
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/webhooks/{subscription_id}", response_model=WebhookSubscriptionResponse)
async def get_webhook_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение webhook подписки по ID"""
    try:
        webhook_manager = get_webhook_manager()
        
        if subscription_id not in webhook_manager.subscriptions:
            raise HTTPException(status_code=404, detail="Webhook subscription not found")
        
        subscription = webhook_manager.subscriptions[subscription_id]
        
        if subscription.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return WebhookSubscriptionResponse(
            id=subscription.id,
            url=subscription.url,
            events=[e.value for e in subscription.events],
            is_active=subscription.is_active,
            created_at=subscription.created_at,
            last_triggered=subscription.last_triggered,
            failure_count=subscription.failure_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/webhooks/{subscription_id}")
async def update_webhook_subscription(
    subscription_id: str,
    subscription_data: WebhookSubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление webhook подписки"""
    try:
        webhook_manager = get_webhook_manager()
        
        if subscription_id not in webhook_manager.subscriptions:
            raise HTTPException(status_code=404, detail="Webhook subscription not found")
        
        subscription = webhook_manager.subscriptions[subscription_id]
        
        if subscription.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Валидация событий
        valid_events = []
        for event_str in subscription_data.events:
            try:
                event_type = WebhookEventType(event_str)
                valid_events.append(event_type)
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid event type: {event_str}"
                )
        
        # Обновляем подписку
        subscription.url = subscription_data.url
        subscription.events = valid_events
        subscription.secret = subscription_data.secret
        subscription.failure_count = 0  # Сбрасываем счетчик ошибок
        
        return {"message": "Webhook subscription updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/webhooks/{subscription_id}")
async def delete_webhook_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удаление webhook подписки"""
    try:
        webhook_manager = get_webhook_manager()
        
        if subscription_id not in webhook_manager.subscriptions:
            raise HTTPException(status_code=404, detail="Webhook subscription not found")
        
        subscription = webhook_manager.subscriptions[subscription_id]
        
        if subscription.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Удаляем подписку
        webhook_manager.remove_subscription(subscription_id)
        
        return {"message": "Webhook subscription deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhooks/{subscription_id}/test")
async def test_webhook_subscription(
    subscription_id: str,
    test_data: WebhookTestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Тестирование webhook подписки"""
    try:
        webhook_manager = get_webhook_manager()
        
        if subscription_id not in webhook_manager.subscriptions:
            raise HTTPException(status_code=404, detail="Webhook subscription not found")
        
        subscription = webhook_manager.subscriptions[subscription_id]
        
        if subscription.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Создаем тестовое событие
        try:
            event_type = WebhookEventType(test_data.event_type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid event type: {test_data.event_type}"
            )
        
        from ..core.webhooks import WebhookEvent
        test_event = WebhookEvent(
            event_type=event_type,
            data=test_data.test_data or {"test": True, "message": "Test webhook event"},
            timestamp=datetime.now(),
            user_id=current_user.id,
            event_id=f"test_{int(time.time())}"
        )
        
        # Отправляем тестовое событие
        await webhook_manager.trigger_event(test_event)
        
        return {"message": "Test webhook event sent successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/webhooks/stats", response_model=WebhookStatsResponse)
async def get_webhook_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение статистики webhook"""
    try:
        webhook_manager = get_webhook_manager()
        stats = await webhook_manager.get_webhook_stats()
        
        return WebhookStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/webhooks/events")
async def list_available_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Список доступных событий для webhook"""
    try:
        events = [
            {
                "type": event_type.value,
                "description": _get_event_description(event_type),
                "example_data": _get_event_example_data(event_type)
            }
            for event_type in WebhookEventType
        ]
        
        return {"events": events}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _get_event_description(event_type: WebhookEventType) -> str:
    """Получение описания события"""
    descriptions = {
        WebhookEventType.CHAT_MESSAGE_CREATED: "Создание нового сообщения в чате",
        WebhookEventType.CHAT_SESSION_UPDATED: "Обновление сессии чата",
        WebhookEventType.USER_SUBSCRIPTION_CHANGED: "Изменение подписки пользователя",
        WebhookEventType.DOCUMENT_ANALYZED: "Анализ документа завершен",
        WebhookEventType.USER_REGISTERED: "Регистрация нового пользователя",
        WebhookEventType.USER_LOGIN: "Вход пользователя в систему",
        WebhookEventType.PAYMENT_COMPLETED: "Завершение платежа",
        WebhookEventType.API_KEY_CREATED: "Создание нового API ключа",
        WebhookEventType.API_KEY_REVOKED: "Отзыв API ключа",
        WebhookEventType.WEBHOOK_SUBSCRIPTION_CREATED: "Создание webhook подписки",
        WebhookEventType.WEBHOOK_SUBSCRIPTION_DELETED: "Удаление webhook подписки"
    }
    return descriptions.get(event_type, "Неизвестное событие")

def _get_event_example_data(event_type: WebhookEventType) -> Dict[str, Any]:
    """Получение примера данных события"""
    examples = {
        WebhookEventType.CHAT_MESSAGE_CREATED: {
            "message_id": "12345",
            "session_id": "67890",
            "content": "Привет, как дела?",
            "role": "user"
        },
        WebhookEventType.USER_SUBSCRIPTION_CHANGED: {
            "user_id": 123,
            "old_subscription": "free",
            "new_subscription": "premium",
            "expires_at": "2024-12-31T23:59:59Z"
        },
        WebhookEventType.DOCUMENT_ANALYZED: {
            "document_id": "doc_123",
            "analysis_type": "contract",
            "confidence": 0.95,
            "summary": "Договор содержит стандартные условия"
        }
    }
    return examples.get(event_type, {"example": "data"})
