"""
Улучшенный LoRA сервис с интеграцией метрик качества
"""

import logging
import json
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class LoRAMetrics:
    """Метрики качества для LoRA обучения"""
    citation_recall: float
    support_coverage: float
    hallucination_score: float
    legal_consistency: float
    overall_quality: float
    response_time: float
    user_satisfaction: float
    complexity_score: float

@dataclass
class TrainingExample:
    """Пример для обучения с метриками"""
    id: str
    query: str
    response: str
    sources: List[Dict[str, Any]]
    metrics: LoRAMetrics
    is_approved: bool = False
    priority: float = 0.0
    created_at: datetime = None

class EnhancedLoRAService:
    """Улучшенный LoRA сервис с метриками качества"""
    
    def __init__(self):
        self.training_examples: List[TrainingExample] = []
        self.quality_thresholds = {
            "min_citation_recall": 0.7,
            "min_support_coverage": 0.5,
            "max_hallucination_score": 0.3,
            "min_legal_consistency": 0.8,
            "min_overall_quality": 0.6
        }
        self.priority_weights = {
            "citation_recall": 0.3,
            "support_coverage": 0.2,
            "hallucination_score": 0.2,
            "legal_consistency": 0.2,
            "user_satisfaction": 0.1
        }
        self.initialized = False
        
    async def initialize(self):
        """Инициализация сервиса"""
        try:
            logger.info("🚀 Инициализация улучшенного LoRA сервиса...")
            
            # Загружаем существующие примеры из базы данных
            await self._load_training_examples()
            
            self.initialized = True
            logger.info("🎉 Улучшенный LoRA сервис инициализирован!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации LoRA сервиса: {e}")
            raise
    
    async def _load_training_examples(self):
        """Загрузка примеров для обучения из базы данных"""
        try:
            # Здесь будет загрузка из базы данных
            # Пока что создаем пустой список
            self.training_examples = []
            logger.info("📥 Примеры для обучения загружены")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки примеров: {e}")
    
    async def add_training_example(
        self,
        query: str,
        response: str,
        sources: List[Dict[str, Any]],
        metrics: LoRAMetrics,
        user_satisfaction: float = None
    ) -> str:
        """Добавление примера для обучения с метриками"""
        try:
            if not self.initialized:
                await self.initialize()
            
            # Создаем ID для примера
            example_id = f"example_{int(datetime.now().timestamp())}_{hashlib.md5(query.encode()).hexdigest()[:8]}"
            
            # Обновляем метрики с user_satisfaction
            if user_satisfaction is not None:
                metrics.user_satisfaction = user_satisfaction
            
            # Вычисляем приоритет
            priority = self._calculate_priority(metrics)
            
            # Проверяем качество
            is_approved = self._check_quality_thresholds(metrics)
            
            # Создаем пример
            example = TrainingExample(
                id=example_id,
                query=query,
                response=response,
                sources=sources,
                metrics=metrics,
                is_approved=is_approved,
                priority=priority,
                created_at=datetime.now()
            )
            
            self.training_examples.append(example)
            
            logger.info(f"✅ Пример добавлен: {example_id} (приоритет: {priority:.2f}, одобрен: {is_approved})")
            
            return example_id
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления примера: {e}")
            raise
    
    def _calculate_priority(self, metrics: LoRAMetrics) -> float:
        """Вычисление приоритета примера для обучения"""
        try:
            # Базовый приоритет на основе метрик
            priority = 0.0
            
            # Citation recall (чем выше, тем лучше)
            priority += metrics.citation_recall * self.priority_weights["citation_recall"]
            
            # Support coverage (чем выше, тем лучше)
            priority += metrics.support_coverage * self.priority_weights["support_coverage"]
            
            # Hallucination score (чем ниже, тем лучше)
            priority += (1.0 - metrics.hallucination_score) * self.priority_weights["hallucination_score"]
            
            # Legal consistency (чем выше, тем лучше)
            priority += metrics.legal_consistency * self.priority_weights["legal_consistency"]
            
            # User satisfaction (чем выше, тем лучше)
            priority += metrics.user_satisfaction * self.priority_weights["user_satisfaction"]
            
            # Дополнительные факторы
            if metrics.overall_quality > 0.8:
                priority += 0.1  # Бонус за высокое качество
            
            if metrics.complexity_score > 0.7:
                priority += 0.05  # Бонус за сложные кейсы
            
            return min(1.0, priority)  # Ограничиваем до 1.0
            
        except Exception as e:
            logger.error(f"❌ Ошибка вычисления приоритета: {e}")
            return 0.5
    
    def _check_quality_thresholds(self, metrics: LoRAMetrics) -> bool:
        """Проверка соответствия пороговым значениям качества"""
        try:
            return (
                metrics.citation_recall >= self.quality_thresholds["min_citation_recall"] and
                metrics.support_coverage >= self.quality_thresholds["min_support_coverage"] and
                metrics.hallucination_score <= self.quality_thresholds["max_hallucination_score"] and
                metrics.legal_consistency >= self.quality_thresholds["min_legal_consistency"] and
                metrics.overall_quality >= self.quality_thresholds["min_overall_quality"]
            )
        except Exception as e:
            logger.error(f"❌ Ошибка проверки качества: {e}")
            return False
    
    async def get_training_batch(
        self,
        batch_size: int = 100,
        min_quality: float = 0.6,
        include_unapproved: bool = False
    ) -> List[TrainingExample]:
        """Получение батча примеров для обучения"""
        try:
            if not self.initialized:
                await self.initialize()
            
            # Фильтруем примеры по качеству
            filtered_examples = []
            for example in self.training_examples:
                if example.metrics.overall_quality >= min_quality:
                    if include_unapproved or example.is_approved:
                        filtered_examples.append(example)
            
            # Сортируем по приоритету
            filtered_examples.sort(key=lambda x: x.priority, reverse=True)
            
            # Берем топ примеров
            batch = filtered_examples[:batch_size]
            
            logger.info(f"📦 Подготовлен батч: {len(batch)} примеров (качество >= {min_quality})")
            
            return batch
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения батча: {e}")
            return []
    
    async def get_priority_examples(self, limit: int = 50) -> List[TrainingExample]:
        """Получение приоритетных примеров для обучения"""
        try:
            if not self.initialized:
                await self.initialize()
            
            # Сортируем по приоритету
            sorted_examples = sorted(self.training_examples, key=lambda x: x.priority, reverse=True)
            
            # Берем топ примеров
            priority_examples = sorted_examples[:limit]
            
            logger.info(f"⭐ Получено {len(priority_examples)} приоритетных примеров")
            
            return priority_examples
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения приоритетных примеров: {e}")
            return []
    
    async def get_quality_statistics(self) -> Dict[str, Any]:
        """Получение статистики качества примеров"""
        try:
            if not self.initialized:
                await self.initialize()
            
            if not self.training_examples:
                return {
                    "total_examples": 0,
                    "approved_examples": 0,
                    "average_quality": 0.0,
                    "quality_distribution": {}
                }
            
            # Базовая статистика
            total_examples = len(self.training_examples)
            approved_examples = sum(1 for ex in self.training_examples if ex.is_approved)
            
            # Средние метрики
            avg_metrics = {
                "citation_recall": np.mean([ex.metrics.citation_recall for ex in self.training_examples]),
                "support_coverage": np.mean([ex.metrics.support_coverage for ex in self.training_examples]),
                "hallucination_score": np.mean([ex.metrics.hallucination_score for ex in self.training_examples]),
                "legal_consistency": np.mean([ex.metrics.legal_consistency for ex in self.training_examples]),
                "overall_quality": np.mean([ex.metrics.overall_quality for ex in self.training_examples]),
                "user_satisfaction": np.mean([ex.metrics.user_satisfaction for ex in self.training_examples])
            }
            
            # Распределение качества
            quality_ranges = {
                "high": sum(1 for ex in self.training_examples if ex.metrics.overall_quality >= 0.8),
                "medium": sum(1 for ex in self.training_examples if 0.6 <= ex.metrics.overall_quality < 0.8),
                "low": sum(1 for ex in self.training_examples if ex.metrics.overall_quality < 0.6)
            }
            
            return {
                "total_examples": total_examples,
                "approved_examples": approved_examples,
                "approval_rate": approved_examples / total_examples if total_examples > 0 else 0,
                "average_quality": avg_metrics["overall_quality"],
                "average_metrics": avg_metrics,
                "quality_distribution": quality_ranges,
                "priority_distribution": {
                    "high": sum(1 for ex in self.training_examples if ex.priority >= 0.8),
                    "medium": sum(1 for ex in self.training_examples if 0.5 <= ex.priority < 0.8),
                    "low": sum(1 for ex in self.training_examples if ex.priority < 0.5)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {}
    
    async def update_quality_thresholds(self, new_thresholds: Dict[str, float]):
        """Обновление пороговых значений качества"""
        try:
            for key, value in new_thresholds.items():
                if key in self.quality_thresholds:
                    self.quality_thresholds[key] = value
                    logger.info(f"📊 Обновлен порог {key}: {value}")
            
            # Пересчитываем одобрение для всех примеров
            for example in self.training_examples:
                example.is_approved = self._check_quality_thresholds(example.metrics)
            
            logger.info("✅ Пороговые значения обновлены")
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления порогов: {e}")
    
    async def export_training_data(
        self,
        format: str = "json",
        include_metrics: bool = True
    ) -> str:
        """Экспорт данных для обучения"""
        try:
            if not self.initialized:
                await self.initialize()
            
            # Получаем одобренные примеры
            approved_examples = [ex for ex in self.training_examples if ex.is_approved]
            
            if format == "json":
                data = []
                for example in approved_examples:
                    item = {
                        "id": example.id,
                        "query": example.query,
                        "response": example.response,
                        "sources": example.sources,
                        "created_at": example.created_at.isoformat(),
                        "priority": example.priority
                    }
                    
                    if include_metrics:
                        item["metrics"] = {
                            "citation_recall": example.metrics.citation_recall,
                            "support_coverage": example.metrics.support_coverage,
                            "hallucination_score": example.metrics.hallucination_score,
                            "legal_consistency": example.metrics.legal_consistency,
                            "overall_quality": example.metrics.overall_quality,
                            "user_satisfaction": example.metrics.user_satisfaction,
                            "complexity_score": example.metrics.complexity_score
                        }
                    
                    data.append(item)
                
                return json.dumps(data, ensure_ascii=False, indent=2)
            
            else:
                raise ValueError(f"Неподдерживаемый формат: {format}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка экспорта данных: {e}")
            return ""
    
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса сервиса"""
        return {
            "status": "enhanced_lora_operational",
            "initialized": self.initialized,
            "total_examples": len(self.training_examples),
            "approved_examples": sum(1 for ex in self.training_examples if ex.is_approved),
            "quality_thresholds": self.quality_thresholds,
            "priority_weights": self.priority_weights
        }

# Глобальный экземпляр сервиса
enhanced_lora_service = EnhancedLoRAService()
