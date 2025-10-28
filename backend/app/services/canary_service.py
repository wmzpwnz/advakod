"""
Сервис Canary-релизов для безопасного тестирования новых версий
"""

import logging
import hashlib
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ModelStatus(Enum):
    """Статус модели"""
    ACTIVE = "active"
    CANARY = "canary"
    DEPRECATED = "deprecated"
    FAILED = "failed"

@dataclass
class ModelVersion:
    """Версия модели"""
    id: str
    name: str
    version: str
    status: ModelStatus
    created_at: datetime
    performance_metrics: Dict[str, float]
    canary_percentage: float = 0.0
    rollback_threshold: float = 0.7
    min_requests: int = 100
    evaluation_period_hours: int = 24

@dataclass
class CanaryMetrics:
    """Метрики Canary-тестирования"""
    total_requests: int
    success_rate: float
    avg_response_time: float
    error_rate: float
    user_satisfaction: float
    quality_score: float
    citation_accuracy: float
    hallucination_rate: float

class CanaryService:
    """Сервис для управления Canary-релизами"""
    
    def __init__(self):
        self.models: Dict[str, ModelVersion] = {}
        self.canary_metrics: Dict[str, CanaryMetrics] = {}
        self.rollback_triggers: List[str] = []
        self.initialized = False
        
    async def initialize(self):
        """Инициализация сервиса"""
        try:
            logger.info("🚀 Инициализация Canary сервиса...")
            
            # Создаем базовую версию модели
            base_model = ModelVersion(
                id="base_v1",
                name="Saiga Mistral 7B",
                version="1.0.0",
                status=ModelStatus.ACTIVE,
                created_at=datetime.now(),
                performance_metrics={
                    "accuracy": 0.75,
                    "response_time": 2.5,
                    "quality_score": 0.7
                },
                canary_percentage=0.0
            )
            
            self.models[base_model.id] = base_model
            self.initialized = True
            
            logger.info("🎉 Canary сервис инициализирован!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Canary сервиса: {e}")
            raise
    
    async def deploy_canary(
        self,
        model_name: str,
        version: str,
        canary_percentage: float = 10.0,
        rollback_threshold: float = 0.7,
        evaluation_period_hours: int = 24
    ) -> str:
        """Развертывание Canary-версии модели"""
        try:
            if not self.initialized:
                await self.initialize()
            
            # Создаем новую версию модели
            model_id = f"{model_name}_{version}_{int(datetime.now().timestamp())}"
            
            canary_model = ModelVersion(
                id=model_id,
                name=model_name,
                version=version,
                status=ModelStatus.CANARY,
                created_at=datetime.now(),
                performance_metrics={},
                canary_percentage=canary_percentage,
                rollback_threshold=rollback_threshold,
                evaluation_period_hours=evaluation_period_hours
            )
            
            self.models[model_id] = canary_model
            
            logger.info(f"🚀 Canary-версия развернута: {model_id} ({canary_percentage}% трафика)")
            
            return model_id
            
        except Exception as e:
            logger.error(f"❌ Ошибка развертывания Canary: {e}")
            raise
    
    async def promote_canary(self, model_id: str) -> bool:
        """Продвижение Canary-версии в активную"""
        try:
            if model_id not in self.models:
                raise ValueError(f"Модель {model_id} не найдена")
            
            canary_model = self.models[model_id]
            
            if canary_model.status != ModelStatus.CANARY:
                raise ValueError(f"Модель {model_id} не в статусе Canary")
            
            # Проверяем метрики
            metrics = self.canary_metrics.get(model_id)
            if not metrics:
                logger.warning(f"⚠️ Нет метрик для модели {model_id}")
                return False
            
            # Проверяем пороговые значения
            if not self._check_promotion_criteria(canary_model, metrics):
                logger.warning(f"⚠️ Модель {model_id} не прошла критерии продвижения")
                return False
            
            # Деактивируем старую активную модель
            for model in self.models.values():
                if model.status == ModelStatus.ACTIVE:
                    model.status = ModelStatus.DEPRECATED
            
            # Активируем новую модель
            canary_model.status = ModelStatus.ACTIVE
            canary_model.canary_percentage = 100.0
            
            logger.info(f"✅ Модель {model_id} успешно продвинута в активную")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка продвижения Canary: {e}")
            return False
    
    async def rollback_canary(self, model_id: str) -> bool:
        """Откат Canary-версии"""
        try:
            if model_id not in self.models:
                raise ValueError(f"Модель {model_id} не найдена")
            
            canary_model = self.models[model_id]
            canary_model.status = ModelStatus.FAILED
            
            # Активируем последнюю стабильную модель
            stable_models = [m for m in self.models.values() if m.status == ModelStatus.DEPRECATED]
            if stable_models:
                latest_stable = max(stable_models, key=lambda x: x.created_at)
                latest_stable.status = ModelStatus.ACTIVE
                latest_stable.canary_percentage = 100.0
            
            logger.info(f"🔄 Canary-версия {model_id} откачена")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка отката Canary: {e}")
            return False
    
    def _check_promotion_criteria(self, model: ModelVersion, metrics: CanaryMetrics) -> bool:
        """Проверка критериев для продвижения модели"""
        # Минимальное количество запросов
        if metrics.total_requests < model.min_requests:
            logger.warning(f"⚠️ Недостаточно запросов: {metrics.total_requests}/{model.min_requests}")
            return False
        
        # Проверка пороговых значений
        if metrics.success_rate < model.rollback_threshold:
            logger.warning(f"⚠️ Низкий success rate: {metrics.success_rate:.2f} < {model.rollback_threshold}")
            return False
        
        if metrics.error_rate > (1 - model.rollback_threshold):
            logger.warning(f"⚠️ Высокий error rate: {metrics.error_rate:.2f} > {1 - model.rollback_threshold}")
            return False
        
        if metrics.quality_score < 0.6:
            logger.warning(f"⚠️ Низкий quality score: {metrics.quality_score:.2f} < 0.6")
            return False
        
        if metrics.hallucination_rate > 0.3:
            logger.warning(f"⚠️ Высокий hallucination rate: {metrics.hallucination_rate:.2f} > 0.3")
            return False
        
        return True
    
    async def record_metrics(
        self,
        model_id: str,
        success: bool,
        response_time: float,
        quality_score: float = None,
        citation_accuracy: float = None,
        hallucination_rate: float = None
    ):
        """Запись метрик для Canary-модели"""
        try:
            if model_id not in self.models:
                return
            
            if model_id not in self.canary_metrics:
                self.canary_metrics[model_id] = CanaryMetrics(
                    total_requests=0,
                    success_rate=0.0,
                    avg_response_time=0.0,
                    error_rate=0.0,
                    user_satisfaction=0.0,
                    quality_score=0.0,
                    citation_accuracy=0.0,
                    hallucination_rate=0.0
                )
            
            metrics = self.canary_metrics[model_id]
            
            # Обновляем базовые метрики
            metrics.total_requests += 1
            
            # Обновляем success rate
            if success:
                metrics.success_rate = (metrics.success_rate * (metrics.total_requests - 1) + 1.0) / metrics.total_requests
            else:
                metrics.success_rate = (metrics.success_rate * (metrics.total_requests - 1) + 0.0) / metrics.total_requests
            
            # Обновляем response time
            metrics.avg_response_time = (metrics.avg_response_time * (metrics.total_requests - 1) + response_time) / metrics.total_requests
            
            # Обновляем error rate
            metrics.error_rate = 1.0 - metrics.success_rate
            
            # Обновляем качественные метрики
            if quality_score is not None:
                metrics.quality_score = (metrics.quality_score * (metrics.total_requests - 1) + quality_score) / metrics.total_requests
            
            if citation_accuracy is not None:
                metrics.citation_accuracy = (metrics.citation_accuracy * (metrics.total_requests - 1) + citation_accuracy) / metrics.total_requests
            
            if hallucination_rate is not None:
                metrics.hallucination_rate = (metrics.hallucination_rate * (metrics.total_requests - 1) + hallucination_rate) / metrics.total_requests
            
            # Проверяем необходимость отката
            await self._check_rollback_conditions(model_id)
            
        except Exception as e:
            logger.error(f"❌ Ошибка записи метрик: {e}")
    
    async def _check_rollback_conditions(self, model_id: str):
        """Проверка условий для отката"""
        try:
            model = self.models.get(model_id)
            metrics = self.canary_metrics.get(model_id)
            
            if not model or not metrics or model.status != ModelStatus.CANARY:
                return
            
            # Проверяем критические метрики
            if metrics.total_requests >= model.min_requests:
                if metrics.success_rate < model.rollback_threshold:
                    logger.warning(f"🚨 Автоматический откат: success_rate {metrics.success_rate:.2f} < {model.rollback_threshold}")
                    await self.rollback_canary(model_id)
                    self.rollback_triggers.append(f"Auto-rollback: {model_id} - low success rate")
                
                elif metrics.error_rate > (1 - model.rollback_threshold):
                    logger.warning(f"🚨 Автоматический откат: error_rate {metrics.error_rate:.2f} > {1 - model.rollback_threshold}")
                    await self.rollback_canary(model_id)
                    self.rollback_triggers.append(f"Auto-rollback: {model_id} - high error rate")
                
                elif metrics.hallucination_rate > 0.5:
                    logger.warning(f"🚨 Автоматический откат: hallucination_rate {metrics.hallucination_rate:.2f} > 0.5")
                    await self.rollback_canary(model_id)
                    self.rollback_triggers.append(f"Auto-rollback: {model_id} - high hallucination rate")
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки условий отката: {e}")
    
    async def get_model_for_request(self, user_id: str) -> Optional[str]:
        """Получение модели для запроса пользователя"""
        try:
            # Находим активную модель
            active_models = [m for m in self.models.values() if m.status == ModelStatus.ACTIVE]
            if not active_models:
                return None
            
            active_model = active_models[0]
            
            # Находим Canary-модели
            canary_models = [m for m in self.models.values() if m.status == ModelStatus.CANARY]
            
            if not canary_models:
                return active_model.id
            
            # Выбираем Canary-модель на основе хеша пользователя
            user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            canary_threshold = sum(m.canary_percentage for m in canary_models)
            
            if (user_hash % 100) < canary_threshold:
                # Выбираем Canary-модель
                canary_model = canary_models[0]  # Упрощенная логика
                return canary_model.id
            
            return active_model.id
            
        except Exception as e:
            logger.error(f"❌ Ошибка выбора модели: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса Canary-системы"""
        return {
            "status": "canary_operational",
            "initialized": self.initialized,
            "models": {
                model_id: {
                    "name": model.name,
                    "version": model.version,
                    "status": model.status.value,
                    "canary_percentage": model.canary_percentage,
                    "created_at": model.created_at.isoformat(),
                    "performance_metrics": model.performance_metrics
                }
                for model_id, model in self.models.items()
            },
            "canary_metrics": {
                model_id: {
                    "total_requests": metrics.total_requests,
                    "success_rate": metrics.success_rate,
                    "avg_response_time": metrics.avg_response_time,
                    "error_rate": metrics.error_rate,
                    "quality_score": metrics.quality_score,
                    "citation_accuracy": metrics.citation_accuracy,
                    "hallucination_rate": metrics.hallucination_rate
                }
                for model_id, metrics in self.canary_metrics.items()
            },
            "rollback_triggers": self.rollback_triggers[-10:]  # Последние 10 триггеров
        }

# Глобальный экземпляр сервиса
canary_service = CanaryService()
