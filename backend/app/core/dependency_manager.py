"""
Dependency Manager - управление зависимостями и порядком инициализации сервисов
Обеспечивает правильную последовательность запуска внешних зависимостей
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DependencyStatus(Enum):
    """Статусы зависимостей"""
    NOT_CHECKED = "not_checked"
    CHECKING = "checking"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class DependencyType(Enum):
    """Типы зависимостей"""
    DATABASE = "database"
    CACHE = "cache"
    VECTOR_STORE = "vector_store"
    MODEL_FILE = "model_file"
    EXTERNAL_SERVICE = "external_service"
    NETWORK = "network"


@dataclass
class DependencyInfo:
    """Информация о зависимости"""
    name: str
    type: DependencyType
    check_function: Callable
    status: DependencyStatus
    last_check: Optional[datetime]
    check_interval: int  # секунды
    timeout: int  # секунды для проверки
    retry_count: int
    max_retries: int
    error_message: Optional[str]
    required: bool  # обязательная ли зависимость
    dependencies: List[str]  # зависимости этой зависимости


class DependencyManager:
    """Менеджер зависимостей для управления внешними сервисами"""
    
    def __init__(self):
        self._dependencies: Dict[str, DependencyInfo] = {}
        self._initialization_order: List[str] = []
        self._check_tasks: Dict[str, asyncio.Task] = {}
        self._shutdown_requested = False
        
        # Настройки
        self._default_timeout = 30
        self._default_max_retries = 3
        self._default_check_interval = 60
        
        # Регистрируем стандартные зависимости
        self._register_standard_dependencies()
    
    def _register_standard_dependencies(self):
        """Регистрирует стандартные зависимости системы"""
        
        # PostgreSQL Database
        self.register_dependency(
            name="postgresql",
            type=DependencyType.DATABASE,
            check_function=self._check_postgresql,
            required=True,
            timeout=10,
            max_retries=5,
            check_interval=30
        )
        
        # Redis Cache
        self.register_dependency(
            name="redis",
            type=DependencyType.CACHE,
            check_function=self._check_redis,
            required=False,  # Есть fallback на in-memory
            timeout=5,
            max_retries=3,
            check_interval=30
        )
        
        # ChromaDB Vector Store
        self.register_dependency(
            name="chromadb",
            type=DependencyType.VECTOR_STORE,
            check_function=self._check_chromadb,
            required=True,
            timeout=15,
            max_retries=3,
            check_interval=60,
            dependencies=["postgresql"]  # ChromaDB может зависеть от PostgreSQL
        )
        
        # AI Model File
        self.register_dependency(
            name="ai_model_file",
            type=DependencyType.MODEL_FILE,
            check_function=self._check_ai_model_file,
            required=True,
            timeout=5,
            max_retries=1,  # Файл либо есть, либо нет
            check_interval=300  # Проверяем реже
        )
        
        # Embeddings Model
        self.register_dependency(
            name="embeddings_model",
            type=DependencyType.MODEL_FILE,
            check_function=self._check_embeddings_model,
            required=True,
            timeout=10,
            max_retries=2,
            check_interval=300
        )
        
        # Вычисляем порядок инициализации
        self._calculate_initialization_order()
    
    def register_dependency(
        self,
        name: str,
        type: DependencyType,
        check_function: Callable,
        required: bool = True,
        timeout: int = None,
        max_retries: int = None,
        check_interval: int = None,
        dependencies: List[str] = None
    ):
        """Регистрирует новую зависимость"""
        
        self._dependencies[name] = DependencyInfo(
            name=name,
            type=type,
            check_function=check_function,
            status=DependencyStatus.NOT_CHECKED,
            last_check=None,
            check_interval=check_interval or self._default_check_interval,
            timeout=timeout or self._default_timeout,
            retry_count=0,
            max_retries=max_retries or self._default_max_retries,
            error_message=None,
            required=required,
            dependencies=dependencies or []
        )
        
        # Пересчитываем порядок инициализации
        self._calculate_initialization_order()
        
        logger.info(f"Registered dependency: {name} (type: {type.value}, required: {required})")
    
    def _calculate_initialization_order(self):
        """Вычисляет порядок инициализации на основе зависимостей"""
        
        # Топологическая сортировка для определения порядка
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(dep_name: str):
            if dep_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {dep_name}")
            
            if dep_name not in visited:
                temp_visited.add(dep_name)
                
                if dep_name in self._dependencies:
                    for dependency in self._dependencies[dep_name].dependencies:
                        visit(dependency)
                
                temp_visited.remove(dep_name)
                visited.add(dep_name)
                order.append(dep_name)
        
        # Обходим все зависимости
        for dep_name in self._dependencies:
            if dep_name not in visited:
                visit(dep_name)
        
        self._initialization_order = order
        logger.info(f"Dependency initialization order: {' -> '.join(self._initialization_order)}")
    
    async def check_all_dependencies(self) -> Dict[str, bool]:
        """Проверяет все зависимости в правильном порядке"""
        
        logger.info("🔍 Starting dependency checks...")
        results = {}
        
        for dep_name in self._initialization_order:
            if dep_name in self._dependencies:
                result = await self._check_single_dependency(dep_name)
                results[dep_name] = result
                
                dep_info = self._dependencies[dep_name]
                if not result and dep_info.required:
                    logger.error(f"❌ Required dependency {dep_name} is not available")
                    # Не прерываем проверку, продолжаем для диагностики
                elif result:
                    logger.info(f"✅ Dependency {dep_name} is available")
                else:
                    logger.warning(f"⚠️ Optional dependency {dep_name} is not available")
        
        # Подсчитываем статистику
        total = len(results)
        available = sum(results.values())
        required_deps = [name for name, info in self._dependencies.items() if info.required]
        required_available = sum(results.get(name, False) for name in required_deps)
        
        logger.info(f"📊 Dependency check complete: {available}/{total} available, "
                   f"{required_available}/{len(required_deps)} required available")
        
        return results
    
    async def _check_single_dependency(self, dep_name: str) -> bool:
        """Проверяет одну зависимость с retry логикой"""
        
        if dep_name not in self._dependencies:
            logger.error(f"Unknown dependency: {dep_name}")
            return False
        
        dep_info = self._dependencies[dep_name]
        dep_info.status = DependencyStatus.CHECKING
        dep_info.last_check = datetime.now()
        
        for attempt in range(dep_info.max_retries + 1):
            try:
                logger.debug(f"Checking dependency {dep_name} (attempt {attempt + 1}/{dep_info.max_retries + 1})")
                
                # Выполняем проверку с таймаутом
                result = await asyncio.wait_for(
                    dep_info.check_function(),
                    timeout=dep_info.timeout
                )
                
                if result:
                    dep_info.status = DependencyStatus.AVAILABLE
                    dep_info.retry_count = 0
                    dep_info.error_message = None
                    return True
                else:
                    dep_info.status = DependencyStatus.UNAVAILABLE
                    
            except asyncio.TimeoutError:
                error_msg = f"Timeout after {dep_info.timeout}s"
                dep_info.error_message = error_msg
                logger.warning(f"Dependency {dep_name} check timeout: {error_msg}")
                
            except Exception as e:
                error_msg = str(e)
                dep_info.error_message = error_msg
                logger.warning(f"Dependency {dep_name} check error: {error_msg}")
            
            # Ждем перед повторной попыткой (кроме последней)
            if attempt < dep_info.max_retries:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.debug(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
        
        # Все попытки исчерпаны
        dep_info.status = DependencyStatus.ERROR
        dep_info.retry_count = dep_info.max_retries + 1
        
        return False
    
    async def wait_for_dependencies(self, required_only: bool = True, timeout: int = 300) -> bool:
        """Ждет готовности зависимостей с таймаутом"""
        
        logger.info(f"⏳ Waiting for dependencies (timeout: {timeout}s, required_only: {required_only})")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            results = await self.check_all_dependencies()
            
            if required_only:
                # Проверяем только обязательные зависимости
                required_deps = [name for name, info in self._dependencies.items() if info.required]
                all_required_ready = all(results.get(name, False) for name in required_deps)
                
                if all_required_ready:
                    logger.info("✅ All required dependencies are ready")
                    return True
            else:
                # Проверяем все зависимости
                if all(results.values()):
                    logger.info("✅ All dependencies are ready")
                    return True
            
            # Ждем перед следующей проверкой
            await asyncio.sleep(5)
        
        logger.error(f"❌ Timeout waiting for dependencies after {timeout}s")
        return False
    
    def get_dependency_status(self) -> Dict[str, Dict[str, Any]]:
        """Возвращает статус всех зависимостей"""
        
        status = {}
        for name, info in self._dependencies.items():
            status[name] = {
                "type": info.type.value,
                "status": info.status.value,
                "required": info.required,
                "last_check": info.last_check.isoformat() if info.last_check else None,
                "retry_count": info.retry_count,
                "max_retries": info.max_retries,
                "error_message": info.error_message,
                "dependencies": info.dependencies
            }
        
        return status
    
    def start_continuous_monitoring(self):
        """Запускает непрерывный мониторинг зависимостей"""
        
        logger.info("🔄 Starting continuous dependency monitoring")
        
        for dep_name, dep_info in self._dependencies.items():
            task = asyncio.create_task(self._monitoring_loop(dep_name))
            self._check_tasks[dep_name] = task
    
    async def _monitoring_loop(self, dep_name: str):
        """Цикл мониторинга для одной зависимости"""
        
        dep_info = self._dependencies[dep_name]
        
        while not self._shutdown_requested:
            try:
                await asyncio.sleep(dep_info.check_interval)
                
                if not self._shutdown_requested:
                    await self._check_single_dependency(dep_name)
                    
            except Exception as e:
                logger.error(f"Error in monitoring loop for {dep_name}: {e}")
                await asyncio.sleep(dep_info.check_interval)
    
    async def stop_monitoring(self):
        """Останавливает мониторинг зависимостей"""
        
        logger.info("🛑 Stopping dependency monitoring")
        self._shutdown_requested = True
        
        # Отменяем все задачи мониторинга
        for task in self._check_tasks.values():
            task.cancel()
        
        # Ждем завершения задач
        if self._check_tasks:
            await asyncio.gather(*self._check_tasks.values(), return_exceptions=True)
        
        self._check_tasks.clear()
    
    # Методы проверки конкретных зависимостей
    
    async def _check_postgresql(self) -> bool:
        """Проверка подключения к PostgreSQL"""
        try:
            from ..core.database import engine
            
            # Пытаемся выполнить простой запрос
            with engine.connect() as conn:
                result = conn.execute("SELECT 1")
                return result.fetchone() is not None
                
        except Exception as e:
            logger.debug(f"PostgreSQL check failed: {e}")
            return False
    
    async def _check_redis(self) -> bool:
        """Проверка подключения к Redis"""
        try:
            from ..core.cache import cache_service
            
            # Проверяем подключение через cache_service
            if cache_service.redis_client and cache_service._initialized:
                await cache_service.redis_client.ping()
                return True
            else:
                # Пытаемся переподключиться
                await cache_service.initialize()
                return cache_service._initialized
                
        except Exception as e:
            logger.debug(f"Redis check failed: {e}")
            return False
    
    async def _check_chromadb(self) -> bool:
        """Проверка ChromaDB"""
        try:
            from ..services.vector_store_service import vector_store_service
            
            # Проверяем готовность vector store
            return vector_store_service.is_ready()
            
        except Exception as e:
            logger.debug(f"ChromaDB check failed: {e}")
            return False
    
    async def _check_ai_model_file(self) -> bool:
        """Проверка наличия файла AI модели"""
        try:
            from ..core.config import settings
            import os
            
            # Проверяем наличие файла модели
            model_path = getattr(settings, 'MODEL_PATH', '/app/models/vistral-24b-v0.1.Q4_K_M.gguf')
            
            if os.path.exists(model_path):
                # Проверяем размер файла (должен быть больше 1GB)
                file_size = os.path.getsize(model_path)
                return file_size > 1024 * 1024 * 1024  # 1GB
            
            return False
            
        except Exception as e:
            logger.debug(f"AI model file check failed: {e}")
            return False
    
    async def _check_embeddings_model(self) -> bool:
        """Проверка модели embeddings"""
        try:
            from ..services.embeddings_service import embeddings_service
            
            # Проверяем загружена ли модель embeddings
            return hasattr(embeddings_service, '_model_loaded') and embeddings_service._model_loaded
            
        except Exception as e:
            logger.debug(f"Embeddings model check failed: {e}")
            return False


# Глобальный экземпляр менеджера зависимостей
dependency_manager = DependencyManager()