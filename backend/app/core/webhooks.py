import asyncio
import aiohttp
import json
import hmac
import hashlib
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class WebhookEventType(Enum):
    """Типы webhook событий"""
    CHAT_MESSAGE_CREATED = "chat.message.created"
    CHAT_SESSION_UPDATED = "chat.session.updated"
    USER_SUBSCRIPTION_CHANGED = "user.subscription.changed"
    DOCUMENT_ANALYZED = "document.analyzed"
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    PAYMENT_COMPLETED = "payment.completed"
    API_KEY_CREATED = "api.key.created"
    API_KEY_REVOKED = "api.key.revoked"
    WEBHOOK_SUBSCRIPTION_CREATED = "webhook.subscription.created"
    WEBHOOK_SUBSCRIPTION_DELETED = "webhook.subscription.deleted"

@dataclass
class WebhookEvent:
    """Webhook событие"""
    event_type: WebhookEventType
    data: Dict[str, Any]
    timestamp: datetime
    user_id: int
    event_id: str

@dataclass
class WebhookSubscription:
    """Webhook подписка"""
    id: str
    user_id: int
    url: str
    events: List[WebhookEventType]
    secret: Optional[str]
    is_active: bool
    created_at: datetime
    last_triggered: Optional[datetime] = None
    failure_count: int = 0

class WebhookManager:
    """Менеджер webhook уведомлений"""
    
    def __init__(self):
        self.subscriptions: Dict[str, WebhookSubscription] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.max_retries = 3
        self.retry_delay = 5  # секунды
        self.timeout = 10  # секунды
        
    def add_subscription(self, subscription: WebhookSubscription):
        """Добавление webhook подписки"""
        self.subscriptions[subscription.id] = subscription
        logger.info(f"Added webhook subscription: {subscription.id}")
    
    def remove_subscription(self, subscription_id: str):
        """Удаление webhook подписки"""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            logger.info(f"Removed webhook subscription: {subscription_id}")
    
    def get_user_subscriptions(self, user_id: int) -> List[WebhookSubscription]:
        """Получение подписок пользователя"""
        return [
            sub for sub in self.subscriptions.values()
            if sub.user_id == user_id and sub.is_active
        ]
    
    async def trigger_event(self, event: WebhookEvent):
        """Триггер webhook события"""
        logger.info(f"Triggering webhook event: {event.event_type.value}")
        
        # Находим подходящие подписки
        matching_subscriptions = [
            sub for sub in self.subscriptions.values()
            if (sub.is_active and 
                event.event_type in sub.events and
                sub.user_id == event.user_id)
        ]
        
        if not matching_subscriptions:
            logger.info(f"No matching subscriptions for event: {event.event_type.value}")
            return
        
        # Отправляем события в очередь
        for subscription in matching_subscriptions:
            await self.event_queue.put((event, subscription))
    
    async def process_webhook_queue(self):
        """Обработка очереди webhook событий"""
        logger.info("Starting webhook queue processor")
        
        while True:
            try:
                # Получаем событие из очереди
                event, subscription = await self.event_queue.get()
                
                # Отправляем webhook
                await self._send_webhook(event, subscription)
                
                # Отмечаем задачу как выполненную
                self.event_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error processing webhook queue: {str(e)}")
                await asyncio.sleep(1)
    
    async def _send_webhook(self, event: WebhookEvent, subscription: WebhookSubscription):
        """Отправка webhook уведомления"""
        try:
            # Подготавливаем payload
            payload = {
                "event_type": event.event_type.value,
                "data": event.data,
                "timestamp": event.timestamp.isoformat(),
                "event_id": event.event_id
            }
            
            # Создаем подпись если есть секрет
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "AI-Lawyer-Webhook/1.0.0"
            }
            
            if subscription.secret:
                signature = self._create_signature(
                    json.dumps(payload, sort_keys=True),
                    subscription.secret
                )
                headers["X-Webhook-Signature"] = f"sha256={signature}"
            
            # Отправляем запрос
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    subscription.url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status >= 200 and response.status < 300:
                        # Успешная отправка
                        subscription.last_triggered = datetime.now()
                        subscription.failure_count = 0
                        logger.info(f"Webhook sent successfully to {subscription.url}")
                    else:
                        # Ошибка отправки
                        subscription.failure_count += 1
                        logger.error(f"Webhook failed: {response.status} - {subscription.url}")
                        
                        # Если слишком много ошибок, деактивируем подписку
                        if subscription.failure_count >= self.max_retries:
                            subscription.is_active = False
                            logger.warning(f"Deactivated webhook subscription due to failures: {subscription.id}")
                        
                        # Повторная попытка
                        if subscription.failure_count < self.max_retries:
                            await asyncio.sleep(self.retry_delay * subscription.failure_count)
                            await self.event_queue.put((event, subscription))
                    
        except asyncio.TimeoutError:
            subscription.failure_count += 1
            logger.error(f"Webhook timeout: {subscription.url}")
            
            if subscription.failure_count < self.max_retries:
                await asyncio.sleep(self.retry_delay * subscription.failure_count)
                await self.event_queue.put((event, subscription))
                
        except Exception as e:
            subscription.failure_count += 1
            logger.error(f"Webhook error: {str(e)} - {subscription.url}")
            
            if subscription.failure_count < self.max_retries:
                await asyncio.sleep(self.retry_delay * subscription.failure_count)
                await self.event_queue.put((event, subscription))
    
    def _create_signature(self, payload: str, secret: str) -> str:
        """Создание подписи для webhook"""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def verify_signature(self, payload: str, signature: str, secret: str) -> bool:
        """Проверка подписи webhook"""
        expected_signature = self._create_signature(payload, secret)
        return hmac.compare_digest(signature, expected_signature)
    
    async def get_webhook_stats(self) -> Dict[str, Any]:
        """Получение статистики webhook"""
        total_subscriptions = len(self.subscriptions)
        active_subscriptions = len([s for s in self.subscriptions.values() if s.is_active])
        
        event_counts = {}
        for subscription in self.subscriptions.values():
            for event_type in subscription.events:
                event_counts[event_type.value] = event_counts.get(event_type.value, 0) + 1
        
        return {
            "total_subscriptions": total_subscriptions,
            "active_subscriptions": active_subscriptions,
            "inactive_subscriptions": total_subscriptions - active_subscriptions,
            "queue_size": self.event_queue.qsize(),
            "event_counts": event_counts,
            "subscriptions_by_user": {
                str(user_id): len([s for s in self.subscriptions.values() if s.user_id == user_id])
                for user_id in set(s.user_id for s in self.subscriptions.values())
            }
        }

# Глобальный экземпляр менеджера webhook
webhook_manager = WebhookManager()

def get_webhook_manager() -> WebhookManager:
    """Получение экземпляра менеджера webhook"""
    return webhook_manager

# Утилиты для создания событий
def create_chat_message_event(user_id: int, message_data: Dict[str, Any]) -> WebhookEvent:
    """Создание события сообщения чата"""
    return WebhookEvent(
        event_type=WebhookEventType.CHAT_MESSAGE_CREATED,
        data=message_data,
        timestamp=datetime.now(),
        user_id=user_id,
        event_id=f"msg_{int(datetime.now().timestamp())}"
    )

def create_user_subscription_event(user_id: int, subscription_data: Dict[str, Any]) -> WebhookEvent:
    """Создание события изменения подписки"""
    return WebhookEvent(
        event_type=WebhookEventType.USER_SUBSCRIPTION_CHANGED,
        data=subscription_data,
        timestamp=datetime.now(),
        user_id=user_id,
        event_id=f"sub_{int(datetime.now().timestamp())}"
    )

def create_document_analyzed_event(user_id: int, document_data: Dict[str, Any]) -> WebhookEvent:
    """Создание события анализа документа"""
    return WebhookEvent(
        event_type=WebhookEventType.DOCUMENT_ANALYZED,
        data=document_data,
        timestamp=datetime.now(),
        user_id=user_id,
        event_id=f"doc_{int(datetime.now().timestamp())}"
    )

def create_user_registered_event(user_id: int, user_data: Dict[str, Any]) -> WebhookEvent:
    """Создание события регистрации пользователя"""
    return WebhookEvent(
        event_type=WebhookEventType.USER_REGISTERED,
        data=user_data,
        timestamp=datetime.now(),
        user_id=user_id,
        event_id=f"reg_{int(datetime.now().timestamp())}"
    )

def create_payment_completed_event(user_id: int, payment_data: Dict[str, Any]) -> WebhookEvent:
    """Создание события завершения платежа"""
    return WebhookEvent(
        event_type=WebhookEventType.PAYMENT_COMPLETED,
        data=payment_data,
        timestamp=datetime.now(),
        user_id=user_id,
        event_id=f"pay_{int(datetime.now().timestamp())}"
    )

# Функция для запуска обработчика webhook
async def start_webhook_processor():
    """Запуск обработчика webhook событий"""
    logger.info("Starting webhook processor")
    await webhook_manager.process_webhook_queue()
