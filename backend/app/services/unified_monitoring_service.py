"""
Unified Monitoring Service - система мониторинга для унифицированных AI-сервисов
Собирает метрики производительности, health checks и интегрируется с Prometheus
"""

import logging
import time
import asyncio
import psutil
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import deque
import json

from ..core.config import settings
from .service_manager import service_manager, ServiceStatus
from .unified_llm_service import unified_llm_service
from .unified_rag_service import unified_rag_service

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Точка метрики"""
    timestamp: datetime
    value: float
    labels: Dict[str, str]


@dataclass
class AlertRule:
    """Правило алерта"""
    name: str
    metric: str
    condition: str  # "gt", "lt", "eq"
    threshold: float
    duration: int  # Секунды
    severity: str  # "critical", "warning", "info"
    enabled: bool = True


@dataclass
class Alert:
    """Активный алерт"""
    rule_name: str
    message: str
    severity: str
    started_at: datetime
    last_triggered: datetime
    count: int


class MetricsCollector:
    """Сборщик метрик"""
    
    def __init__(self, max_points: int = 1000):
        self._metrics: Dict[str, deque] = {}
        self._max_points = max_points
    
    def add_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """Добавляет точку метрики"""
        if name not in self._metrics:
            self._metrics[name] = deque(maxlen=self._max_points)
        
        point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            labels=labels or {}
        )
        
        self._metrics[name].append(point)
    
    def get_metric_history(self, name: str, duration: timedelta = None) -> List[MetricPoint]:
        """Получает историю метрики"""
        if name not in self._metrics:
            return []
        
        points = list(self._metrics[name])
        
        if duration:
            cutoff_time = datetime.now() - duration
            points = [p for p in points if p.timestamp >= cutoff_time]
        
        return points
    
    def get_latest_value(self, name: str) -> Optional[float]:
        """Получает последнее значение метрики"""
        if name not in self._metrics or not self._metrics[name]:
            return None
        
        return self._metrics[name][-1].value
    
    def get_average(self, name: str, duration: timedelta = None) -> Optional[float]:
        """Получает среднее значение метрики"""
        points = self.get_metric_history(name, duration)
        if not points:
            return None
        
        return sum(p.value for p in points) / len(points)


class AlertManager:
    """Менеджер алертов"""
    
    def __init__(self):
        self._rules: Dict[str, AlertRule] = {}
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: List[Alert] = []
        self._max_history = 1000
        
        # Загружаем правила по умолчанию
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Загружает правила алертов по умолчанию"""
        
        default_rules = [
            AlertRule(
                name="high_error_rate",
                metric="llm_error_rate",
                condition="gt",
                threshold=0.1,  # 10%
                duration=300,   # 5 минут
                severity="critical"
            ),
            AlertRule(
                name="slow_response_time",
                metric="llm_p95_response_time",
                condition="gt",
                threshold=30.0,  # 30 секунд
                duration=180,    # 3 минуты
                severity="warning"
            ),
            AlertRule(
                name="high_queue_length",
                metric="llm_queue_length",
                condition="gt",
                threshold=20,
                duration=120,    # 2 минуты
                severity="warning"
            ),
            AlertRule(
                name="low_cache_hit_rate",
                metric="rag_cache_hit_rate",
                condition="lt",
                threshold=0.3,   # 30%
                duration=600,    # 10 минут
                severity="info"
            ),
            AlertRule(
                name="high_memory_usage",
                metric="system_memory_usage_percent",
                condition="gt",
                threshold=85.0,  # 85%
                duration=300,    # 5 минут
                severity="warning"
            ),
            AlertRule(
                name="service_unhealthy",
                metric="service_health_score",
                condition="lt",
                threshold=0.8,   # 80%
                duration=60,     # 1 минута
                severity="critical"
            )
        ]
        
        for rule in default_rules:
            self._rules[rule.name] = rule
    
    def add_rule(self, rule: AlertRule):
        """Добавляет правило алерта"""
        self._rules[rule.name] = rule
    
    def remove_rule(self, rule_name: str):
        """Удаляет правило алерта"""
        if rule_name in self._rules:
            del self._rules[rule_name]
        
        # Закрываем активный алерт если есть
        if rule_name in self._active_alerts:
            self._close_alert(rule_name)
    
    def check_alerts(self, metrics_collector: MetricsCollector):
        """Проверяет все правила алертов"""
        
        for rule_name, rule in self._rules.items():
            if not rule.enabled:
                continue
            
            try:
                self._check_single_rule(rule, metrics_collector)
            except Exception as e:
                logger.error("❌ Ошибка проверки правила %s: %s", rule_name, e)
    
    def _check_single_rule(self, rule: AlertRule, metrics_collector: MetricsCollector):
        """Проверяет одно правило алерта"""
        
        # Получаем значения метрики за период duration
        duration = timedelta(seconds=rule.duration)
        points = metrics_collector.get_metric_history(rule.metric, duration)
        
        if not points:
            return
        
        # Проверяем условие
        triggered = False
        latest_value = points[-1].value
        
        if rule.condition == "gt" and latest_value > rule.threshold:
            triggered = True
        elif rule.condition == "lt" and latest_value < rule.threshold:
            triggered = True
        elif rule.condition == "eq" and abs(latest_value - rule.threshold) < 0.001:
            triggered = True
        
        if triggered:
            # Проверяем, что условие выполняется достаточно долго
            violation_start = None
            for point in reversed(points):
                if rule.condition == "gt" and point.value <= rule.threshold:
                    break
                elif rule.condition == "lt" and point.value >= rule.threshold:
                    break
                elif rule.condition == "eq" and abs(point.value - rule.threshold) >= 0.001:
                    break
                violation_start = point.timestamp
            
            if violation_start and (datetime.now() - violation_start).total_seconds() >= rule.duration:
                self._trigger_alert(rule, latest_value)
        else:
            # Закрываем алерт если он был активен
            if rule.name in self._active_alerts:
                self._close_alert(rule.name)
    
    def _trigger_alert(self, rule: AlertRule, current_value: float):
        """Запускает алерт"""
        
        if rule.name in self._active_alerts:
            # Обновляем существующий алерт
            alert = self._active_alerts[rule.name]
            alert.last_triggered = datetime.now()
            alert.count += 1
        else:
            # Создаем новый алерт
            message = f"{rule.metric} {rule.condition} {rule.threshold} (current: {current_value:.2f})"
            
            alert = Alert(
                rule_name=rule.name,
                message=message,
                severity=rule.severity,
                started_at=datetime.now(),
                last_triggered=datetime.now(),
                count=1
            )
            
            self._active_alerts[rule.name] = alert
            logger.warning("🚨 Алерт активирован: %s - %s", rule.name, message)
    
    def _close_alert(self, rule_name: str):
        """Закрывает алерт"""
        
        if rule_name in self._active_alerts:
            alert = self._active_alerts.pop(rule_name)
            self._alert_history.append(alert)
            
            # Ограничиваем размер истории
            if len(self._alert_history) > self._max_history:
                self._alert_history = self._alert_history[-self._max_history:]
            
            logger.info("✅ Алерт закрыт: %s", rule_name)
    
    def get_active_alerts(self) -> List[Alert]:
        """Возвращает активные алерты"""
        return list(self._active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Возвращает историю алертов"""
        return self._alert_history[-limit:]


class UnifiedMonitoringService:
    """Единая система мониторинга для AI-сервисов"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        
        # Настройки
        self._collection_interval = getattr(settings, "MONITORING_COLLECTION_INTERVAL", 30)
        self._alert_check_interval = getattr(settings, "MONITORING_ALERT_CHECK_INTERVAL", 60)
        
        # Фоновые задачи
        self._background_tasks: List[asyncio.Task] = []
        self._shutdown_requested = False
        
        # Статистика
        self._stats = {
            "metrics_collected": 0,
            "alerts_triggered": 0,
            "collection_errors": 0,
            "last_collection": None,
            "uptime": time.time()
        }
    
    async def initialize(self):
        """Инициализирует систему мониторинга"""
        try:
            logger.info("🚀 Инициализация UnifiedMonitoringService...")
            
            # Запускаем фоновые задачи
            await self._start_background_tasks()
            
            logger.info("✅ UnifiedMonitoringService инициализирован успешно")
            
        except Exception as e:
            logger.error("❌ Ошибка инициализации UnifiedMonitoringService: %s", e)
            raise
    
    async def _start_background_tasks(self):
        """Запускает фоновые задачи"""
        
        # Задача сбора метрик
        metrics_task = asyncio.create_task(self._metrics_collection_loop())
        self._background_tasks.append(metrics_task)
        
        # Задача проверки алертов
        alerts_task = asyncio.create_task(self._alert_check_loop())
        self._background_tasks.append(alerts_task)
        
        logger.info("🔄 Фоновые задачи мониторинга запущены")
    
    async def _metrics_collection_loop(self):
        """Цикл сбора метрик"""
        
        while not self._shutdown_requested:
            try:
                await self._collect_all_metrics()
                await asyncio.sleep(self._collection_interval)
            except Exception as e:
                logger.error("❌ Ошибка сбора метрик: %s", e)
                self._stats["collection_errors"] += 1
                await asyncio.sleep(self._collection_interval)
    
    async def _alert_check_loop(self):
        """Цикл проверки алертов"""
        
        while not self._shutdown_requested:
            try:
                self.alert_manager.check_alerts(self.metrics_collector)
                await asyncio.sleep(self._alert_check_interval)
            except Exception as e:
                logger.error("❌ Ошибка проверки алертов: %s", e)
                await asyncio.sleep(self._alert_check_interval)
    
    async def _collect_all_metrics(self):
        """Собирает все метрики"""
        
        try:
            # Метрики LLM сервиса
            await self._collect_llm_metrics()
            
            # Метрики RAG сервиса
            await self._collect_rag_metrics()
            
            # Системные метрики
            await self._collect_system_metrics()
            
            # Метрики ServiceManager
            await self._collect_service_manager_metrics()
            
            self._stats["metrics_collected"] += 1
            self._stats["last_collection"] = datetime.now()
            
        except Exception as e:
            logger.error("❌ Ошибка сбора метрик: %s", e)
            self._stats["collection_errors"] += 1
    
    async def _collect_llm_metrics(self):
        """Собирает метрики LLM сервиса"""
        
        try:
            if unified_llm_service.is_model_loaded():
                metrics = unified_llm_service.get_metrics()
                
                self.metrics_collector.add_metric("llm_requests_per_minute", metrics.requests_per_minute)
                self.metrics_collector.add_metric("llm_average_response_time", metrics.average_response_time)
                self.metrics_collector.add_metric("llm_p95_response_time", metrics.p95_response_time)
                self.metrics_collector.add_metric("llm_error_rate", metrics.error_rate)
                self.metrics_collector.add_metric("llm_queue_length", metrics.queue_length)
                self.metrics_collector.add_metric("llm_concurrent_requests", metrics.concurrent_requests)
                self.metrics_collector.add_metric("llm_total_requests", metrics.total_requests)
                self.metrics_collector.add_metric("llm_successful_requests", metrics.successful_requests)
                self.metrics_collector.add_metric("llm_failed_requests", metrics.failed_requests)
                
        except Exception as e:
            logger.error("❌ Ошибка сбора метрик LLM: %s", e)
    
    async def _collect_rag_metrics(self):
        """Собирает метрики RAG сервиса"""
        
        try:
            if unified_rag_service.is_ready():
                metrics = unified_rag_service.get_metrics()
                
                self.metrics_collector.add_metric("rag_search_time_avg", metrics.search_time_avg)
                self.metrics_collector.add_metric("rag_generation_time_avg", metrics.generation_time_avg)
                self.metrics_collector.add_metric("rag_cache_hit_rate", metrics.cache_hit_rate)
                self.metrics_collector.add_metric("rag_vector_store_size", metrics.vector_store_size)
                self.metrics_collector.add_metric("rag_embedding_generation_time", metrics.embedding_generation_time)
                self.metrics_collector.add_metric("rag_total_searches", metrics.total_searches)
                self.metrics_collector.add_metric("rag_successful_searches", metrics.successful_searches)
                self.metrics_collector.add_metric("rag_failed_searches", metrics.failed_searches)
                
        except Exception as e:
            logger.error("❌ Ошибка сбора метрик RAG: %s", e)
    
    async def _collect_system_metrics(self):
        """Собирает системные метрики"""
        
        try:
            # CPU и память
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            self.metrics_collector.add_metric("system_cpu_usage_percent", cpu_percent)
            self.metrics_collector.add_metric("system_memory_usage_percent", memory.percent)
            self.metrics_collector.add_metric("system_memory_used_mb", memory.used / 1024 / 1024)
            self.metrics_collector.add_metric("system_disk_usage_percent", disk.percent)
            
            # Сетевые соединения
            connections = len(psutil.net_connections())
            self.metrics_collector.add_metric("system_network_connections", connections)
            
        except Exception as e:
            logger.error("❌ Ошибка сбора системных метрик: %s", e)
    
    async def _collect_service_manager_metrics(self):
        """Собирает метрики ServiceManager"""
        
        try:
            system_health = service_manager.get_service_status()
            
            # Общие метрики здоровья
            health_score = system_health.healthy_services / system_health.total_services if system_health.total_services > 0 else 0
            self.metrics_collector.add_metric("service_health_score", health_score)
            self.metrics_collector.add_metric("service_total_count", system_health.total_services)
            self.metrics_collector.add_metric("service_healthy_count", system_health.healthy_services)
            self.metrics_collector.add_metric("service_degraded_count", system_health.degraded_services)
            self.metrics_collector.add_metric("service_unhealthy_count", system_health.unhealthy_services)
            self.metrics_collector.add_metric("service_uptime", system_health.uptime)
            
            # Метрики отдельных сервисов
            for service_name, service_info in system_health.services.items():
                labels = {"service": service_name}
                
                status_value = 1 if service_info.status == ServiceStatus.HEALTHY else 0
                self.metrics_collector.add_metric(f"service_status", status_value, labels)
                self.metrics_collector.add_metric(f"service_error_count", service_info.error_count, labels)
                self.metrics_collector.add_metric(f"service_restart_count", service_info.restart_count, labels)
                
                if service_info.initialization_time:
                    self.metrics_collector.add_metric(f"service_initialization_time", service_info.initialization_time, labels)
                
        except Exception as e:
            logger.error("❌ Ошибка сбора метрик ServiceManager: %s", e)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Возвращает данные для дашборда"""
        
        # Последние значения ключевых метрик
        key_metrics = {
            "llm_requests_per_minute": self.metrics_collector.get_latest_value("llm_requests_per_minute") or 0,
            "llm_average_response_time": self.metrics_collector.get_latest_value("llm_average_response_time") or 0,
            "llm_error_rate": self.metrics_collector.get_latest_value("llm_error_rate") or 0,
            "llm_queue_length": self.metrics_collector.get_latest_value("llm_queue_length") or 0,
            "rag_cache_hit_rate": self.metrics_collector.get_latest_value("rag_cache_hit_rate") or 0,
            "rag_vector_store_size": self.metrics_collector.get_latest_value("rag_vector_store_size") or 0,
            "system_cpu_usage_percent": self.metrics_collector.get_latest_value("system_cpu_usage_percent") or 0,
            "system_memory_usage_percent": self.metrics_collector.get_latest_value("system_memory_usage_percent") or 0,
            "service_health_score": self.metrics_collector.get_latest_value("service_health_score") or 0
        }
        
        # Активные алерты
        active_alerts = [asdict(alert) for alert in self.alert_manager.get_active_alerts()]
        
        # Статус сервисов
        system_health = service_manager.get_service_status()
        
        return {
            "metrics": key_metrics,
            "alerts": {
                "active": active_alerts,
                "count": len(active_alerts)
            },
            "services": {
                "total": system_health.total_services,
                "healthy": system_health.healthy_services,
                "degraded": system_health.degraded_services,
                "unhealthy": system_health.unhealthy_services,
                "status": system_health.status.value
            },
            "system": {
                "uptime": time.time() - self._stats["uptime"],
                "metrics_collected": self._stats["metrics_collected"],
                "collection_errors": self._stats["collection_errors"],
                "last_collection": self._stats["last_collection"].isoformat() if self._stats["last_collection"] else None
            }
        }
    
    def get_metric_history(self, metric_name: str, duration_minutes: int = 60) -> List[Dict[str, Any]]:
        """Возвращает историю метрики"""
        
        duration = timedelta(minutes=duration_minutes)
        points = self.metrics_collector.get_metric_history(metric_name, duration)
        
        return [
            {
                "timestamp": point.timestamp.isoformat(),
                "value": point.value,
                "labels": point.labels
            }
            for point in points
        ]
    
    def get_prometheus_metrics(self) -> str:
        """Возвращает метрики в формате Prometheus"""
        
        lines = []
        
        # Добавляем все метрики
        for metric_name, points in self.metrics_collector._metrics.items():
            if not points:
                continue
            
            latest_point = points[-1]
            
            # Очищаем имя метрики для Prometheus
            prometheus_name = metric_name.replace(".", "_")
            
            # Добавляем метрику
            if latest_point.labels:
                labels_str = ",".join(f'{k}="{v}"' for k, v in latest_point.labels.items())
                lines.append(f'{prometheus_name}{{{labels_str}}} {latest_point.value}')
            else:
                lines.append(f'{prometheus_name} {latest_point.value}')
        
        return "\n".join(lines)
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья системы мониторинга"""
        
        return {
            "status": "healthy" if not self._shutdown_requested else "shutting_down",
            "background_tasks": len(self._background_tasks),
            "metrics_count": len(self.metrics_collector._metrics),
            "active_alerts": len(self.alert_manager.get_active_alerts()),
            "stats": self._stats.copy()
        }
    
    async def graceful_shutdown(self):
        """Graceful shutdown системы мониторинга"""
        
        logger.info("🔄 Начинаем graceful shutdown UnifiedMonitoringService...")
        self._shutdown_requested = True
        
        # Останавливаем фоновые задачи
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        logger.info("✅ UnifiedMonitoringService успешно остановлен")


# Глобальный экземпляр сервиса
unified_monitoring_service = UnifiedMonitoringService()