"""
Redis Events Service - сервис для публикации и подписки на события через Redis
"""

import logging
import asyncio
from enum import Enum
from typing import Any, Dict, Callable, Optional
import json

logger = logging.getLogger(__name__)

# Попытка импорта Redis
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis не установлен, события будут игнорироваться")


class EventType(Enum):
    """Типы событий"""
    SERVICE_HEALTH_CHECK = "service.health_check"
    SERVICE_RECOVERY_NEEDED = "service.recovery_needed"
    SERVICE_STATUS_CHANGED = "service.status_changed"
    METRICS_UPDATED = "metrics.updated"


class RedisEventsService:
    """Сервис для работы с событиями через Redis pub/sub"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.redis_url: Optional[str] = None
        self._initialized: bool = False
        self._subscribers: Dict[EventType, list] = {}
        self._listen_task: Optional[asyncio.Task] = None
    
    async def initialize(self, redis_url: str) -> bool:
        """Инициализация сервиса"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis недоступен, события будут игнорироваться")
            self._initialized = False
            return False
        
        try:
            self.redis_url = redis_url
            self.redis_client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Проверяем подключение
            await self.redis_client.ping()
            self._initialized = True
            logger.info("✅ Redis Events Service инициализирован")
            return True
            
        except Exception as e:
            logger.warning(f"Не удалось инициализировать Redis Events Service: {e}")
            self._initialized = False
            return False
    
    async def publish_event(self, event_type: EventType, data: Dict[str, Any]) -> bool:
        """Публикация события"""
        if not self._initialized or not self.redis_client:
            return False
        
        try:
            message = json.dumps({
                "type": event_type.value,
                "data": data
            }, ensure_ascii=False, default=str)
            
            await self.redis_client.publish(event_type.value, message)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка публикации события {event_type.value}: {e}")
            return False
    
    async def subscribe(self, event_type: EventType, callback: Callable) -> bool:
        """Подписка на событие"""
        if not self._initialized or not self.redis_client:
            return False
        
        try:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            
            self._subscribers[event_type].append(callback)
            
            # Запускаем прослушивание если еще не запущено
            if self._listen_task is None or self._listen_task.done():
                self._listen_task = asyncio.create_task(self._listen_events())
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка подписки на событие {event_type.value}: {e}")
            return False
    
    async def _listen_events(self):
        """Прослушивание событий"""
        if not self._initialized or not self.redis_client:
            return
        
        try:
            pubsub = self.redis_client.pubsub()
            
            # Подписываемся на все каналы событий
            for event_type in self._subscribers.keys():
                await pubsub.subscribe(event_type.value)
            
            # Прослушиваем события
            while self._initialized:
                try:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if message and message['type'] == 'message':
                        channel = message['channel']
                        data = json.loads(message['data'])
                        
                        # Находим соответствующий EventType
                        for event_type, callbacks in self._subscribers.items():
                            if event_type.value == channel:
                                for callback in callbacks:
                                    try:
                                        if asyncio.iscoroutinefunction(callback):
                                            await callback(data)
                                        else:
                                            callback(data)
                                    except Exception as e:
                                        logger.error(f"Ошибка в callback для {event_type.value}: {e}")
                
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Ошибка при прослушивании событий: {e}")
                    await asyncio.sleep(1)
            
            await pubsub.close()
            
        except Exception as e:
            logger.error(f"Ошибка в _listen_events: {e}")
    
    async def close(self):
        """Закрытие сервиса"""
        self._initialized = False
        
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        
        if self.redis_client:
            try:
                await self.redis_client.aclose()
            except Exception:
                pass
        
        self._subscribers.clear()
        logger.info("Redis Events Service закрыт")


# Глобальный экземпляр сервиса
redis_events_service = RedisEventsService()

