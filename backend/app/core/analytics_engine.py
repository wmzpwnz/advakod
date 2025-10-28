"""
Система аналитики и мониторинга для ИИ-Юриста
Отслеживает производительность, качество ответов и пользовательскую активность
"""

import asyncio
import time
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)


@dataclass
class QueryAnalytics:
    """Аналитика запроса"""
    query_id: str
    user_id: Optional[str]
    query_text: str
    response_time: float
    quality_score: float
    confidence: float
    legal_field: str
    complexity: str
    timestamp: float
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class PerformanceMetrics:
    """Метрики производительности"""
    total_requests: int
    average_response_time: float
    cache_hit_rate: float
    error_rate: float
    throughput: float  # запросов в минуту
    uptime: float


@dataclass
class QualityMetrics:
    """Метрики качества"""
    average_quality_score: float
    validation_success_rate: float
    user_satisfaction: float
    legal_accuracy: float
    response_completeness: float


class AnalyticsEngine:
    """Движок аналитики"""
    
    def __init__(self):
        self.queries = deque(maxlen=10000)  # Храним последние 10k запросов
        self.user_sessions = defaultdict(list)
        self.performance_history = deque(maxlen=1000)
        self.quality_history = deque(maxlen=1000)
        
        # Статистика по отраслям права
        self.legal_field_stats = defaultdict(int)
        
        # Статистика по сложности
        self.complexity_stats = defaultdict(int)
        
        # Временные метрики
        self.start_time = time.time()
        self.last_reset = time.time()
        
        # Алерты
        self.alerts = []
        
        # Настройки мониторинга
        self.monitoring_config = {
            "response_time_threshold": 5.0,  # секунд
            "error_rate_threshold": 0.05,    # 5%
            "quality_score_threshold": 0.7,   # 70%
            "cache_hit_rate_threshold": 0.3,  # 30%
            "throughput_threshold": 10.0      # запросов в минуту
        }
    
    def record_query(self, query_analytics: QueryAnalytics):
        """Записывает аналитику запроса"""
        self.queries.append(query_analytics)
        
        # Обновляем статистику пользователя
        if query_analytics.user_id:
            self.user_sessions[query_analytics.user_id].append(query_analytics)
        
        # Обновляем статистику по отраслям права
        self.legal_field_stats[query_analytics.legal_field] += 1
        
        # Обновляем статистику по сложности
        self.complexity_stats[query_analytics.complexity] += 1
        
        # Проверяем алерты
        self._check_alerts()
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Возвращает метрики производительности"""
        current_time = time.time()
        
        # Фильтруем запросы за последний час
        recent_queries = [
            q for q in self.queries 
            if current_time - q.timestamp < 3600
        ]
        
        if not recent_queries:
            return PerformanceMetrics(
                total_requests=0,
                average_response_time=0.0,
                cache_hit_rate=0.0,
                error_rate=0.0,
                throughput=0.0,
                uptime=current_time - self.start_time
            )
        
        # Вычисляем метрики
        total_requests = len(recent_queries)
        response_times = [q.response_time for q in recent_queries]
        average_response_time = statistics.mean(response_times) if response_times else 0.0
        
        # Cache hit rate (упрощенная версия)
        cache_hits = sum(1 for q in recent_queries if q.response_time < 1.0)
        cache_hit_rate = cache_hits / total_requests if total_requests > 0 else 0.0
        
        # Error rate (упрощенная версия)
        errors = sum(1 for q in recent_queries if q.quality_score < 0.3)
        error_rate = errors / total_requests if total_requests > 0 else 0.0
        
        # Throughput (запросов в минуту)
        throughput = total_requests / 60.0
        
        return PerformanceMetrics(
            total_requests=total_requests,
            average_response_time=average_response_time,
            cache_hit_rate=cache_hit_rate,
            error_rate=error_rate,
            throughput=throughput,
            uptime=current_time - self.start_time
        )
    
    def get_quality_metrics(self) -> QualityMetrics:
        """Возвращает метрики качества"""
        if not self.queries:
            return QualityMetrics(
                average_quality_score=0.0,
                validation_success_rate=0.0,
                user_satisfaction=0.0,
                legal_accuracy=0.0,
                response_completeness=0.0
            )
        
        # Фильтруем запросы за последний час
        current_time = time.time()
        recent_queries = [
            q for q in self.queries 
            if current_time - q.timestamp < 3600
        ]
        
        if not recent_queries:
            return QualityMetrics(
                average_quality_score=0.0,
                validation_success_rate=0.0,
                user_satisfaction=0.0,
                legal_accuracy=0.0,
                response_completeness=0.0
            )
        
        # Вычисляем метрики качества
        quality_scores = [q.quality_score for q in recent_queries]
        average_quality_score = statistics.mean(quality_scores) if quality_scores else 0.0
        
        # Validation success rate
        validation_successes = sum(1 for q in recent_queries if q.quality_score > 0.7)
        validation_success_rate = validation_successes / len(recent_queries) if recent_queries else 0.0
        
        # User satisfaction (на основе confidence)
        confidence_scores = [q.confidence for q in recent_queries]
        user_satisfaction = statistics.mean(confidence_scores) if confidence_scores else 0.0
        
        # Legal accuracy (упрощенная версия)
        legal_accuracy = sum(1 for q in recent_queries if q.legal_field != "general") / len(recent_queries)
        
        # Response completeness (упрощенная версия)
        response_completeness = sum(1 for q in recent_queries if q.quality_score > 0.5) / len(recent_queries)
        
        return QualityMetrics(
            average_quality_score=average_quality_score,
            validation_success_rate=validation_success_rate,
            user_satisfaction=user_satisfaction,
            legal_accuracy=legal_accuracy,
            response_completeness=response_completeness
        )
    
    def get_legal_field_analytics(self) -> Dict[str, Any]:
        """Возвращает аналитику по отраслям права"""
        total_queries = sum(self.legal_field_stats.values())
        
        if total_queries == 0:
            return {"fields": {}, "total": 0}
        
        field_percentages = {
            field: (count / total_queries) * 100
            for field, count in self.legal_field_stats.items()
        }
        
        # Сортируем по популярности
        sorted_fields = sorted(
            field_percentages.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            "fields": dict(sorted_fields),
            "total": total_queries,
            "top_field": sorted_fields[0][0] if sorted_fields else None
        }
    
    def get_complexity_analytics(self) -> Dict[str, Any]:
        """Возвращает аналитику по сложности запросов"""
        total_queries = sum(self.complexity_stats.values())
        
        if total_queries == 0:
            return {"complexity": {}, "total": 0}
        
        complexity_percentages = {
            complexity: (count / total_queries) * 100
            for complexity, count in self.complexity_stats.items()
        }
        
        return {
            "complexity": complexity_percentages,
            "total": total_queries
        }
    
    def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """Возвращает аналитику пользователя"""
        if user_id not in self.user_sessions:
            return {"error": "User not found"}
        
        user_queries = self.user_sessions[user_id]
        
        if not user_queries:
            return {"error": "No queries found for user"}
        
        # Вычисляем метрики пользователя
        total_queries = len(user_queries)
        avg_response_time = statistics.mean([q.response_time for q in user_queries])
        avg_quality_score = statistics.mean([q.quality_score for q in user_queries])
        
        # Популярные отрасли права
        user_legal_fields = defaultdict(int)
        for q in user_queries:
            user_legal_fields[q.legal_field] += 1
        
        top_legal_field = max(user_legal_fields.items(), key=lambda x: x[1])[0] if user_legal_fields else None
        
        # Временная активность
        query_times = [q.timestamp for q in user_queries]
        first_query = min(query_times) if query_times else None
        last_query = max(query_times) if query_times else None
        
        return {
            "total_queries": total_queries,
            "average_response_time": avg_response_time,
            "average_quality_score": avg_quality_score,
            "top_legal_field": top_legal_field,
            "first_query": first_query,
            "last_query": last_query,
            "legal_fields": dict(user_legal_fields)
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Возвращает состояние системы"""
        performance = self.get_performance_metrics()
        quality = self.get_quality_metrics()
        
        # Определяем статус системы
        health_status = "healthy"
        issues = []
        
        if performance.average_response_time > self.monitoring_config["response_time_threshold"]:
            health_status = "degraded"
            issues.append("High response time")
        
        if performance.error_rate > self.monitoring_config["error_rate_threshold"]:
            health_status = "degraded"
            issues.append("High error rate")
        
        if quality.average_quality_score < self.monitoring_config["quality_score_threshold"]:
            health_status = "degraded"
            issues.append("Low quality score")
        
        if performance.cache_hit_rate < self.monitoring_config["cache_hit_rate_threshold"]:
            health_status = "degraded"
            issues.append("Low cache hit rate")
        
        return {
            "status": health_status,
            "issues": issues,
            "performance": asdict(performance),
            "quality": asdict(quality),
            "uptime": performance.uptime,
            "timestamp": time.time()
        }
    
    def _check_alerts(self):
        """Проверяет условия для алертов"""
        current_time = time.time()
        
        # Проверяем производительность
        performance = self.get_performance_metrics()
        
        if performance.average_response_time > self.monitoring_config["response_time_threshold"]:
            self._add_alert("high_response_time", f"Average response time: {performance.average_response_time:.2f}s")
        
        if performance.error_rate > self.monitoring_config["error_rate_threshold"]:
            self._add_alert("high_error_rate", f"Error rate: {performance.error_rate:.2%}")
        
        # Проверяем качество
        quality = self.get_quality_metrics()
        
        if quality.average_quality_score < self.monitoring_config["quality_score_threshold"]:
            self._add_alert("low_quality", f"Average quality score: {quality.average_quality_score:.2f}")
    
    def _add_alert(self, alert_type: str, message: str):
        """Добавляет алерт"""
        alert = {
            "type": alert_type,
            "message": message,
            "timestamp": time.time(),
            "severity": "warning"
        }
        
        self.alerts.append(alert)
        
        # Ограничиваем количество алертов
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-50:]
        
        logger.warning(f"Alert: {alert_type} - {message}")
    
    def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Возвращает последние алерты"""
        return self.alerts[-limit:]
    
    def clear_alerts(self):
        """Очищает алерты"""
        self.alerts.clear()
    
    def reset_statistics(self):
        """Сбрасывает статистику"""
        self.queries.clear()
        self.user_sessions.clear()
        self.performance_history.clear()
        self.quality_history.clear()
        self.legal_field_stats.clear()
        self.complexity_stats.clear()
        self.alerts.clear()
        self.last_reset = time.time()
        
        logger.info("Analytics statistics reset")
    
    def export_analytics(self, format: str = "json") -> str:
        """Экспортирует аналитику"""
        data = {
            "performance": asdict(self.get_performance_metrics()),
            "quality": asdict(self.get_quality_metrics()),
            "legal_fields": self.get_legal_field_analytics(),
            "complexity": self.get_complexity_analytics(),
            "system_health": self.get_system_health(),
            "alerts": self.get_alerts(),
            "export_timestamp": time.time()
        }
        
        if format == "json":
            return json.dumps(data, indent=2, ensure_ascii=False)
        else:
            return str(data)


# Глобальный экземпляр
analytics_engine = AnalyticsEngine()
