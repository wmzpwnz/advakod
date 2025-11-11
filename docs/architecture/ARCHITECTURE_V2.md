# 🏗️ АДВАКОД - Архитектура v2.0 (Unified)

**Версия:** 2.0  
**Дата обновления:** 28 октября 2025  
**Статус:** Production Ready

---

## 📋 Обзор

АДВАКОД v2.0 представляет собой полностью перестроенную AI-архитектуру с фокусом на:
- **Унификацию** - 2 основных сервиса вместо 7
- **Производительность** - оптимизация памяти и процессора
- **Масштабируемость** - поддержка высокой нагрузки
- **Надежность** - автоматическое восстановление
- **Мониторинг** - централизованные метрики

---

## 🎯 Унифицированные AI-сервисы

### 1. UnifiedLLMService (Vistral-24B-Instruct)

**Файл:** `/backend/app/services/unified_llm_service.py`

**Назначение:** Единый сервис для всех операций с языковыми моделями.

#### Основные компоненты:

```python
class UnifiedLLMService:
    - model: Llama                           # Vistral-24B модель
    - _request_queue: PriorityQueue         # Приоритизация запросов
    - _active_requests: Dict                 # Отслеживание активных
    - _request_history: List[LLMResponse]   # История для метрик
    - _stats: Dict                           # Статистика производительности
```

#### Ключевые возможности:

1. **Управление очередью:**
   - Приоритизация запросов (LOW, NORMAL, HIGH, URGENT)
   - Максимальный размер очереди: 50 запросов
   - FIFO с поддержкой приоритетов

2. **Конкурентность:**
   - Настраиваемое количество параллельных запросов (default: 3)
   - Семафоры для контроля конкурентности
   - Защита от перегрузки

3. **Streaming:**
   - Real-time потоковая генерация
   - Поддержка WebSocket
   - Chunked responses

4. **Метрики:**
   - Requests per minute
   - Average/P95 response time
   - Error rate
   - Queue length
   - Memory/CPU usage

#### Методы API:

```python
# Основная генерация
async def generate_response(
    prompt: str,
    context: Optional[str] = None,
    stream: bool = True,
    max_tokens: int = 1024,
    temperature: float = 0.3,
    top_p: float = 0.8,
    user_id: str = "anonymous",
    priority: RequestPriority = RequestPriority.NORMAL
) -> AsyncGenerator[str, None]

# Health check
async def health_check() -> ServiceHealth

# Метрики
def get_metrics() -> LLMMetrics

# Проверка состояния
def is_model_loaded() -> bool
```

#### Конфигурация:

```bash
VISTRAL_MODEL_PATH=/opt/advakod/models/vistral/Vistral-24B-Instruct-Q5_0.gguf
VISTRAL_N_CTX=8192              # Размер контекста
VISTRAL_N_THREADS=8             # Количество потоков
VISTRAL_MAX_CONCURRENCY=3       # Параллельные запросы
VISTRAL_INFERENCE_TIMEOUT=900   # Таймаут (секунды)
VISTRAL_TEMPERATURE=0.3         # Температура генерации
VISTRAL_TOP_P=0.8              # Top-p sampling
VISTRAL_TOKEN_MARGIN=32        # Резерв токенов
```

---

### 2. UnifiedRAGService

**Файл:** `/backend/app/services/unified_rag_service.py`

**Назначение:** Унифицированная система RAG (Retrieval-Augmented Generation).

#### Основные компоненты:

```python
class UnifiedRAGService:
    - vector_store: VectorStore          # Qdrant
    - embeddings: EmbeddingsService      # Sentence Transformers
    - llm: UnifiedLLMService            # Для генерации
    - cache: Dict                        # 5-минутный кэш
    - search_strategies: List            # Hybrid search
```

#### Возможности:

1. **Гибридный поиск:**
   - Semantic search (векторный)
   - Keyword search (BM25)
   - Reciprocal Rank Fusion (RRF)

2. **Re-ranking:**
   - Cross-Encoder для улучшения релевантности
   - Настраиваемый top-k

3. **Кэширование:**
   - TTL: 5 минут
   - LRU eviction
   - Автоматическая инвалидация

4. **Chunking:**
   - Умное разбиение документов
   - Сохранение контекста
   - Overlap для связности

#### Методы API:

```python
# Поиск документов
async def search_documents(
    query: str,
    top_k: int = 20,
    use_hybrid: bool = True,
    enable_reranking: bool = True
) -> List[SearchResult]

# RAG генерация
async def generate_with_rag(
    query: str,
    max_results: int = 5,
    context_window: int = 4000
) -> RAGResponse

# Управление векторной БД
async def index_document(
    content: str,
    metadata: Dict
) -> str

# Статус
def is_ready() -> bool
def get_status() -> Dict
```

#### Конфигурация:

```bash
RAG_MAX_RESULTS=20
RAG_SIMILARITY_THRESHOLD=0.7
RAG_RERANK_TOP_K=5
RAG_CONTEXT_WINDOW=4000
RAG_CHUNK_OVERLAP=200
RAG_ENABLE_RERANKING=true
RAG_ENABLE_HYBRID_SEARCH=true
```

---

### 3. ServiceManager

**Файл:** `/backend/app/services/service_manager.py`

**Назначение:** Централизованное управление жизненным циклом всех AI-сервисов.

#### Функциональность:

1. **Инициализация:**
   - Последовательная загрузка с учетом зависимостей
   - Проверка готовности
   - Таймауты и повторные попытки

2. **Мониторинг:**
   - Health checks каждые 30 секунд
   - Автоматическое обнаружение сбоев
   - Метрики состояния

3. **Auto-recovery:**
   - Автоматический перезапуск при сбоях
   - До 3 попыток восстановления
   - Exponential backoff

4. **Graceful shutdown:**
   - Завершение активных запросов
   - Сохранение состояния
   - Очистка ресурсов

#### Методы API:

```python
# Инициализация
async def initialize_services() -> bool

# Получение статуса
def get_service_status() -> SystemHealth

# Управление
async def restart_service(service_name: str) -> bool
async def shutdown_services() -> None
```

---

### 4. UnifiedMonitoringService

**Файл:** `/backend/app/services/unified_monitoring_service.py`

**Назначение:** Единая система мониторинга и сбора метрик.

#### Возможности:

1. **Метрики:**
   - Prometheus-совместимый формат
   - Real-time сбор
   - Исторические данные (1000 последних)

2. **Алерты:**
   - 6 предустановленных правил
   - Настраиваемые пороги
   - Email/Webhook уведомления

3. **Dashboard:**
   - JSON API для визуализации
   - WebSocket для real-time обновлений
   - Grafana-совместимый формат

#### Метрики:

```python
# LLM метрики
llm_requests_total
llm_response_time_seconds
llm_error_rate
llm_queue_length
llm_concurrent_requests

# RAG метрики
rag_search_time_seconds
rag_cache_hit_rate
rag_vector_store_size
rag_documents_indexed

# Системные метрики
system_memory_usage_mb
system_cpu_usage_percent
system_disk_usage_gb
```

---

## 🔧 Инфраструктура

### Docker Compose (Production)

**Файл:** `/docker-compose.prod.yml`

```yaml
services:
  # PostgreSQL - основная БД
  postgres:
    image: postgres:15-alpine
    ports: ["5432:5432"]
    
  # Qdrant - векторная БД
  qdrant:
    image: qdrant/qdrant:v1.7.0
    ports: ["6333:6333"]
    
  # Redis - кэширование
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    
  # Backend - FastAPI + Vistral
  backend:
    build: ./backend
    environment:
      - VISTRAL_MODEL_PATH=/opt/advakod/models/vistral/...
      - DATABASE_URL=postgresql://...@postgres:5432/...
      - QDRANT_HOST=qdrant
      - REDIS_URL=redis://redis:6379
    deploy:
      resources:
        limits:
          memory: 28G  # Для Vistral-24B
          
  # Frontend - React
  frontend:
    build: ./frontend
    environment:
      - REACT_APP_API_URL=https://advacodex.com/api/v1
      
  # Nginx - reverse proxy
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
```

---

## 📊 Архитектурные паттерны

### 1. Service Layer Pattern

Все AI-функциональность изолирована в сервисном слое:
```
app/
├── api/              # REST endpoints
├── services/         # Бизнес-логика
│   ├── unified_llm_service.py
│   ├── unified_rag_service.py
│   └── service_manager.py
├── core/             # Утилиты
└── models/           # ORM модели
```

### 2. Dependency Injection

Сервисы внедряются через DI:
```python
@router.post("/chat")
async def chat(
    llm: UnifiedLLMService = Depends(get_llm_service),
    rag: UnifiedRAGService = Depends(get_rag_service)
):
    ...
```

### 3. Repository Pattern

Доступ к данным через репозитории:
```python
class UserRepository:
    async def find_by_id(self, user_id: int) -> User
    async def save(self, user: User) -> User
```

### 4. Factory Pattern

Создание сервисов через фабрики:
```python
class ServiceFactory:
    @staticmethod
    def create_llm_service() -> UnifiedLLMService:
        return UnifiedLLMService()
```

---

## 🔐 Безопасность

### 1. Аутентификация и авторизация

- **JWT токены** для API
- **2FA** для админ-панели
- **Role-based access control (RBAC)**
- **API key** для внешних интеграций

### 2. Rate Limiting

- **ML-based rate limiting** с адаптацией
- **IP-based throttling**
- **User-based quotas**
- **Endpoint-specific limits**

### 3. Валидация входных данных

- **Pydantic схемы** для всех endpoints
- **SQL injection protection** через ORM
- **XSS protection** через sanitization
- **CSRF tokens** для форм

### 4. Шифрование

- **Encryption at rest** для чувствительных данных
- **TLS/SSL** для всех соединений
- **Secrets management** через environment variables

---

## 📈 Масштабирование

### Горизонтальное масштабирование

```yaml
# Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: advakod-backend
spec:
  replicas: 3  # Несколько инстансов
  template:
    spec:
      containers:
      - name: backend
        image: advakod-backend:2.0
        resources:
          limits:
            memory: "28Gi"
            cpu: "8"
```

### Вертикальное масштабирование

- **Увеличение VISTRAL_N_THREADS** для более мощного CPU
- **Увеличение VISTRAL_N_CTX** для большего контекста
- **GPU acceleration** через VISTRAL_N_GPU_LAYERS

### Кэширование

- **Redis** для hot data
- **CDN** для статики
- **Application-level cache** для RAG результатов

---

## 🧪 Тестирование

### Unit тесты

```bash
# Запуск unit тестов
pytest backend/tests/unit/ -v
```

### Integration тесты

```bash
# Запуск integration тестов
pytest backend/tests/integration/ -v
```

### Performance тесты

```bash
# Load testing
locust -f backend/tests/performance/locustfile.py
```

### End-to-end тесты

```bash
# Cypress E2E
cd frontend && npm run cypress:run
```

---

## 📝 Логирование

### Структурированное логирование

```python
logger.info(
    "LLM request processed",
    extra={
        "user_id": user.id,
        "request_id": request_id,
        "duration_ms": duration,
        "tokens_generated": tokens
    }
)
```

### Log levels:
- **DEBUG** - детальная отладка
- **INFO** - информационные сообщения
- **WARNING** - предупреждения
- **ERROR** - ошибки
- **CRITICAL** - критические сбои

### Централизация:
- **Elasticsearch/Kibana** для анализа
- **Sentry** для error tracking
- **Jaeger** для distributed tracing

---

## 🔄 CI/CD

### GitHub Actions workflow

```yaml
name: Deploy to Production
on:
  push:
    branches: [main]
    
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: pytest
      - name: Build Docker images
        run: docker-compose build
      - name: Deploy to server
        run: ./deploy.sh
```

---

## 📚 Дополнительная документация

- **API Documentation:** `/docs` (Swagger UI)
- **Legacy Services:** `/backend/app/services/legacy/README.md`
- **Migration Guide:** `/MIGRATION_COMPLETE.md`
- **Deployment Guide:** `/PRODUCTION_DEPLOYMENT_GUIDE.md`

---

## 🎯 Roadmap

### Q4 2025:
- [ ] GPU acceleration для Vistral
- [ ] Multi-modal support (изображения)
- [ ] Advanced caching strategies
- [ ] Kubernetes deployment

### Q1 2026:
- [ ] Distributed inference
- [ ] Model quantization (Q4 → Q8)
- [ ] Advanced analytics dashboard
- [ ] Mobile app integration

---

**Версия:** 2.0 (Unified Architecture)  
**Последнее обновление:** 28 октября 2025  
**Статус:** ✅ Production Ready

