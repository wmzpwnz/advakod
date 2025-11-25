"""
AI-валидатор документов на основе Saiga Mistral 7B
Использует языковую модель для более умной проверки юридических документов
"""

import logging
import json
from typing import Dict, Any, List, Optional
from enum import Enum

from .unified_llm_service import unified_llm_service

logger = logging.getLogger(__name__)

class DocumentType(str, Enum):
    """Типы документов"""
    LEGAL = "legal"  # Юридический документ
    REGULATORY = "regulatory"  # Нормативный акт
    LEGISLATIVE = "legislative"  # Законодательный акт
    JUDICIAL = "judicial"  # Судебный документ
    ADMINISTRATIVE = "administrative"  # Административный документ
    CONTRACT = "contract"  # Договор
    INVALID = "invalid"  # Неподходящий документ

class AIDocumentValidator:
    """AI-валидатор документов на основе унифицированного LLM сервиса (Vistral-24B)"""
    
    def __init__(self):
        self.llm_service = unified_llm_service
        self.validation_prompt = self._create_validation_prompt()
        
    def _create_validation_prompt(self) -> str:
        """Создает промпт для валидации документов"""
        return """Ты - эксперт по российскому праву. Твоя задача - определить, является ли документ юридическим/правовым документом.

АНАЛИЗИРУЙ ДОКУМЕНТ И ОПРЕДЕЛИ:

1. ТИП ДОКУМЕНТА (выбери один):
   - legal: Обычный юридический документ (статьи, кодексы, законы)
   - regulatory: Нормативный акт (постановления, приказы, инструкции)
   - legislative: Законодательный акт (федеральные законы, конституция)
   - judicial: Судебный документ (решения, определения, постановления судов)
   - administrative: Административный документ (распоряжения, приказы)
   - contract: Договор или соглашение
   - invalid: НЕ юридический документ (сказки, рецепты, рассказы, техническая документация)

2. УВЕРЕННОСТЬ (от 0.0 до 1.0):
   - 0.9-1.0: Абсолютно уверен
   - 0.7-0.9: Очень уверен
   - 0.5-0.7: Умеренно уверен
   - 0.3-0.5: Слабо уверен
   - 0.0-0.3: Очень не уверен

3. ПРИЧИНА (если invalid):
   - Почему документ не является юридическим

4. РЕКОМЕНДАЦИИ (если invalid):
   - Что нужно изменить, чтобы документ стал юридическим

ОТВЕТ ДАЙ В JSON ФОРМАТЕ:
{
    "document_type": "тип_документа",
    "confidence": 0.95,
    "is_valid": true/false,
    "reason": "причина_отклонения_если_есть",
    "suggestions": ["рекомендация1", "рекомендация2"]
}

ДОКУМЕНТ ДЛЯ АНАЛИЗА:
"""

    async def validate_document(self, text: str, filename: str = None) -> Dict[str, Any]:
        """
        Валидирует документ с помощью AI модели
        
        Args:
            text: Текст документа
            filename: Имя файла (опционально)
            
        Returns:
            Dict с результатами валидации
        """
        if not text or len(text.strip()) < 10:
            return {
                "is_valid": False,
                "document_type": DocumentType.INVALID,
                "confidence": 0.0,
                "reason": "Документ слишком короткий или пустой",
                "suggestions": ["Загрузите документ с достаточным количеством текста"]
            }
        
        try:
            # Ограничиваем длину текста для обработки (первые 2000 символов)
            text_sample = text[:2000] if len(text) > 2000 else text
            
            # Создаем полный промпт
            full_prompt = f"{self.validation_prompt}\n\n{text_sample}"
            
            # Получаем ответ от унифицированной LLM модели
            response = ""
            async for chunk in self.llm_service.generate_response(
                prompt=full_prompt,
                max_tokens=500,
                temperature=0.1,  # Низкая температура для более детерминированного ответа
                stream=True
            ):
                response += chunk
            
            # Парсим JSON ответ
            result = self._parse_ai_response(response)
            
            # Добавляем метаданные
            result.update({
                "text_length": len(text),
                "filename": filename,
                "validation_method": "ai_unified_llm_vistral",
                "text_sample_length": len(text_sample)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка AI валидации: {e}")
            # Fallback к базовой валидации
            return self._fallback_validation(text, filename)

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Парсит ответ AI модели"""
        try:
            # Ищем JSON в ответе
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("JSON не найден в ответе")
            
            json_str = response[json_start:json_end]
            # Безопасная обработка JSON
            try:
                result = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"❌ Ошибка парсинга JSON: {e}")
                result = {"error": "Invalid JSON response"}
            
            # Валидируем и нормализуем результат
            return self._normalize_result(result)
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Ошибка парсинга AI ответа: {e}")
            logger.error(f"Ответ модели: {response}")
            
            # Fallback к базовой валидации
            return self._fallback_validation("", "")

    def _normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Нормализует результат AI валидации"""
        # Нормализуем тип документа
        doc_type = result.get("document_type", "invalid").lower()
        if doc_type not in [e.value for e in DocumentType]:
            doc_type = "invalid"
        
        # Нормализуем уверенность
        confidence = float(result.get("confidence", 0.0))
        confidence = max(0.0, min(1.0, confidence))
        
        # Определяем валидность
        is_valid = result.get("is_valid", False)
        if not is_valid and doc_type != "invalid":
            is_valid = confidence > 0.5
        
        return {
            "is_valid": is_valid,
            "document_type": doc_type,
            "confidence": confidence,
            "reason": result.get("reason", ""),
            "suggestions": result.get("suggestions", [])
        }

    def _fallback_validation(self, text: str, filename: str) -> Dict[str, Any]:
        """Fallback валидация при ошибке AI"""
        # Простая проверка на наличие юридических терминов
        legal_terms = [
            "статья", "пункт", "часть", "раздел", "глава",
            "закон", "кодекс", "конституция", "указ", "постановление",
            "право", "обязанность", "ответственность", "нарушение",
            "суд", "судья", "прокурор", "адвокат", "юрист",
            "договор", "соглашение", "контракт", "сделка"
        ]
        
        text_lower = text.lower()
        legal_count = sum(1 for term in legal_terms if term in text_lower)
        
        # Простая проверка на неюридический контент
        invalid_terms = [
            "сказка", "рассказ", "повесть", "роман", "стихотворение",
            "рецепт", "инструкция по применению", "руководство пользователя",
            "программирование", "код", "алгоритм", "игра", "фильм"
        ]
        
        invalid_count = sum(1 for term in invalid_terms if term in text_lower)
        
        if invalid_count > 0:
            return {
                "is_valid": False,
                "document_type": "invalid",
                "confidence": 0.8,
                "reason": "Документ содержит неюридический контент",
                "suggestions": ["Загрузите документ, содержащий правовые термины и нормы"]
            }
        
        if legal_count > 0:
            return {
                "is_valid": True,
                "document_type": "legal",
                "confidence": 0.6,
                "reason": "",
                "suggestions": []
            }
        
        return {
            "is_valid": False,
            "document_type": "invalid",
            "confidence": 0.7,
            "reason": "Документ не содержит юридических терминов",
            "suggestions": ["Загрузите документ, содержащий правовые термины и нормы"]
        }

    async def validate_batch(self, documents: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Валидирует несколько документов одновременно"""
        results = []
        for doc in documents:
            result = await self.validate_document(
                text=doc.get("text", ""),
                filename=doc.get("filename")
            )
            results.append(result)
        return results

    def get_validation_stats(self) -> Dict[str, Any]:
        """Возвращает статистику валидации"""
        return {
            "validator_type": "ai_saiga",
            "model_name": "Saiga Mistral 7B",
            "supported_languages": ["ru", "en"],
            "max_text_length": 2000,
            "fallback_enabled": True
        }

# Глобальный экземпляр AI валидатора
ai_document_validator = AIDocumentValidator()
