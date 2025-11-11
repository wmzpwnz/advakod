"""
AI-классификатор типов документов
Использует LLM для более точного определения типа документа
"""

import logging
import json
from typing import Dict, Any, Optional
from .unified_llm_service import unified_llm_service
from .vector_store_service import determine_document_type

logger = logging.getLogger(__name__)


class AIDocumentClassifier:
    """AI-классификатор документов с использованием LLM"""
    
    def __init__(self):
        self.llm_service = unified_llm_service
        self.use_ai = True  # Можно отключить для быстрой работы
        
    async def classify_document_ai(
        self, 
        text_content: str,
        file_name: str = "",
        document_id: str = ""
    ) -> Dict[str, Any]:
        """
        Классифицирует документ с помощью AI
        
        Returns:
            {
                "type": "codex|federal_law|...",
                "confidence": 0.0-1.0,
                "reason": "объяснение",
                "method": "ai|rule"
            }
        """
        
        # Сначала пробуем правило-основанный подход
        rule_type = determine_document_type(file_name, document_id, text_content)
        
        # Если уверены - возвращаем сразу
        if rule_type != 'other' and (
            document_id.startswith('codex_') or 
            'кодекс' in file_name.lower()
        ):
            return {
                "type": rule_type,
                "confidence": 0.95,
                "reason": "Определено по правилам (кодекс)",
                "method": "rule"
            }
        
        # Для остальных используем AI
        if not self.use_ai or not text_content:
            return {
                "type": rule_type,
                "confidence": 0.7,
                "reason": "Определено по правилам",
                "method": "rule"
            }
        
        try:
            prompt = self._create_classification_prompt(text_content[:2000])
            
            response = await self.llm_service.generate_async(
                prompt=prompt,
                max_tokens=100,
                temperature=0.1,  # Низкая температура для точности
                stream=False
            )
            
            # Парсим ответ
            result = self._parse_ai_response(response, rule_type)
            return result
            
        except Exception as e:
            logger.error(f"Ошибка AI-классификации: {e}")
            return {
                "type": rule_type,
                "confidence": 0.6,
                "reason": f"Ошибка AI, использованы правила: {str(e)}",
                "method": "rule_fallback"
            }
    
    def _create_classification_prompt(self, text_content: str) -> str:
        """Создает промпт для классификации"""
        return f"""Ты - эксперт по российскому праву. Определи тип документа.

Документ (первые 2000 символов):
{text_content}

Типы документов:
- codex: Кодекс (Гражданский кодекс РФ, Уголовный кодекс РФ, Трудовой кодекс РФ и т.д.)
- federal_law: Федеральный закон (ФЗ, например "О защите прав потребителей")
- supreme_court_resolution: Постановление Верховного Суда РФ или Пленума ВС РФ
- resolution: Постановление (Правительства РФ, министерств, ведомств)
- decree: Указ Президента РФ
- order: Приказ (министерств, ведомств, федеральных служб)
- other: Другое (не подходит ни к одной категории)

Верни ТОЛЬКО JSON в формате:
{{
    "type": "один из типов выше",
    "confidence": число от 0.0 до 1.0,
    "reason": "краткое объяснение (1-2 предложения)"
}}

Ответ (только JSON, без дополнительного текста):"""
    
    def _parse_ai_response(self, response: str, fallback_type: str) -> Dict[str, Any]:
        """Парсит ответ от AI"""
        try:
            # Пытаемся найти JSON в ответе
            response = response.strip()
            
            # Убираем markdown код блоки если есть
            if response.startswith('```'):
                lines = response.split('\n')
                response = '\n'.join(lines[1:-1]) if len(lines) > 2 else response
            
            # Парсим JSON
            result = json.loads(response)
            
            # Валидация
            valid_types = [
                'codex', 'federal_law', 'supreme_court_resolution',
                'resolution', 'decree', 'order', 'other'
            ]
            
            if result.get('type') not in valid_types:
                result['type'] = fallback_type
            
            result['method'] = 'ai'
            return result
            
        except json.JSONDecodeError:
            # Если не JSON - пытаемся извлечь тип из текста
            response_lower = response.lower()
            for doc_type in ['codex', 'federal_law', 'supreme_court_resolution', 
                           'resolution', 'decree', 'order']:
                if doc_type in response_lower:
                    return {
                        "type": doc_type,
                        "confidence": 0.7,
                        "reason": "Извлечено из текстового ответа AI",
                        "method": "ai_text"
                    }
            
            # Fallback на правило
            return {
                "type": fallback_type,
                "confidence": 0.6,
                "reason": "Не удалось распарсить ответ AI",
                "method": "rule_fallback"
            }
    
    async def classify_batch(
        self, 
        documents: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Классифицирует несколько документов за раз (батчинг)
        Эффективнее чем по одному
        """
        results = []
        
        for doc in documents:
            result = await self.classify_document_ai(
                text_content=doc.get('text', ''),
                file_name=doc.get('file_name', ''),
                document_id=doc.get('document_id', '')
            )
            results.append(result)
        
        return results


# Глобальный экземпляр
ai_document_classifier = AIDocumentClassifier()


# Удобная функция для использования
async def classify_document_with_ai(
    text_content: str,
    file_name: str = "",
    document_id: str = ""
) -> str:
    """
    Простая функция для классификации документа
    Возвращает только тип (string)
    """
    result = await ai_document_classifier.classify_document_ai(
        text_content=text_content,
        file_name=file_name,
        document_id=document_id
    )
    return result['type']


def classify_document_with_ai_sync(
    text_content: str,
    file_name: str = "",
    document_id: str = ""
) -> str:
    """
    Синхронная версия для использования в синхронном коде
    Возвращает только тип (string)
    """
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Если loop уже запущен, используем rule-based
            from .vector_store_service import determine_document_type
            return determine_document_type(file_name, document_id, text_content)
        else:
            result = loop.run_until_complete(
                ai_document_classifier.classify_document_ai(
                    text_content=text_content,
                    file_name=file_name,
                    document_id=document_id
                )
            )
            return result['type']
    except RuntimeError:
        # Нет event loop, создаем новый
        result = asyncio.run(
            ai_document_classifier.classify_document_ai(
                text_content=text_content,
                file_name=file_name,
                document_id=document_id
            )
        )
        return result['type']

