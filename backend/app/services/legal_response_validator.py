"""
Валидатор юридических ответов для проверки точности информации
"""

import re
import logging
from typing import Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    is_valid: bool
    confidence: float
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]

class LegalResponseValidator:
    """Валидатор юридических ответов для проверки точности"""
    
    def __init__(self):
        # Паттерны для проверки точности
        self.constitution_patterns = {
            "correct_chapters": r"Глава\s+[1-9]",
            "incorrect_members": r"член\s+[0-9]+",
            "incorrect_articles": r"148\s+статей",
            "correct_articles": r"137\s+статей"
        }
        
        # Запрещенные паттерны
        self.forbidden_patterns = [
            r"член\s+[0-9]+",  # "члены" вместо "глав"
            r"Глава\s+[1-9][0-9]+",  # Несуществующие главы (10+)
            r"148\s+статей",  # Неправильное количество статей
        ]
        
        # Правильные данные о Конституции
        self.constitution_facts = {
            "adoption_date": "12 декабря 1993 года",
            "total_articles": 137,
            "total_chapters": 9,
            "chapters": [
                "Основы конституционного строя",
                "Права и свободы человека и гражданина", 
                "Федеративное устройство",
                "Президент Российской Федерации",
                "Федеральное Собрание",
                "Правительство Российской Федерации",
                "Судебная власть и прокуратура",
                "Местное самоуправление",
                "Конституционные поправки и пересмотр Конституции"
            ]
        }
    
    def validate_response(self, response_text: str, question: str) -> ValidationResult:
        """Валидирует юридический ответ на точность"""
        errors = []
        warnings = []
        suggestions = []
        
        # Проверяем на запрещенные паттерны
        for pattern in self.forbidden_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                if "член" in pattern:
                    errors.append("Использовано неправильное слово 'член' вместо 'глава'")
                elif "Глава" in pattern:
                    errors.append("Указаны несуществующие главы Конституции")
                elif "148" in pattern:
                    errors.append("Указано неправильное количество статей (148 вместо 137)")
        
        # Проверяем точность данных о Конституции
        if "конституция" in question.lower():
            self._validate_constitution_facts(response_text, errors, warnings, suggestions)
        
        # Проверяем общую точность
        self._validate_general_accuracy(response_text, errors, warnings, suggestions)
        
        # Определяем confidence
        confidence = self._calculate_confidence(errors, warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            confidence=confidence,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _validate_constitution_facts(self, text: str, errors: List[str], warnings: List[str], suggestions: List[str]):
        """Проверяет точность фактов о Конституции"""
        
        # Проверяем дату принятия
        if "25 декабря" in text:
            errors.append("Неправильная дата принятия Конституции (указано 25 декабря вместо 12 декабря)")
        
        # Проверяем количество статей
        if "148 статей" in text:
            errors.append("Неправильное количество статей (указано 148 вместо 137)")
        
        # Проверяем структуру
        if "член" in text.lower():
            errors.append("Использовано неправильное слово 'член' вместо 'глава'")
        
        # Проверяем количество глав
        chapter_count = len(re.findall(r"Глава\s+[1-9]", text))
        if chapter_count > 0 and chapter_count != 9:
            warnings.append(f"Указано {chapter_count} глав вместо 9")
    
    def _validate_general_accuracy(self, text: str, errors: List[str], warnings: List[str], suggestions: List[str]):
        """Общая проверка точности"""
        
        # Проверяем на выдуманные законы
        if "ст. 999" in text or "статья 999" in text:
            errors.append("Указана несуществующая статья 999")
        
        # Проверяем на нереалистичные сроки
        if re.search(r"\d+\s+лет", text):
            if "10 лет" in text or "20 лет" in text:
                warnings.append("Указаны нереалистично длинные сроки")
        
        # Проверяем на внешние источники
        if "consultant.ru" in text or "garant.ru" in text:
            errors.append("Упоминание внешних источников запрещено")
    
    def _calculate_confidence(self, errors: List[str], warnings: List[str]) -> float:
        """Рассчитывает confidence на основе ошибок и предупреждений"""
        base_confidence = 1.0
        
        # Штрафуем за ошибки
        for error in errors:
            if "член" in error or "148" in error or "25 декабря" in error:
                base_confidence -= 0.3  # Критические ошибки
            else:
                base_confidence -= 0.1  # Обычные ошибки
        
        # Штрафуем за предупреждения
        for warning in warnings:
            base_confidence -= 0.05
        
        return max(0.0, min(1.0, base_confidence))
    
    def _generate_safe_response(self, validation_result: ValidationResult) -> str:
        """Генерирует безопасный ответ при невалидном результате"""
        if not validation_result.is_valid:
            return f"""Извините, но я не могу дать точный ответ на ваш вопрос. 

Проблемы с точностью:
{chr(10).join(f"- {error}" for error in validation_result.errors)}

Рекомендую обратиться к официальным источникам или компетентным органам для получения точной информации.

Если у вас есть конкретный правовой вопрос, пожалуйста, уточните его более детально."""
        
        return "Ответ прошел валидацию и может быть предоставлен пользователю."

# Глобальный экземпляр
legal_response_validator = LegalResponseValidator()
