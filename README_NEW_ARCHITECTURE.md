# АДВАКОД - ИИ-Юрист для РФ (Унифицированная Архитектура)

## 🚀 Обзор

АДВАКОД - это AI-powered юридическая платформа для Российской Федерации, построенная на унифицированной архитектуре AI-сервисов.

### ✨ Ключевые особенности

- **🤖 Унифицированные AI-сервисы**: 2 основных сервиса вместо 7
- **⚡ Высокая производительность**: 10-15 запросов/минуту, P95 < 20 секунд
- **🔄 Автоматическое восстановление**: ServiceManager с health checks
- **📊 Комплексный мониторинг**: Метрики, алерты, дашборды
- **🎯 Vistral-24B**: Современная русскоязычная модель

## 🏗️ Архитектура

### Унифицированные AI-сервисы

```
┌─────────────────────────────────────────────────────────────┐
│                    ServiceManager                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ UnifiedLLMService│  │ UnifiedRAGService│  │ Monitoring   │ │
│  │                 │  │                 │  │ Service      │ │
│  │ • Vistral-24B   │  │ • Hybrid Search │  │ • Metrics    │ │
│  │ • Queue Mgmt    │  │ • RRF Fusion    │  │ • Alerts     │ │
│  │ • Streaming     │  │ • Caching       │  │ • Health     │ │
│  │ • 2-3 Concurrent│  │ • Re-ranking    │  │ • Dashboard  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Основные компоненты

#### 1. **UnifiedLLMService**
- **Модель**: Vistral-24B-Instruct (русскоязычная)
- **Конкурентность**: 2-3 параллельных запроса
- **Очередь**: Приоритизация запросов
- **Streaming**: Real-time ответы
- **Мониторинг**: Метрики производительности

#### 2. **UnifiedRAGService**
- **Гибридный поиск**: Semantic + Keyword
- **RRF**: Reciprocal Rank Fusion
- **Кэширование**: 5-минутный TTL
- **Re-ranking**: Cross-Encoder оптимизация
- **Chunking**: Умное разбиение документов

#### 3. **ServiceManager**
- **Инициализация**: Управление жизненным циклом
- **Health Checks**: Автоматическая проверка состояния
- **Auto Recovery**: Перезапуск при сбоях (до 3 попыток)
- **Graceful Shutdown**: Корректное завершение

#### 4. **UnifiedMonitoringService**
- **Метрики**: Prometheus совместимые
- **Алерты**: 6 предустановленных правил
- **Dashboard**: JSON API для визуализации
- **История**: 1000 последних событий

## 🔧 Конфигурация

### Основные параметры

```bash
# Vistral LLM
VISTRAL_MODEL_PATH=/opt/advakod/models/vistral-24b-instruct-q4_K_M.gguf
VISTRAL_MAX_CONCURRENCY=3
VISTRAL_N_CTX=8192
VISTRAL_INFERENCE_TIMEOUT=900

# RAG System
RAG_MAX_RESULTS=20
RAG_SIMILARITY_THRESHOLD=0.7
RAG_ENABLE_HYBRID_SEARCH=true
RAG_ENABLE_RERANKING=true

# Monitoring
SERVICE_HEALTH_CHECK_INTERVAL=30
MONITORING_COLLECTION_INTERVAL=30
```

## 📊 API Endpoints

### Основные endpoints

- `POST /api/v1/chat/enhanced` - Унифицированный чат с RAG
- `GET /ready` - Проверка готовности системы
- `GET /metrics` - Prometheus метрики
- `GET /metrics/json` - JSON метрики для дашборда

### Мониторинг

- `GET /health` - Liveness probe
- `GET /ready` - Readiness probe с детальным статусом
- `GET /metrics/json` - Комплексные метрики системы

## 🚀 Запуск

### Разработка

```bash
# Backend
cd backend
python main.py

# Frontend
cd frontend
npm start
```

### Production

```bash
# Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Или через скрипты
./DEPLOY_ALL_IN_ONE.sh
```

## 📈 Производительность

### Ключевые метрики

- **Throughput**: 10-15 запросов/минуту
- **Response Time**: P95 < 20 секунд
- **Concurrency**: 2-3 параллельных запроса
- **Memory**: -30% потребления
- **Startup**: < 30 секунд инициализация

### Мониторинг

- **LLM метрики**: requests/min, response time, error rate, queue length
- **RAG метрики**: search time, cache hit rate, vector store size
- **Системные**: CPU, память, диск, сетевые соединения
- **Алерты**: Автоматические уведомления при проблемах

## 🔄 Миграция

### Что изменилось

- **7 сервисов → 2**: Упрощенная архитектура
- **Saiga → Vistral**: Современная русскоязычная модель
- **Ручная инициализация → ServiceManager**: Автоматизация
- **Разрозненный мониторинг → Единая система**: Централизация

### Legacy поддержка

Старые сервисы архивированы в `app/services/legacy/` для совместимости.

## 🛠️ Разработка

### Структура проекта

```
backend/
├── app/
│   ├── services/
│   │   ├── unified_llm_service.py      # Единый LLM сервис
│   │   ├── unified_rag_service.py      # Единый RAG сервис
│   │   ├── service_manager.py          # Управление сервисами
│   │   ├── unified_monitoring_service.py # Мониторинг
│   │   └── legacy/                     # Архивированные сервисы
│   ├── api/                           # REST API endpoints
│   └── core/                          # Конфигурация и утилиты
```

### Добавление новых функций

1. **LLM функции**: Расширяйте `UnifiedLLMService`
2. **RAG функции**: Расширяйте `UnifiedRAGService`
3. **Мониторинг**: Добавляйте метрики в `UnifiedMonitoringService`
4. **API**: Создавайте endpoints в `app/api/`

## 📚 Документация

- **API**: `/docs` - Swagger UI
- **Метрики**: `/metrics` - Prometheus format
- **Статус**: `/ready` - Детальный статус системы

## 🔒 Безопасность

- **Rate Limiting**: ML-based ограничения
- **Input Validation**: Проверка входных данных
- **Security Headers**: Защитные заголовки
- **Audit Logging**: Логирование всех операций

## 🤝 Поддержка

Для вопросов по новой архитектуре:
1. Проверьте `/ready` endpoint для диагностики
2. Изучите метрики в `/metrics/json`
3. Проверьте логи ServiceManager
4. Обратитесь к документации legacy сервисов при необходимости

---

**Версия архитектуры**: 2.0 (Унифицированная)  
**Дата обновления**: ${new Date().toISOString().split('T')[0]}  
**Статус**: Production Ready ✅