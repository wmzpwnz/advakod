# Пример использования AI-классификации

## 📝 Базовое использование

```python
from app.services.ai_document_classifier import classify_document_with_ai

# Простая классификация
doc_type = await classify_document_with_ai(
    text_content="ФЕДЕРАЛЬНЫЙ ЗАКОН от 01.05.2019 N 51-ФЗ...",
    file_name="law.pdf",
    document_id="doc_123"
)
# Вернет: "federal_law"
```

## 🎯 Детальная классификация

```python
from app.services.ai_document_classifier import ai_document_classifier

result = await ai_document_classifier.classify_document_ai(
    text_content="ПОСТАНОВЛЕНИЕ Пленума Верховного Суда РФ...",
    file_name="resolution.pdf"
)

print(result)
# {
#     "type": "supreme_court_resolution",
#     "confidence": 0.95,
#     "reason": "Это постановление Пленума ВС РФ",
#     "method": "ai"
# }
```

## 🔄 Интеграция в vector_store_service

```python
# В vector_store_service.py, метод add_document:

# Определяем тип документа
if "document_type" not in sanitized_metadata:
    # Сначала пробуем правила (быстро)
    file_name = sanitized_metadata.get("file_name", "")
    doc_type = determine_document_type(file_name, document_id, content)
    
    # Если не уверены - используем AI
    if doc_type == 'other' and self.use_ai_classification:
        from .ai_document_classifier import classify_document_with_ai
        doc_type = await classify_document_with_ai(
            text_content=content,
            file_name=file_name,
            document_id=document_id
        )
    
    sanitized_metadata["document_type"] = doc_type
```

## ⚡ Оптимизация производительности

### Кэширование результатов

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def get_cached_type(text_hash: str) -> str:
    """Кэширует результаты классификации"""
    # ...

# Использование
text_hash = hashlib.md5(text_content[:500].encode()).hexdigest()
doc_type = get_cached_type(text_hash)
```

### Батчинг для массовой загрузки

```python
# В load_documents_optimized.py

# Собираем документы для AI-классификации
uncertain_docs = []
for chunk in chunks:
    rule_type = determine_document_type(...)
    if rule_type == 'other':
        uncertain_docs.append({
            'text': chunk.get('text', ''),
            'file_name': file_name,
            'document_id': document_id
        })

# Классифицируем батчем
if uncertain_docs:
    ai_results = await ai_document_classifier.classify_batch(uncertain_docs)
    # Используем результаты
```

## 📊 Сравнение методов

| Ситуация | Rule-Based | AI-Based | Гибридный |
|----------|-----------|----------|-----------|
| Кодексы | ✅ 100% | ✅ 100% | ✅ 100% |
| Стандартные законы | ✅ 90% | ✅ 95% | ✅ 92% |
| Нестандартные документы | ❌ 60% | ✅ 95% | ✅ 90% |
| Скорость | ⚡ 1 мс | 🐌 500-2000 мс | ⚡ 1-500 мс |

## 🎛️ Настройка

```python
# Отключить AI (только правила)
ai_document_classifier.use_ai = False

# Включить AI для всех документов
ai_document_classifier.use_ai = True
```

