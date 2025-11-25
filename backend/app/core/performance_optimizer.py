"""
Система оптимизации производительности для ИИ-Юриста
Включает кэширование, пулинг соединений и асинхронную загрузку моделей
"""

import asyncio
import time
import hashlib
import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from functools import lru_cache, wraps
import logging
from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue, Empty
import weakref

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Запись в кэше"""
    data: Any
    timestamp: float
    ttl: float
    access_count: int = 0
    last_access: float = 0.0


class AdvancedCache:
    """Продвинутый кэш с LRU и TTL"""
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Получает значение из кэша"""
        with self.lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            current_time = time.time()
            
            # Проверяем TTL
            if current_time - entry.timestamp > entry.ttl:
                del self.cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)
                return None
            
            # Обновляем статистику доступа
            entry.access_count += 1
            entry.last_access = current_time
            
            # Обновляем порядок доступа
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
            
            return entry.data
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Устанавливает значение в кэш"""
        with self.lock:
            current_time = time.time()
            ttl = ttl or self.default_ttl
            
            # Если ключ уже существует, обновляем
            if key in self.cache:
                self.cache[key].data = value
                self.cache[key].timestamp = current_time
                self.cache[key].ttl = ttl
                return
            
            # Проверяем размер кэша
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            # Добавляем новую запись
            self.cache[key] = CacheEntry(
                data=value,
                timestamp=current_time,
                ttl=ttl,
                access_count=1,
                last_access=current_time
            )
            self.access_order.append(key)
    
    def _evict_lru(self) -> None:
        """Удаляет наименее используемые записи"""
        if not self.access_order:
            return
        
        # Удаляем самую старую запись
        oldest_key = self.access_order[0]
        if oldest_key in self.cache:
            del self.cache[oldest_key]
        self.access_order.pop(0)
    
    def clear(self) -> None:
        """Очищает кэш"""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику кэша"""
        with self.lock:
            if not self.cache:
                return {"size": 0, "hit_rate": 0.0}
            
            total_access = sum(entry.access_count for entry in self.cache.values())
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "total_access": total_access,
                "hit_rate": total_access / len(self.cache) if self.cache else 0.0
            }


class ResponseCache:
    """Кэш для ответов ИИ"""
    
    def __init__(self, max_size: int = 1000):
        self.cache = AdvancedCache(max_size=max_size, default_ttl=7200)  # 2 часа
        self.query_hasher = QueryHasher()
    
    def get_cached_response(self, query: str, context: str = None) -> Optional[Dict]:
        """Получает кэшированный ответ"""
        cache_key = self.query_hasher.hash_query(query, context)
        return self.cache.get(cache_key)
    
    def cache_response(self, query: str, response: Dict, context: str = None, ttl: float = 7200):
        """Кэширует ответ"""
        cache_key = self.query_hasher.hash_query(query, context)
        self.cache.set(cache_key, response, ttl)
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику кэша"""
        return self.cache.get_stats()


class QueryHasher:
    """Хеширование запросов для кэширования"""
    
    def __init__(self):
        self.hash_cache = {}
    
    def hash_query(self, query: str, context: str = None) -> str:
        """Создает хеш для запроса"""
        # Нормализуем запрос
        normalized_query = self._normalize_query(query)
        normalized_context = self._normalize_query(context) if context else ""
        
        # Создаем ключ для хеширования
        hash_input = f"{normalized_query}|{normalized_context}"
        
        # Проверяем кэш хешей
        if hash_input in self.hash_cache:
            return self.hash_cache[hash_input]
        
        # Создаем хеш
        hash_obj = hashlib.sha256(hash_input.encode('utf-8'))
        query_hash = hash_obj.hexdigest()[:16]  # Используем первые 16 символов
        
        # Кэшируем хеш
        self.hash_cache[hash_input] = query_hash
        
        return query_hash
    
    def _normalize_query(self, query: str) -> str:
        """Нормализует запрос для хеширования"""
        if not query:
            return ""
        
        # Приводим к нижнему регистру
        normalized = query.lower().strip()
        
        # Удаляем лишние пробелы
        normalized = ' '.join(normalized.split())
        
        # Удаляем знаки препинания для лучшего сопоставления
        import re
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        return normalized


class PerformanceMonitor:
    """Монитор производительности"""
    
    def __init__(self):
        self.metrics = {}
        self.lock = threading.Lock()
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """Записывает метрику"""
        with self.lock:
            if name not in self.metrics:
                self.metrics[name] = []
            
            metric_entry = {
                "value": value,
                "timestamp": time.time(),
                "tags": tags or {}
            }
            self.metrics[name].append(metric_entry)
            
            # Ограничиваем количество записей
            if len(self.metrics[name]) > 1000:
                self.metrics[name] = self.metrics[name][-500:]
    
    def get_metric_stats(self, name: str) -> Dict[str, Any]:
        """Возвращает статистику метрики"""
        with self.lock:
            if name not in self.metrics:
                return {}
            
            values = [entry["value"] for entry in self.metrics[name]]
            if not values:
                return {}
            
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "latest": values[-1] if values else None
            }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Возвращает все метрики"""
        with self.lock:
            return {
                name: self.get_metric_stats(name)
                for name in self.metrics.keys()
            }


# Глобальные экземпляры
response_cache = ResponseCache()
performance_monitor = PerformanceMonitor()


def cache_ai_response(ttl: float = 7200):
    """Декоратор для кэширования ответов ИИ"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Извлекаем query и context из аргументов
            query = kwargs.get('query') or (args[0] if args else None)
            context = kwargs.get('context')
            
            if not query:
                return await func(*args, **kwargs)
            
            # Проверяем кэш
            cached_response = response_cache.get_cached_response(query, context)
            if cached_response:
                performance_monitor.record_metric("cache_hit", 1.0)
                return cached_response
            
            # Выполняем функцию
            start_time = time.time()
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Кэшируем результат
            if isinstance(result, dict):
                response_cache.cache_response(query, result, context, ttl)
            
            # Записываем метрики
            performance_monitor.record_metric("ai_response_time", duration)
            performance_monitor.record_metric("cache_miss", 1.0)
            
            return result
        
        return wrapper
    return decorator

    
def monitor_performance(metric_name: str):
    """Декоратор для мониторинга производительности"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                performance_monitor.record_metric(metric_name, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                performance_monitor.record_metric(f"{metric_name}_error", duration)
                raise
        
        return wrapper
    return decorator