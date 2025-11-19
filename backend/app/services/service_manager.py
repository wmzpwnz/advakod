"""
Service Manager - централизованное управление жизненным циклом AI-сервисов
Управляет инициализацией, мониторингом и graceful shutdown всех сервисов
"""

import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from ..core.config import settings
from .unified_llm_service import unified_llm_service, ServiceHealth as LLMServiceHealth
from .unified_rag_service import unified_rag_service

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Статусы сервисов"""
    NOT_STARTED = "not_started"
    INITIALIZING = "initializing"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"
    ERROR = "error"


class ServicePriority(Enum):
    """Приоритеты загрузки сервисов"""
    CRITICAL = 1    # Должны быть загружены первыми
    HIGH = 2        # Важные сервисы
    NORMAL = 3      # Обычные сервисы
    LOW = 4         # Могут быть загружены последними


@dataclass
class ServiceInfo:
    """Информация о сервисе"""
    name: str
    instance: Any
    priority: ServicePriority
    status: ServiceStatus
    last_health_check: Optional[datetime]
    initialization_time: Optional[float]
    error_count: int
    last_error: Optional[str]
    restart_count: int
    dependencies: List[str]  # Список зависимостей
    health_check_interval: int  # Интервал проверки здоровья в секундах


@dataclass
class SystemHealth:
    """Общее состояние системы"""
    status: ServiceStatus
    total_services: int
    healthy_services: int
    degraded_services: int
    unhealthy_services: int
    last_check: datetime
    uptime: float
    services: Dict[str, ServiceInfo]


class ServiceManager:
    """Менеджер для управления жизненным циклом AI-сервисов"""
    
    def __init__(self):
        self._services: Dict[str, ServiceInfo] = {}
        self._initialization_order: List[str] = []
        self._background_tasks: List[asyncio.Task] = []
        self._shutdown_requested = False
        self._startup_time = time.time()
        
        # Настройки
        self._health_check_interval = getattr(settings, "SERVICE_HEALTH_CHECK_INTERVAL", 30)
        self._max_restart_attempts = getattr(settings, "SERVICE_MAX_RESTART_ATTEMPTS", 3)
        self._restart_delay = getattr(settings, "SERVICE_RESTART_DELAY", 5)
        
        # Статистика
        self._stats = {
            "total_initializations": 0,
            "successful_initializations": 0,
            "failed_initializations": 0,
            "total_restarts": 0,
            "successful_restarts": 0,
            "failed_restarts": 0,
            "average_initialization_time": 0.0
        }
        
        # Регистрируем сервисы
        self._register_services()
    
    def _register_services(self):
        """Регистрирует все AI-сервисы"""
        
        # Unified LLM Service - критический сервис
        self._services["unified_llm"] = ServiceInfo(
            name="unified_llm",
            instance=unified_llm_service,
            priority=ServicePriority.CRITICAL,
            status=ServiceStatus.NOT_STARTED,
            last_health_check=None,
            initialization_time=None,
            error_count=0,
            last_error=None,
            restart_count=0,
            dependencies=[],  # Нет зависимостей
            health_check_interval=30
        )
        
        # Unified RAG Service - высокий приоритет, зависит от vector store и embeddings
        self._services["unified_rag"] = ServiceInfo(
            name="unified_rag",
            instance=unified_rag_service,
            priority=ServicePriority.HIGH,
            status=ServiceStatus.NOT_STARTED,
            last_health_check=None,
            initialization_time=None,
            error_count=0,
            last_error=None,
            restart_count=0,
            dependencies=["vector_store", "embeddings"],
            health_check_interval=30
        )
        
        # Определяем порядок инициализации на основе приоритетов и зависимостей
        self._calculate_initialization_order()
    
    def _calculate_initialization_order(self):
        """Рассчитывает порядок инициализации сервисов на основе приоритетов и зависимостей"""
        
        # Сортируем по приоритету
        services_by_priority = sorted(
            self._services.items(),
            key=lambda x: x[1].priority.value
        )
        
        self._initialization_order = [name for name, _ in services_by_priority]
        
        logger.info("📋 Порядок инициализации сервисов: %s", " -> ".join(self._initialization_order))
    
    async def initialize_services(self) -> bool:
        """Инициализирует все сервисы в правильном порядке"""
        
        logger.info("🚀 Начинаем инициализацию AI-сервисов...")
        start_time = time.time()
        
        successful_count = 0
        total_count = len(self._services)
        
        for service_name in self._initialization_order:
            service_info = self._services[service_name]
            
            try:
                logger.info("🔄 Инициализация сервиса: %s (приоритет: %s)", 
                          service_name, service_info.priority.name)
                
                # Проверяем зависимости
                if not await self._check_dependencies(service_name):
                    logger.error("❌ Зависимости сервиса %s не выполнены", service_name)
                    service_info.status = ServiceStatus.ERROR
                    service_info.last_error = "Dependencies not met"
                    continue
                
                # Инициализируем сервис
                service_info.status = ServiceStatus.INITIALIZING
                init_start_time = time.time()
                
                await self._initialize_single_service(service_info)
                
                init_time = time.time() - init_start_time
                service_info.initialization_time = init_time
                service_info.status = ServiceStatus.HEALTHY
                successful_count += 1
                
                logger.info("✅ Сервис %s инициализирован за %.2f секунд", 
                          service_name, init_time)
                
                self._stats["successful_initializations"] += 1
                
            except Exception as e:
                service_info.status = ServiceStatus.ERROR
                service_info.error_count += 1
                service_info.last_error = str(e)
                
                logger.error("❌ Ошибка инициализации сервиса %s: %s", service_name, e)
                self._stats["failed_initializations"] += 1
        
        total_time = time.time() - start_time
        
        # Обновляем статистику
        self._stats["total_initializations"] += total_count
        if self._stats["successful_initializations"] > 0:
            total_init_time = self._stats["average_initialization_time"] * (self._stats["successful_initializations"] - successful_count)
            self._stats["average_initialization_time"] = (total_init_time + total_time) / self._stats["successful_initializations"]
        
        # Запускаем фоновые задачи
        await self._start_background_tasks()
        
        success_rate = successful_count / total_count
        logger.info("🎯 Инициализация завершена: %d/%d сервисов (%.1f%%) за %.2f секунд", 
                   successful_count, total_count, success_rate * 100, total_time)
        
        return success_rate >= 0.5  # Считаем успешным если инициализировано >= 50% сервисов
    
    async def _check_dependencies(self, service_name: str) -> bool:
        """Проверяет, что все зависимости сервиса выполнены"""
        
        service_info = self._services[service_name]
        
        for dependency in service_info.dependencies:
            if dependency in self._services:
                dep_service = self._services[dependency]
                if dep_service.status not in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]:
                    logger.warning("⚠️ Зависимость %s для сервиса %s не готова (статус: %s)", 
                                 dependency, service_name, dep_service.status.value)
                    return False
            else:
                # Зависимость не является управляемым сервисом - используем dependency_manager
                if not await self._check_external_dependency_via_manager(dependency):
                    logger.warning("⚠️ Внешняя зависимость %s для сервиса %s не готова", 
                                 dependency, service_name)
                    return False
        
        return True
    
    async def _check_external_dependency_via_manager(self, dependency: str) -> bool:
        """Проверяет внешние зависимости через dependency_manager"""
        
        try:
            from ..core.dependency_manager import dependency_manager
            
            # Получаем статус зависимости из dependency_manager
            dep_status = dependency_manager.get_dependency_status()
            
            # Маппинг имен зависимостей
            dependency_mapping = {
                "vector_store": "chromadb",
                "embeddings": "embeddings_model",
                "database": "postgresql",
                "cache": "redis"
            }
            
            mapped_name = dependency_mapping.get(dependency, dependency)
            
            if mapped_name in dep_status:
                status = dep_status[mapped_name]["status"]
                return status == "available"
            else:
                # Fallback на старый метод проверки
                return await self._check_external_dependency(dependency)
                
        except Exception as e:
            logger.warning(f"Error checking dependency {dependency} via manager: {e}")
            # Fallback на старый метод проверки
            return await self._check_external_dependency(dependency)
    
    async def _check_external_dependency(self, dependency: str) -> bool:
        """Проверяет внешние зависимости"""
        
        if dependency == "vector_store":
            # Проверяем готовность vector store
            try:
                from .vector_store_service import vector_store_service
                return vector_store_service.is_ready()
            except Exception:
                return False
        
        elif dependency == "embeddings":
            # Проверяем готовность embeddings service
            try:
                from .embeddings_service import embeddings_service
                return hasattr(embeddings_service, '_model_loaded') and embeddings_service._model_loaded
            except Exception:
                return False
        
        return True
    
    async def _initialize_single_service(self, service_info: ServiceInfo):
        """Инициализирует один сервис"""
        
        service_instance = service_info.instance
        
        # Проверяем наличие метода initialize
        if hasattr(service_instance, 'initialize'):
            await service_instance.initialize()
        else:
            logger.warning("⚠️ Сервис %s не имеет метода initialize", service_info.name)
    
    async def _start_background_tasks(self):
        """Запускает фоновые задачи"""
        
        # Задача мониторинга здоровья сервисов
        health_monitor = asyncio.create_task(self._health_monitor_loop())
        self._background_tasks.append(health_monitor)
        
        # Задача автоматического восстановления
        recovery_task = asyncio.create_task(self._auto_recovery_loop())
        self._background_tasks.append(recovery_task)
        
        logger.info("🔄 Фоновые задачи ServiceManager запущены")
    
    async def _health_monitor_loop(self):
        """Цикл мониторинга здоровья сервисов"""
        
        while not self._shutdown_requested:
            try:
                await self._check_all_services_health()
                await asyncio.sleep(self._health_check_interval)
            except Exception as e:
                logger.error("❌ Ошибка в мониторе здоровья: %s", e)
                await asyncio.sleep(self._health_check_interval)
    
    async def _auto_recovery_loop(self):
        """Цикл автоматического восстановления сервисов"""
        
        while not self._shutdown_requested:
            try:
                await self._attempt_service_recovery()
                await asyncio.sleep(60)  # Проверяем каждую минуту
            except Exception as e:
                logger.error("❌ Ошибка в системе восстановления: %s", e)
                await asyncio.sleep(60)
    
    async def _check_all_services_health(self):
        """Проверяет здоровье всех сервисов"""
        
        for service_name, service_info in self._services.items():
            try:
                await self._check_service_health(service_info)
            except Exception as e:
                logger.error("❌ Ошибка проверки здоровья сервиса %s: %s", service_name, e)
                service_info.status = ServiceStatus.ERROR
                service_info.error_count += 1
                service_info.last_error = str(e)
    
    async def _check_service_health(self, service_info: ServiceInfo):
        """Проверяет здоровье одного сервиса"""
        
        service_instance = service_info.instance
        
        # Проверяем наличие метода health_check
        if hasattr(service_instance, 'health_check'):
            health_result = await service_instance.health_check()
            
            if isinstance(health_result, dict):
                status_str = health_result.get("status", "unknown")
                if status_str == "healthy":
                    service_info.status = ServiceStatus.HEALTHY
                elif status_str == "degraded":
                    service_info.status = ServiceStatus.DEGRADED
                else:
                    service_info.status = ServiceStatus.UNHEALTHY
            else:
                # Если health_check возвращает не dict, считаем сервис здоровым
                service_info.status = ServiceStatus.HEALTHY
        
        elif hasattr(service_instance, 'is_ready'):
            # Fallback на метод is_ready
            if service_instance.is_ready():
                service_info.status = ServiceStatus.HEALTHY
            else:
                service_info.status = ServiceStatus.UNHEALTHY
        
        else:
            # Если нет методов проверки, считаем сервис здоровым если он инициализирован
            if service_info.status == ServiceStatus.INITIALIZING:
                service_info.status = ServiceStatus.HEALTHY
        
        service_info.last_health_check = datetime.now()
    
    async def _attempt_service_recovery(self):
        """Пытается восстановить неработающие сервисы"""
        
        for service_name, service_info in self._services.items():
            if (service_info.status in [ServiceStatus.UNHEALTHY, ServiceStatus.ERROR] and
                service_info.restart_count < self._max_restart_attempts):
                
                logger.info("🔄 Попытка восстановления сервиса: %s (попытка %d/%d)", 
                          service_name, service_info.restart_count + 1, self._max_restart_attempts)
                
                try:
                    await self._restart_service(service_name)
                except Exception as e:
                    logger.error("❌ Ошибка восстановления сервиса %s: %s", service_name, e)
    
    async def restart_service(self, service_name: str) -> bool:
        """Перезапускает указанный сервис"""
        
        if service_name not in self._services:
            logger.error("❌ Сервис %s не найден", service_name)
            return False
        
        return await self._restart_service(service_name)
    
    async def _restart_service(self, service_name: str) -> bool:
        """Внутренний метод перезапуска сервиса"""
        
        service_info = self._services[service_name]
        
        try:
            service_info.status = ServiceStatus.SHUTTING_DOWN
            
            # Graceful shutdown если поддерживается
            if hasattr(service_info.instance, 'graceful_shutdown'):
                await service_info.instance.graceful_shutdown()
            
            # Ждем немного перед перезапуском
            await asyncio.sleep(self._restart_delay)
            
            # Перезапускаем
            service_info.status = ServiceStatus.INITIALIZING
            await self._initialize_single_service(service_info)
            
            service_info.status = ServiceStatus.HEALTHY
            service_info.restart_count += 1
            service_info.error_count = 0  # Сбрасываем счетчик ошибок
            service_info.last_error = None
            
            logger.info("✅ Сервис %s успешно перезапущен", service_name)
            self._stats["successful_restarts"] += 1
            return True
            
        except Exception as e:
            service_info.status = ServiceStatus.ERROR
            service_info.error_count += 1
            service_info.last_error = str(e)
            
            logger.error("❌ Ошибка перезапуска сервиса %s: %s", service_name, e)
            self._stats["failed_restarts"] += 1
            return False
        
        finally:
            self._stats["total_restarts"] += 1
    
    def get_service_status(self) -> SystemHealth:
        """Возвращает статус всех сервисов"""
        
        healthy_count = sum(1 for s in self._services.values() if s.status == ServiceStatus.HEALTHY)
        degraded_count = sum(1 for s in self._services.values() if s.status == ServiceStatus.DEGRADED)
        unhealthy_count = sum(1 for s in self._services.values() 
                            if s.status in [ServiceStatus.UNHEALTHY, ServiceStatus.ERROR])
        
        # Определяем общий статус системы
        if unhealthy_count == 0 and degraded_count == 0:
            system_status = ServiceStatus.HEALTHY
        elif unhealthy_count == 0:
            system_status = ServiceStatus.DEGRADED
        elif healthy_count > 0:
            system_status = ServiceStatus.DEGRADED
        else:
            system_status = ServiceStatus.UNHEALTHY
        
        return SystemHealth(
            status=system_status,
            total_services=len(self._services),
            healthy_services=healthy_count,
            degraded_services=degraded_count,
            unhealthy_services=unhealthy_count,
            last_check=datetime.now(),
            uptime=time.time() - self._startup_time,
            services=self._services.copy()
        )
    
    def get_service_info(self, service_name: str) -> Optional[ServiceInfo]:
        """Возвращает информацию о конкретном сервисе"""
        return self._services.get(service_name)
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику ServiceManager"""
        return {
            "initialization": self._stats.copy(),
            "services": {
                name: {
                    "status": info.status.value,
                    "priority": info.priority.name,
                    "error_count": info.error_count,
                    "restart_count": info.restart_count,
                    "initialization_time": info.initialization_time,
                    "last_error": info.last_error
                }
                for name, info in self._services.items()
            },
            "system": {
                "uptime": time.time() - self._startup_time,
                "background_tasks": len(self._background_tasks),
                "shutdown_requested": self._shutdown_requested
            }
        }
    
    async def shutdown_services(self) -> bool:
        """Graceful shutdown всех сервисов"""
        
        logger.info("🔄 Начинаем graceful shutdown AI-сервисов...")
        self._shutdown_requested = True
        
        # Останавливаем фоновые задачи
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Останавливаем сервисы в обратном порядке инициализации
        shutdown_order = list(reversed(self._initialization_order))
        successful_shutdowns = 0
        
        for service_name in shutdown_order:
            service_info = self._services[service_name]
            
            if service_info.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]:
                try:
                    logger.info("🔄 Остановка сервиса: %s", service_name)
                    service_info.status = ServiceStatus.SHUTTING_DOWN
                    
                    # Graceful shutdown если поддерживается
                    if hasattr(service_info.instance, 'graceful_shutdown'):
                        await service_info.instance.graceful_shutdown()
                    
                    service_info.status = ServiceStatus.STOPPED
                    successful_shutdowns += 1
                    
                    logger.info("✅ Сервис %s остановлен", service_name)
                    
                except Exception as e:
                    service_info.status = ServiceStatus.ERROR
                    service_info.last_error = str(e)
                    logger.error("❌ Ошибка остановки сервиса %s: %s", service_name, e)
        
        total_services = len([s for s in self._services.values() 
                            if s.status not in [ServiceStatus.NOT_STARTED, ServiceStatus.STOPPED]])
        
        if total_services > 0:
            success_rate = successful_shutdowns / total_services
            logger.info("🎯 Shutdown завершен: %d/%d сервисов (%.1f%%)", 
                       successful_shutdowns, total_services, success_rate * 100)
        else:
            success_rate = 1.0
            logger.info("✅ Все сервисы успешно остановлены")
        
        return success_rate >= 0.8  # Считаем успешным если остановлено >= 80% сервисов


# Глобальный экземпляр менеджера
service_manager = ServiceManager()