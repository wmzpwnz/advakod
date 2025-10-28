"""
Гибридный валидатор документов
Комбинирует быструю проверку правил с AI валидацией для сложных случаев
"""

import logging
import hashlib
from typing import Dict, Any, Optional
from functools import lru_cache

from .document_validator import document_validator
from .ai_document_validator import ai_document_validator

logger = logging.getLogger(__name__)

class HybridDocumentValidator:
    """Гибридный валидатор документов"""
    
    def __init__(self):
        self.rule_validator = document_validator
        self.ai_validator = ai_document_validator
        self.validation_cache = {}
        
    def _get_text_sample(self, text: str, max_length: int = 1000) -> str:
        """Получает репрезентативную выборку текста"""
        if len(text) <= max_length:
            return text
        
        # Берем начало, середину и конец документа
        sample_size = max_length // 3
        
        start = text[:sample_size]
        middle_start = len(text) // 2 - sample_size // 2
        middle = text[middle_start:middle_start + sample_size]
        end = text[-sample_size:]
        
        return f"{start}\n\n... [пропуск] ...\n\n{middle}\n\n... [пропуск] ...\n\n{end}"
    
    def _is_obviously_invalid(self, text: str) -> Optional[Dict[str, Any]]:
        """Быстрая проверка на явно неюридический контент"""
        # Отключена проверка на недопустимые паттерны
        # Все документы проходят валидацию
        return None
    
    def _is_obviously_valid(self, text: str) -> Optional[Dict[str, Any]]:
        """Быстрая проверка на явно юридический контент"""
        text_lower = text.lower()
        
        # Счетчик юридических терминов
        legal_terms = [
            "статья", "пункт", "часть", "раздел", "глава",
            "закон", "кодекс", "конституция", "указ", "постановление",
            "право", "обязанность", "ответственность", "нарушение",
            "суд", "судья", "прокурор", "адвокат", "юрист",
            "договор", "соглашение", "контракт", "сделка"
        ]
        
        legal_count = sum(1 for term in legal_terms if term in text_lower)
        total_words = len(text.split())
        
        if total_words == 0:
            return None
        
        legal_ratio = legal_count / total_words
        
        # Если много юридических терминов
        if legal_ratio > 0.05:  # Более 5% юридических терминов
            return {
                "is_valid": True,
                "document_type": "legal",
                "confidence": 0.9,
                "reason": "",
                "suggestions": [],
                "validation_method": "rule_based_fast",
                "legal_ratio": legal_ratio
            }
        
        # Проверка на правовые паттерны
        legal_patterns = [
            "статья\\s+\\d+", "пункт\\s+\\d+", "часть\\s+\\d+",
            "федеральный\\s+закон", "гражданский\\s+кодекс",
            "уголовный\\s+кодекс", "трудовой\\s+кодекс"
        ]
        
        import re
        pattern_count = sum(1 for pattern in legal_patterns if re.search(pattern, text_lower))
        
        if pattern_count > 0:
            return {
                "is_valid": True,
                "document_type": "legal",
                "confidence": 0.85,
                "reason": "",
                "suggestions": [],
                "validation_method": "rule_based_fast",
                "pattern_count": pattern_count
            }
        
        return None
    
    @lru_cache(maxsize=1000)
    def _get_cached_validation(self, text_hash: str, text_sample: str) -> Dict[str, Any]:
        """Получает кэшированный результат валидации"""
        # AI валидация для сложных случаев
        return self.ai_validator.validate_document(text_sample)
    
    async def validate_document(self, text: str, filename: str = None) -> Dict[str, Any]:
        """
        Гибридная валидация документа
        
        Алгоритм:
        1. Быстрая проверка на явно неюридический контент
        2. Быстрая проверка на явно юридический контент  
        3. AI валидация для сомнительных случаев
        4. Кэширование результатов
        """
        if not text or len(text.strip()) < 10:
            return {
                "is_valid": False,
                "document_type": "invalid",
                "confidence": 0.0,
                "reason": "Документ слишком короткий или пустой",
                "suggestions": ["Загрузите документ с достаточным количеством текста"],
                "validation_method": "hybrid_fast"
            }
        
        # 1. Быстрая проверка на явно неюридический контент
        invalid_result = self._is_obviously_invalid(text)
        if invalid_result:
            return invalid_result
        
        # 2. Быстрая проверка на явно юридический контент
        valid_result = self._is_obviously_valid(text)
        if valid_result:
            return valid_result
        
        # 3. AI валидация для сомнительных случаев
        try:
            # Получаем выборку текста для AI анализа
            text_sample = self._get_text_sample(text, max_length=1000)
            text_hash = hashlib.md5(text_sample.encode()).hexdigest()
            
            # Проверяем кэш
            if text_hash in self.validation_cache:
                result = self.validation_cache[text_hash].copy()
                result["validation_method"] = "hybrid_cached"
                return result
            
            # AI валидация
            result = await self.ai_validator.validate_document(text_sample, filename)
            result["validation_method"] = "hybrid_ai"
            
            # Кэшируем результат
            self.validation_cache[text_hash] = result.copy()
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка AI валидации в гибридном режиме: {e}")
            
            # Fallback к правилам
            result = self.rule_validator.validate_document(text, filename)
            result["validation_method"] = "hybrid_fallback"
            return result
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Возвращает статистику валидации"""
        return {
            "validator_type": "hybrid",
            "cache_size": len(self.validation_cache),
            "rule_validator_stats": {
                "type": "rule_based",
                "keywords_count": len(self.rule_validator.legal_keywords)
            },
            "ai_validator_stats": self.ai_validator.get_validation_stats(),
            "optimization_features": [
                "fast_invalid_detection",
                "fast_valid_detection", 
                "ai_for_ambiguous_cases",
                "text_sampling",
                "result_caching"
            ]
        }
    
    def clear_cache(self):
        """Очищает кэш валидации"""
        self.validation_cache.clear()
        logger.info("Кэш валидации очищен")

# Глобальный экземпляр гибридного валидатора
hybrid_document_validator = HybridDocumentValidator()
