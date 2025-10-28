import json
import hashlib
import logging
from typing import Any, Optional, Union, Dict
from datetime import datetime, timedelta
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)

# Попытка импорта Redis, если не установлен - используем in-memory кэш
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis не установлен, используется in-memory кэш")


class InMemoryCache:
    """In-memory кэш для случаев когда Redis недоступен"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key in self._cache:
                item = self._cache[key]
                if item['expires_at'] > datetime.now():
                    return item['value']
                else:
                    del self._cache[key]
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        async with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': datetime.now() + timedelta(seconds=ttl)
            }
            return True
    
    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        async with self._lock:
            if key in self._cache:
                item = self._cache[key]
                if item['expires_at'] > datetime.now():
                    return True
                else:
                    del self._cache[key]
            return False
    
    async def clear(self) -> bool:
        async with self._lock:
            self._cache.clear()
            return True


class CacheService:
    """Сервис кэширования с поддержкой Redis и fallback на in-memory"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.in_memory_cache = InMemoryCache()
        self._initialized = False
    
    async def initialize(self):
        """Инициализация кэша"""
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                
                # Проверяем подключение
                await self.redis_client.ping()
                self._initialized = True
                logger.info("Redis кэш инициализирован успешно")
                
            except Exception as e:
                logger.warning(f"Не удалось подключиться к Redis: {e}. Используется in-memory кэш")
                self.redis_client = None
                self._initialized = False
        else:
            logger.info("Redis недоступен, используется in-memory кэш")
            self._initialized = False
    
    async def get(self, key: str) -> Optional[Any]:
        """Получение значения из кэша"""
        if self.redis_client and self._initialized:
            try:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
                return None
            except Exception as e:
                logger.error(f"Ошибка получения из Redis: {e}")
                # Fallback на in-memory кэш
                return await self.in_memory_cache.get(key)
        else:
            return await self.in_memory_cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Сохранение значения в кэш"""
        try:
            serialized_value = json.dumps(value, ensure_ascii=False, default=str)
            
            if self.redis_client and self._initialized:
                try:
                    await self.redis_client.setex(key, ttl, serialized_value)
                    return True
                except Exception as e:
                    logger.error(f"Ошибка сохранения в Redis: {e}")
                    # Fallback на in-memory кэш
                    return await self.in_memory_cache.set(key, value, ttl)
            else:
                return await self.in_memory_cache.set(key, value, ttl)
                
        except Exception as e:
            logger.error(f"Ошибка сериализации для кэша: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Удаление значения из кэша"""
        if self.redis_client and self._initialized:
            try:
                result = await self.redis_client.delete(key)
                return result > 0
            except Exception as e:
                logger.error(f"Ошибка удаления из Redis: {e}")
                # Fallback на in-memory кэш
                return await self.in_memory_cache.delete(key)
        else:
            return await self.in_memory_cache.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Проверка существования ключа в кэше"""
        if self.redis_client and self._initialized:
            try:
                return await self.redis_client.exists(key) > 0
            except Exception as e:
                logger.error(f"Ошибка проверки существования в Redis: {e}")
                # Fallback на in-memory кэш
                return await self.in_memory_cache.exists(key)
        else:
            return await self.in_memory_cache.exists(key)
    
    async def clear_pattern(self, pattern: str) -> int:
        """Очистка ключей по паттерну"""
        if self.redis_client and self._initialized:
            try:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    return await self.redis_client.delete(*keys)
                return 0
            except Exception as e:
                logger.error(f"Ошибка очистки паттерна в Redis: {e}")
                return 0
        else:
            # Для in-memory кэша очищаем все (упрощенная реализация)
            await self.in_memory_cache.clear()
            return 1
    
    async def get_or_set(self, key: str, func, ttl: int = 3600, *args, **kwargs) -> Any:
        """Получить значение из кэша или вычислить и сохранить"""
        value = await self.get(key)
        if value is not None:
            return value
        
        # Вычисляем значение
        if asyncio.iscoroutinefunction(func):
            value = await func(*args, **kwargs)
        else:
            value = func(*args, **kwargs)
        
        # Сохраняем в кэш
        await self.set(key, value, ttl)
        return value
    
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Генерация ключа кэша на основе аргументов"""
        # Создаем строку из всех аргументов
        key_data = f"{prefix}:{':'.join(map(str, args))}"
        
        if kwargs:
            # Сортируем kwargs для консистентности
            sorted_kwargs = sorted(kwargs.items())
            key_data += f":{':'.join(f'{k}={v}' for k, v in sorted_kwargs)}"
        
        # Создаем хэш для длинных ключей
        if len(key_data) > 200:
            key_data = f"{prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"
        
        return key_data
    
    async def close(self):
        """Закрытие соединения с Redis"""
        if self.redis_client:
            await self.redis_client.close()


# Глобальный экземпляр кэша
cache_service = CacheService()


def cached(ttl: int = 3600, key_prefix: str = "cache"):
    """Декоратор для кэширования результатов функций"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Генерируем ключ кэша
            cache_key = cache_service.generate_key(
                key_prefix, 
                func.__name__, 
                *args, 
                **kwargs
            )
            
            # Пытаемся получить из кэша
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Выполняем функцию
            logger.debug(f"Cache miss for {cache_key}")
            result = await func(*args, **kwargs)
            
            # Сохраняем в кэш
            await cache_service.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Для синхронных функций создаем асинхронную обертку
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


# Специализированные кэши для разных типов данных
class ChatCache:
    """Кэш для чат-ответов"""
    
    @staticmethod
    async def cache_ai_response(question: str, response: str, ttl: int = 7200):
        """Кэширование ответа ИИ"""
        key = cache_service.generate_key("ai_response", question)
        await cache_service.set(key, response, ttl)
    
    @staticmethod
    async def get_cached_ai_response(question: str) -> Optional[str]:
        """Получение кэшированного ответа ИИ"""
        key = cache_service.generate_key("ai_response", question)
        return await cache_service.get(key)
    
    @staticmethod
    async def cache_rag_context(question: str, context: str, ttl: int = 3600):
        """Кэширование контекста RAG"""
        key = cache_service.generate_key("rag_context", question)
        await cache_service.set(key, context, ttl)
    
    @staticmethod
    async def get_cached_rag_context(question: str) -> Optional[str]:
        """Получение кэшированного контекста RAG"""
        key = cache_service.generate_key("rag_context", question)
        return await cache_service.get(key)


class UserCache:
    """Кэш для пользовательских данных"""
    
    @staticmethod
    async def cache_user_profile(user_id: int, profile_data: Dict[str, Any], ttl: int = 1800):
        """Кэширование профиля пользователя"""
        key = cache_service.generate_key("user_profile", user_id)
        await cache_service.set(key, profile_data, ttl)
    
    @staticmethod
    async def get_cached_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
        """Получение кэшированного профиля пользователя"""
        key = cache_service.generate_key("user_profile", user_id)
        return await cache_service.get(key)
    
    @staticmethod
    async def invalidate_user_cache(user_id: int):
        """Инвалидация кэша пользователя"""
        pattern = f"user_profile:{user_id}*"
        await cache_service.clear_pattern(pattern)
