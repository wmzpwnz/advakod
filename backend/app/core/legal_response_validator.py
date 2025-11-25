"""
Система валидации юридических ответов
Проверяет корректность, полноту и юридическую точность ответов ИИ
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Уровни валидации"""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"


@dataclass
class ValidationResult:
    """Результат валидации"""
    is_valid: bool
    score: float
    issues: List[str]
    warnings: List[str]
    suggestions: List[str]
    confidence: float


class LegalResponseValidator:
    """Валидатор юридических ответов"""
    
    def __init__(self):
        # Паттерны для проверки юридических ссылок
        self.legal_reference_patterns = [
            r'ст\.\s*\d+',  # статья
            r'ч\.\s*\d+',   # часть
            r'п\.\s*\d+',   # пункт
            r'ГК\s*РФ',     # Гражданский кодекс
            r'УК\s*РФ',     # Уголовный кодекс
            r'ТК\s*РФ',     # Трудовой кодекс
            r'СК\s*РФ',     # Семейный кодекс
            r'НК\s*РФ',     # Налоговый кодекс
            r'КоАП\s*РФ',   # Кодекс об административных правонарушениях
            r'ГПК\s*РФ',    # Гражданский процессуальный кодекс
            r'УПК\s*РФ',    # Уголовный процессуальный кодекс
            r'АПК\s*РФ',    # Арбитражный процессуальный кодекс
            r'Конституция\s*РФ',  # Конституция
            r'ФЗ\s*№\s*\d+',  # Федеральный закон
            r'Постановление\s*Пленума',  # Постановления Пленума
        ]
        
        # Обязательные элементы юридического ответа
        self.required_elements = [
            "проблема", "закон", "решение", "действия"
        ]
        
        # Ключевые юридические термины
        self.legal_terms = [
            "право", "обязанность", "ответственность", "суд", "иск",
            "договор", "сделка", "собственность", "наследство", "алименты",
            "трудовой договор", "увольнение", "налог", "штраф", "лицензия"
        ]
        
        # Опасные фразы, которые не должны быть в ответе
        self.dangerous_phrases = [
            "я не могу", "я не знаю", "я не уверен",
            "это не моя специализация", "обратитесь к другому",
            "я не юрист", "я не адвокат", "я не эксперт"
        ]
        
        # Фразы, указывающие на неопределенность
        self.uncertainty_phrases = [
            "возможно", "вероятно", "может быть", "скорее всего",
            "наверное", "предположительно", "если я правильно понимаю"
        ]
    
    def validate_response(
        self, 
        response: str, 
        query: str, 
        level: ValidationLevel = ValidationLevel.STANDARD
    ) -> ValidationResult:
        """Валидирует юридический ответ"""
        
        issues = []
        warnings = []
        suggestions = []
        score = 100.0
        
        # 1. Проверка базовой структуры
        structure_issues = self._validate_structure(response)
        issues.extend(structure_issues)
        score -= len(structure_issues) * 10
        
        # 2. Проверка юридических ссылок
        legal_ref_issues = self._validate_legal_references(response)
        issues.extend(legal_ref_issues)
        score -= len(legal_ref_issues) * 5
        
        # 3. Проверка содержания
        content_issues = self._validate_content(response, query)
        issues.extend(content_issues)
        score -= len(content_issues) * 8
        
        # 4. Проверка на опасные фразы
        dangerous_issues = self._validate_dangerous_phrases(response)
        issues.extend(dangerous_issues)
        score -= len(dangerous_issues) * 15
        
        # 5. Проверка неопределенности
        uncertainty_warnings = self._validate_uncertainty(response)
        warnings.extend(uncertainty_warnings)
        score -= len(uncertainty_warnings) * 3
        
        # 6. Проверка полноты
        completeness_issues = self._validate_completeness(response, query)
        issues.extend(completeness_issues)
        score -= len(completeness_issues) * 7
        
        # 7. Проверка юридической точности
        accuracy_issues = self._validate_legal_accuracy(response)
        issues.extend(accuracy_issues)
        score -= len(accuracy_issues) * 12
        
        # 8. Генерация предложений по улучшению
        suggestions = self._generate_suggestions(response, issues, warnings)
        
        # Вычисляем уверенность
        confidence = max(0.0, min(1.0, score / 100.0))
        
        # Определяем валидность
        is_valid = len(issues) == 0 and score >= 70.0
        
        return ValidationResult(
            is_valid=is_valid,
            score=max(0.0, score),
            issues=issues,
            warnings=warnings,
            suggestions=suggestions,
            confidence=confidence
        )
    
    def _validate_structure(self, response: str) -> List[str]:
        """Проверяет структуру ответа"""
        issues = []
        
        # Проверяем длину ответа
        if len(response.strip()) < 50:
            issues.append("Ответ слишком короткий для юридической консультации")
        
        if len(response) > 5000:
            issues.append("Ответ слишком длинный, может быть неудобен для чтения")
        
        # Проверяем наличие обязательных элементов
        response_lower = response.lower()
        for element in self.required_elements:
            if element not in response_lower:
                issues.append(f"Отсутствует обязательный элемент: {element}")
        
        return issues
    
    def _validate_legal_references(self, response: str) -> List[str]:
        """Проверяет наличие юридических ссылок"""
        issues = []
        
        # Ищем юридические ссылки
        legal_refs_found = []
        for pattern in self.legal_reference_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            legal_refs_found.extend(matches)
        
        if not legal_refs_found:
            issues.append("Отсутствуют ссылки на конкретные статьи законов")
        
        # Проверяем корректность ссылок
        for ref in legal_refs_found:
            if not self._is_valid_legal_reference(ref):
                issues.append(f"Некорректная юридическая ссылка: {ref}")
        
        return issues
    
    def _validate_content(self, response: str, query: str) -> List[str]:
        """Проверяет содержание ответа"""
        issues = []
        
        # Проверяем соответствие запросу
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        
        # Находим пересечение ключевых слов
        common_words = query_words.intersection(response_words)
        if len(common_words) < len(query_words) * 0.3:
            issues.append("Ответ не полностью соответствует заданному вопросу")
        
        # Проверяем наличие юридических терминов
        response_lower = response.lower()
        legal_terms_found = [term for term in self.legal_terms if term in response_lower]
        
        if len(legal_terms_found) < 2:
            issues.append("Недостаточно юридических терминов в ответе")
        
        return issues
    
    def _validate_dangerous_phrases(self, response: str) -> List[str]:
        """Проверяет наличие опасных фраз"""
        issues = []
        
        response_lower = response.lower()
        for phrase in self.dangerous_phrases:
            if phrase in response_lower:
                issues.append(f"Обнаружена нежелательная фраза: '{phrase}'")
        
        return issues
    
    def _validate_uncertainty(self, response: str) -> List[str]:
        """Проверяет уровень неопределенности"""
        warnings = []
        
        response_lower = response.lower()
        uncertainty_count = sum(1 for phrase in self.uncertainty_phrases if phrase in response_lower)
        
        if uncertainty_count > 3:
            warnings.append("Высокий уровень неопределенности в ответе")
        elif uncertainty_count > 1:
            warnings.append("Повышенный уровень неопределенности в ответе")
        
        return warnings
    
    def _validate_completeness(self, response: str, query: str) -> List[str]:
        """Проверяет полноту ответа"""
        issues = []
        
        # Проверяем, отвечает ли ответ на вопрос
        question_words = ["что", "как", "где", "когда", "почему", "зачем", "кто", "какой"]
        query_lower = query.lower()
        
        for word in question_words:
            if word in query_lower and not self._addresses_question(response, word):
                issues.append(f"Ответ не полностью раскрывает вопрос с '{word}'")
        
        return issues
    
    def _validate_legal_accuracy(self, response: str) -> List[str]:
        """Проверяет юридическую точность"""
        issues = []
        
        # Проверяем на противоречия
        if self._has_contradictions(response):
            issues.append("Обнаружены противоречия в ответе")
        
        # Проверяем на устаревшие ссылки
        outdated_refs = self._find_outdated_references(response)
        if outdated_refs:
            issues.append(f"Обнаружены устаревшие ссылки: {', '.join(outdated_refs)}")
        
        return issues
    
    def _is_valid_legal_reference(self, ref: str) -> bool:
        """Проверяет корректность юридической ссылки"""
        # Простая проверка формата
        if re.match(r'ст\.\s*\d+', ref):
            return True
        if re.match(r'ч\.\s*\d+', ref):
            return True
        if re.match(r'п\.\s*\d+', ref):
            return True
        if re.match(r'[А-Я]{2,}\s*РФ', ref):
            return True
        
        return False
    
    def _addresses_question(self, response: str, question_word: str) -> bool:
        """Проверяет, отвечает ли ответ на вопрос с определенным словом"""
        # Простая эвристика
        if question_word == "что":
            return "это" in response.lower() or "означает" in response.lower()
        elif question_word == "как":
            return "порядок" in response.lower() or "процедура" in response.lower()
        elif question_word == "где":
            return "место" in response.lower() or "адрес" in response.lower()
        elif question_word == "когда":
            return "срок" in response.lower() or "время" in response.lower()
        elif question_word == "почему":
            return "причина" in response.lower() or "основание" in response.lower()
        
        return True
    
    def _has_contradictions(self, response: str) -> bool:
        """Проверяет наличие противоречий"""
        # Простая проверка на противоречия
        contradiction_patterns = [
            (r'можно', r'нельзя'),
            (r'разрешено', r'запрещено'),
            (r'обязательно', r'необязательно'),
            (r'всегда', r'никогда')
        ]
        
        for pos_pattern, neg_pattern in contradiction_patterns:
            if re.search(pos_pattern, response, re.IGNORECASE) and \
               re.search(neg_pattern, response, re.IGNORECASE):
                return True
        
        return False
    
    def _find_outdated_references(self, response: str) -> List[str]:
        """Находит устаревшие ссылки"""
        outdated_refs = []
        
        # Проверяем на устаревшие законы
        outdated_laws = [
            r'Закон\s*РСФСР',
            r'Указ\s*Президента\s*СССР',
            r'Постановление\s*Совета\s*Министров\s*СССР'
        ]
        
        for pattern in outdated_laws:
            matches = re.findall(pattern, response, re.IGNORECASE)
            outdated_refs.extend(matches)
        
        return outdated_refs
    
    def _generate_suggestions(
        self, 
        response: str, 
        issues: List[str], 
        warnings: List[str]
    ) -> List[str]:
        """Генерирует предложения по улучшению"""
        suggestions = []
        
        if "Отсутствуют ссылки на конкретные статьи законов" in issues:
            suggestions.append("Добавьте ссылки на конкретные статьи ГК РФ, УК РФ или других кодексов")
        
        if "Ответ слишком короткий" in issues:
            suggestions.append("Расширьте ответ, добавив больше деталей и примеров")
        
        if "Недостаточно юридических терминов" in issues:
            suggestions.append("Используйте больше профессиональных юридических терминов")
        
        if "Высокий уровень неопределенности" in warnings:
            suggestions.append("Уменьшите количество неопределенных формулировок")
        
        if "Обнаружены противоречия" in issues:
            suggestions.append("Проверьте ответ на наличие противоречивых утверждений")
        
        return suggestions
    
    def get_quality_score(self, response: str, query: str) -> Dict[str, Any]:
        """Возвращает детальную оценку качества ответа"""
        validation_result = self.validate_response(response, query)
        
        return {
            "overall_score": validation_result.score,
            "confidence": validation_result.confidence,
            "is_valid": validation_result.is_valid,
            "issues_count": len(validation_result.issues),
            "warnings_count": len(validation_result.warnings),
            "suggestions_count": len(validation_result.suggestions),
            "legal_references": self._count_legal_references(response),
            "structure_quality": self._assess_structure_quality(response),
            "content_relevance": self._assess_content_relevance(response, query)
        }
    
    def _count_legal_references(self, response: str) -> int:
        """Подсчитывает количество юридических ссылок"""
        count = 0
        for pattern in self.legal_reference_patterns:
            count += len(re.findall(pattern, response, re.IGNORECASE))
        return count
    
    def _assess_structure_quality(self, response: str) -> float:
        """Оценивает качество структуры ответа"""
        score = 0.0
        
        # Проверяем наличие заголовков/разделов
        if re.search(r'\d+\.', response):
            score += 0.3
        
        # Проверяем наличие списков
        if re.search(r'[•\-\*]', response):
            score += 0.2
        
        # Проверяем длину абзацев
        paragraphs = response.split('\n\n')
        if len(paragraphs) > 1:
            score += 0.3
        
        # Проверяем наличие заключения
        if any(word in response.lower() for word in ['заключение', 'итог', 'вывод']):
            score += 0.2
        
        return min(1.0, score)
    
    def _assess_content_relevance(self, response: str, query: str) -> float:
        """Оценивает релевантность содержания"""
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        
        # Вычисляем пересечение
        common_words = query_words.intersection(response_words)
        
        if len(query_words) == 0:
            return 1.0
        
        return len(common_words) / len(query_words)


# Глобальный экземпляр
legal_response_validator = LegalResponseValidator()
