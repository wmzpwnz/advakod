"""
Retry Manager - управление повторными попытками для внешних сервисов
Обеспечивает надежное подключение к внешним зависимостям с различными стратегиями retry
"""

import asyncio
import logging
import time
import random
from typing import Callable, Any, Optional, Dict, List, Union
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Стратегии повторных попыток"""
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    RANDOM_JITTER = "random_jitter"
    FIBONACCI = "fibonacci"


class RetryCondition(Enum):
    """Условия для повторных попыток"""
    ON_EXCEPTION = "on_exception"
    ON_FALSE_RESULT = "on_false_result"
    ON_NONE_RESULT = "on_none_result"
    ON_CUSTOM_CONDITION = "on_custom_condition"


@dataclass
class RetryConfig:
    """Конфигурация повторных попыток"""
    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0
    jitter: bool = True
    timeout: Optional[float] = None
    retry_on_exceptions: List[type] = None
    retry_condition: RetryCondition = RetryCondition.ON_EXCEPTION
    custom_condition: Optional[Callable] = None
    backoff_factor: float = 0.1


@dataclass
class RetryAttempt:
    """Информация о попытке"""
    attempt_number: int
    start_time: datetime
    end_time: Optional[datetime]
    success: bool
    error: Optional[Exception]
    result: Any
    delay_before: float


@dataclass
class RetryStats:
    """Статистика повторных попыток"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_attempts: int = 0
    total_retry_time: float = 0.0
    average_attempts: float = 0.0
    success_rate: float = 0.0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None


class RetryManager:
    """Менеджер повторных попыток"""
    
    def __init__(self):
        self._stats: Dict[str, RetryStats] = {}
        self._active_retries: Dict[str, List[RetryAttempt]] = {}
        
        # Предустановленные конфигурации для разных типов сервисов
        self._service_configs = {
            "database": RetryConfig(
                max_attempts=5,
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                base_delay=0.5,
                max_delay=30.0,
                retry_on_exceptions=[ConnectionError, TimeoutError]
            ),
            "redis": RetryConfig(
                max_attempts=3,
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                base_delay=0.2,
                max_delay=10.0,
                retry_on_exceptions=[ConnectionError, TimeoutError]
            ),
            "chromadb": RetryConfig(
                max_attempts=3,
                strategy=RetryStrategy.LINEAR_BACKOFF,
                base_delay=1.0,
                max_delay=15.0,
                retry_on_exceptions=[ConnectionError, RuntimeError]
            ),
            "ai_model": RetryConfig(
                max_attempts=2,
                strategy=RetryStrategy.FIXED_DELAY,
                base_delay=2.0,
                max_delay=10.0,
                retry_on_exceptions=[RuntimeError, MemoryError]
            ),
            "file_system": RetryConfig(
                max_attempts=3,
                strategy=RetryStrategy.FIXED_DELAY,
                base_delay=0.1,
                max_delay=1.0,
                retry_on_exceptions=[FileNotFoundError, PermissionError, OSError]
            ),
            "network": RetryConfig(
                max_attempts=4,
                strategy=RetryStrategy.RANDOM_JITTER,
                base_delay=1.0,
                max_delay=20.0,
                retry_on_exceptions=[ConnectionError, TimeoutError, OSError]
            )
        }
    
    def get_config(self, service_type: str) -> RetryConfig:
        """Получает конфигурацию для типа сервиса"""
        return self._service_configs.get(service_type, RetryConfig())
    
    def register_service_config(self, service_type: str, config: RetryConfig):
        """Регистрирует конфигурацию для типа сервиса"""
        self._service_configs[service_type] = config
        logger.info(f"Registered retry config for service type: {service_type}")
    
    async def execute_with_retry(
        self,
        func: Callable,
        config: RetryConfig,
        service_name: str = "unknown",
        *args,
        **kwargs
    ) -> Any:
        """Выполняет функцию с повторными попытками"""
        
        # Инициализируем статистику если нужно
        if service_name not in self._stats:
            self._stats[service_name] = RetryStats()
        
        stats = self._stats[service_name]
        stats.total_calls += 1
        
        attempts = []
        last_exception = None
        
        for attempt_num in range(1, config.max_attempts + 1):
            attempt = RetryAttempt(
                attempt_number=attempt_num,
                start_time=datetime.now(),
                end_time=None,
                success=False,
                error=None,
                result=None,
                delay_before=0.0
            )
            
            # Вычисляем задержку перед попыткой (кроме первой)
            if attempt_num > 1:
                delay = self._calculate_delay(config, attempt_num - 1)
                attempt.delay_before = delay
                
                logger.debug(f"Retry attempt {attempt_num}/{config.max_attempts} for {service_name} "
                           f"after {delay:.2f}s delay")
                await asyncio.sleep(delay)
            
            try:
                # Выполняем функцию с таймаутом если указан
                if config.timeout:
                    if asyncio.iscoroutinefunction(func):
                        result = await asyncio.wait_for(func(*args, **kwargs), timeout=config.timeout)
                    else:
                        # Для синхронных функций создаем задачу
                        result = await asyncio.wait_for(
                            asyncio.get_event_loop().run_in_executor(None, func, *args, **kwargs),
                            timeout=config.timeout
                        )
                else:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                
                attempt.end_time = datetime.now()
                attempt.result = result
                
                # Проверяем условие успеха
                if self._is_success(result, config):
                    attempt.success = True
                    attempts.append(attempt)
                    
                    # Обновляем статистику
                    stats.successful_calls += 1
                    stats.total_attempts += attempt_num
                    stats.last_success = datetime.now()
                    
                    if stats.total_calls > 0:
                        stats.success_rate = stats.successful_calls / stats.total_calls
                        stats.average_attempts = stats.total_attempts / stats.total_calls
                    
                    # Сохраняем информацию о попытках
                    self._active_retries[service_name] = attempts
                    
                    logger.debug(f"Success for {service_name} on attempt {attempt_num}")
                    return result
                else:
                    # Результат не соответствует условию успеха
                    attempt.error = ValueError(f"Result does not meet success condition: {result}")
                    attempts.append(attempt)
                    
                    if attempt_num == config.max_attempts:
                        break  # Последняя попытка, выходим
                    
            except Exception as e:
                attempt.end_time = datetime.now()
                attempt.error = e
                attempts.append(attempt)
                last_exception = e
                
                # Проверяем, нужно ли повторять при этом исключении
                if not self._should_retry_on_exception(e, config):
                    logger.debug(f"Not retrying {service_name} due to non-retryable exception: {type(e).__name__}")
                    break
                
                logger.debug(f"Attempt {attempt_num} failed for {service_name}: {type(e).__name__}: {e}")
                
                if attempt_num == config.max_attempts:
                    break  # Последняя попытка, выходим
        
        # Все попытки исчерпаны
        stats.failed_calls += 1
        stats.total_attempts += config.max_attempts
        stats.last_failure = datetime.now()
        
        if stats.total_calls > 0:
            stats.success_rate = stats.successful_calls / stats.total_calls
            stats.average_attempts = stats.total_attempts / stats.total_calls
        
        # Сохраняем информацию о неудачных попытках
        self._active_retries[service_name] = attempts
        
        # Вычисляем общее время retry
        total_retry_time = sum(attempt.delay_before for attempt in attempts)
        stats.total_retry_time += total_retry_time
        
        logger.error(f"All retry attempts failed for {service_name} after {config.max_attempts} attempts")
        
        # Поднимаем последнее исключение или создаем новое
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError(f"All retry attempts failed for {service_name}")
    
    def _calculate_delay(self, config: RetryConfig, attempt_num: int) -> float:
        """Вычисляет задержку для указанной попытки"""
        
        if config.strategy == RetryStrategy.FIXED_DELAY:
            delay = config.base_delay
            
        elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (config.multiplier ** attempt_num)
            
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * (1 + attempt_num)
            
        elif config.strategy == RetryStrategy.FIBONACCI:
            # Последовательность Фибоначчи для задержек
            fib_sequence = [1, 1]
            for i in range(2, attempt_num + 2):
                fib_sequence.append(fib_sequence[i-1] + fib_sequence[i-2])
            delay = config.base_delay * fib_sequence[min(attempt_num, len(fib_sequence) - 1)]
            
        elif config.strategy == RetryStrategy.RANDOM_JITTER:
            # Случайная задержка в диапазоне
            delay = config.base_delay + random.uniform(0, config.base_delay * attempt_num)
            
        else:
            delay = config.base_delay
        
        # Применяем jitter если включен
        if config.jitter:
            jitter_amount = delay * config.backoff_factor * random.uniform(-1, 1)
            delay += jitter_amount
        
        # Ограничиваем максимальной задержкой
        delay = min(delay, config.max_delay)
        
        return max(0, delay)  # Не может быть отрицательной
    
    def _is_success(self, result: Any, config: RetryConfig) -> bool:
        """Проверяет, является ли результат успешным"""
        
        if config.retry_condition == RetryCondition.ON_EXCEPTION:
            # Если дошли до этой точки, значит исключения не было
            return True
            
        elif config.retry_condition == RetryCondition.ON_FALSE_RESULT:
            return bool(result)
            
        elif config.retry_condition == RetryCondition.ON_NONE_RESULT:
            return result is not None
            
        elif config.retry_condition == RetryCondition.ON_CUSTOM_CONDITION:
            if config.custom_condition:
                return config.custom_condition(result)
            return True
            
        return True
    
    def _should_retry_on_exception(self, exception: Exception, config: RetryConfig) -> bool:
        """Проверяет, нужно ли повторять при данном исключении"""
        
        if not config.retry_on_exceptions:
            return True  # Повторяем при любых исключениях
        
        # Проверяем, является ли исключение одним из разрешенных для retry
        for exc_type in config.retry_on_exceptions:
            if isinstance(exception, exc_type):
                return True
        
        return False
    
    def get_stats(self, service_name: str = None) -> Union[RetryStats, Dict[str, RetryStats]]:
        """Получает статистику повторных попыток"""
        
        if service_name:
            return self._stats.get(service_name, RetryStats())
        else:
            return self._stats.copy()
    
    def get_recent_attempts(self, service_name: str) -> List[RetryAttempt]:
        """Получает информацию о недавних попытках"""
        return self._active_retries.get(service_name, [])
    
    def reset_stats(self, service_name: str = None):
        """Сбрасывает статистику"""
        
        if service_name:
            if service_name in self._stats:
                self._stats[service_name] = RetryStats()
            if service_name in self._active_retries:
                del self._active_retries[service_name]
        else:
            self._stats.clear()
            self._active_retries.clear()
        
        logger.info(f"Reset retry stats for {service_name or 'all services'}")


# Глобальный экземпляр менеджера повторных попыток
retry_manager = RetryManager()


def with_retry(
    service_type: str = "default",
    service_name: str = None,
    config: RetryConfig = None
):
    """Декоратор для добавления retry логики к функциям"""
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Определяем конфигурацию
            retry_config = config or retry_manager.get_config(service_type)
            name = service_name or f"{func.__module__}.{func.__name__}"
            
            return await retry_manager.execute_with_retry(
                func, retry_config, name, *args, **kwargs
            )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Для синхронных функций создаем асинхронную обертку
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# Специализированные декораторы для разных типов сервисов

def with_database_retry(service_name: str = None, max_attempts: int = None):
    """Декоратор для операций с базой данных"""
    config = retry_manager.get_config("database")
    if max_attempts:
        config.max_attempts = max_attempts
    
    return with_retry("database", service_name, config)


def with_redis_retry(service_name: str = None, max_attempts: int = None):
    """Декоратор для операций с Redis"""
    config = retry_manager.get_config("redis")
    if max_attempts:
        config.max_attempts = max_attempts
    
    return with_retry("redis", service_name, config)


def with_chromadb_retry(service_name: str = None, max_attempts: int = None):
    """Декоратор для операций с ChromaDB"""
    config = retry_manager.get_config("chromadb")
    if max_attempts:
        config.max_attempts = max_attempts
    
    return with_retry("chromadb", service_name, config)


def with_ai_model_retry(service_name: str = None, max_attempts: int = None):
    """Декоратор для операций с AI моделью"""
    config = retry_manager.get_config("ai_model")
    if max_attempts:
        config.max_attempts = max_attempts
    
    return with_retry("ai_model", service_name, config)


def with_network_retry(service_name: str = None, max_attempts: int = None):
    """Декоратор для сетевых операций"""
    config = retry_manager.get_config("network")
    if max_attempts:
        config.max_attempts = max_attempts
    
    return with_retry("network", service_name, config)


# Вспомогательные функции для создания конфигураций

def create_retry_config(
    max_attempts: int = 3,
    strategy: str = "exponential_backoff",
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    **kwargs
) -> RetryConfig:
    """Создает конфигурацию retry с удобными параметрами"""
    
    strategy_enum = RetryStrategy(strategy)
    
    return RetryConfig(
        max_attempts=max_attempts,
        strategy=strategy_enum,
        base_delay=base_delay,
        max_delay=max_delay,
        **kwargs
    )


def create_database_retry_config(**kwargs) -> RetryConfig:
    """Создает конфигурацию retry для базы данных"""
    defaults = {
        "max_attempts": 5,
        "strategy": "exponential_backoff",
        "base_delay": 0.5,
        "max_delay": 30.0,
        "retry_on_exceptions": [ConnectionError, TimeoutError]
    }
    defaults.update(kwargs)
    return create_retry_config(**defaults)


def create_cache_retry_config(**kwargs) -> RetryConfig:
    """Создает конфигурацию retry для кэша"""
    defaults = {
        "max_attempts": 3,
        "strategy": "exponential_backoff",
        "base_delay": 0.2,
        "max_delay": 10.0,
        "retry_on_exceptions": [ConnectionError, TimeoutError]
    }
    defaults.update(kwargs)
    return create_retry_config(**defaults)