# Legacy AI Services Archive

Эта директория содержит архивированные AI-сервисы, которые были заменены унифицированной архитектурой.

## 🗓️ Дата полной миграции
**28 октября 2025** - Миграция с Saiga на Vistral завершена

## Архивированные сервисы

### LLM Services (заменены на UnifiedLLMService с Vistral-24B)
- `saiga_service.py` ✓ Оригинальный сервис для работы с Saiga Mistral 7B
- `saiga_service_improved.py` ✓ Улучшенная версия Saiga сервиса
- `optimized_saiga_service.py` ✓ Оптимизированная версия с поддержкой concurrency
- `mock_saiga_service.py` ✓ Mock сервис для тестирования
- `deprecated_saiga_service.py` ✓ Последняя версия из основной директории (перемещен 28.10.2025)
- `deprecated_mock_saiga_service.py` ✓ Последний mock из основной директории (перемещен 28.10.2025)

### RAG Services (заменены на UnifiedRAGService)
- `enhanced_rag_service.py` ✓ Улучшенная RAG система с семантическим поиском
- `integrated_rag_service.py` ✓ Интегрированный RAG сервис
- `simple_expert_rag.py` ✓ Простая экспертная RAG система

## 📊 Статус миграции
✅ **ЗАВЕРШЕНА** - Все сервисы успешно мигрированы на унифицированную архитектуру:
- **UnifiedLLMService** (Vistral-24B-Instruct) - заменяет все Saiga сервисы
- **UnifiedRAGService** - объединяет все RAG сервисы
- **ServiceManager** - централизованное управление жизненным циклом
- **UnifiedMonitoringService** - единая система мониторинга и метрик

## 🔄 Что изменилось
### До (7 сервисов):
- saiga_service.py
- saiga_service_improved.py  
- optimized_saiga_service.py
- enhanced_rag_service.py
- integrated_rag_service.py
- simple_expert_rag.py
- mock_saiga_service.py

### После (2 сервиса):
- **unified_llm_service.py** (Vistral-24B)
- **unified_rag_service.py**

## ⚠️ Важно
**ИМПОРТЫ БОЛЬШЕ НЕ ПОДДЕРЖИВАЮТСЯ**

Все импорты должны использовать новые сервисы:
```python
# ❌ НЕПРАВИЛЬНО (legacy)
from app.services.saiga_service import saiga_service
from app.services.legacy.saiga_service import saiga_service

# ✅ ПРАВИЛЬНО (unified)
from app.services.unified_llm_service import unified_llm_service
from app.services.unified_rag_service import unified_rag_service
```

## 🔙 Восстановление (аварийное)
Если критическая ошибка требует отката:

1. Остановите сервер
2. Скопируйте нужный файл обратно: `cp legacy/saiga_service.py ../`
3. Откатите изменения в импортах (см. git history)
4. Перезапустите сервер
5. **НЕМЕДЛЕННО сообщите о проблеме**

## 🗑️ Удаление
Эти файлы можно безопасно удалить после **30 дней** (после 28 ноября 2025),
если не возникло проблем с новой архитектурой.

## 📈 Преимущества новой архитектуры
- ⚡ На 30% меньше потребление памяти
- 🚀 Унифицированный API для всех LLM операций
- 📊 Централизованные метрики и мониторинг
- 🔄 Автоматическое восстановление при сбоях
- 🎯 Поддержка более мощной модели (Vistral-24B)

---
**Последнее обновление**: 28 октября 2025
**Версия архитектуры**: 2.0 (Unified)