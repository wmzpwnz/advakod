# ПЛАН ИСПРАВЛЕНИЙ - ИИ-ЮРИСТ

## 🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ (Фаза 1 - 1-2 недели)

### 1. Утечка секретов
**Приоритет:** CRITICAL  
**Время:** 2 часа  
**Исправление:**
```bash
# 1. Создать .env файл
cp ENV_EXAMPLE.txt .env

# 2. Сгенерировать новые секреты
export SECRET_KEY="$(openssl rand -base64 32)"
export ENCRYPTION_KEY="$(openssl rand -base64 32)"
export POSTGRES_PASSWORD="$(openssl rand -base64 16)"

# 3. Добавить в .gitignore
echo ".env" >> .gitignore
echo "config.env" >> .gitignore
```

### 2. Валидация входных данных
**Приоритет:** CRITICAL  
**Время:** 4 часа  
**Файлы:** `backend/app/api/chat.py`  
**Исправление:**
```python
from pydantic import BaseModel, validator, Field

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[int] = Field(None, ge=1)
    
    @validator('message')
    def validate_message(cls, v):
        # Проверка на XSS
        if any(tag in v.lower() for tag in ['<script', '<iframe', 'javascript:']):
            raise ValueError('Potentially malicious content detected')
        return v.strip()
```

### 3. Безопасность паролей
**Приоритет:** CRITICAL  
**Время:** 3 часа  
**Файлы:** `backend/app/services/auth_service.py`  
**Исправление:**
```python
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"], 
    deprecated="auto",
    argon2__memory_cost=65536,
    argon2__time_cost=3,
    argon2__parallelism=4
)
```

## 🔥 ВЫСОКИЕ ПРИОРИТЕТЫ (Фаза 2 - 2-3 недели)

### 1. RAG система
**Приоритет:** HIGH  
**Время:** 1 неделя  
**Файлы:** `backend/app/services/rag_service.py`  
**Исправления:**
- Добавить RRF для объединения BM25 и векторного поиска
- Реализовать reranking
- Добавить дедупликацию результатов

### 2. Чанкинг документов
**Приоритет:** HIGH  
**Время:** 3 дня  
**Файлы:** `backend/app/services/document_service.py`  
**Исправления:**
- Улучшить алгоритм чанкинга
- Добавить overlap между чанками
- Сохранять контекст

### 3. LoRA обучение
**Приоритет:** HIGH  
**Время:** 1 неделя  
**Файлы:** `backend/app/services/lora_training_service.py`  
**Исправления:**
- Исправить гиперпараметры
- Добавить валидацию данных
- Настроить мониторинг

## 📈 ПРОИЗВОДИТЕЛЬНОСТЬ (Фаза 3 - 1-2 недели)

### 1. Кэширование
**Приоритет:** HIGH  
**Время:** 2 дня  
**Исправление:**
```python
import redis
from functools import lru_cache

# Настройка Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)

@lru_cache(maxsize=1000)
def get_cached_response(query_hash: str) -> Optional[str]:
    return redis_client.get(query_hash)
```

### 2. Оптимизация БД
**Приоритет:** MEDIUM  
**Время:** 1 день  
**Исправление:**
```python
# Connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)
```

## 🧪 ТЕСТИРОВАНИЕ (Фаза 4 - 1 неделя)

### 1. Увеличить покрытие
**Приоритет:** HIGH  
**Время:** 3 дня  
**Цель:** Покрытие > 80%

### 2. Интеграционные тесты
**Приоритет:** MEDIUM  
**Время:** 2 дня  
**Добавить тесты для:**
- RAG системы
- LoRA обучения
- Векторного поиска

## 📊 МЕТРИКИ ПРИЕМКИ

### Функциональные
- [ ] Hit@5 ≥ 0.95
- [ ] Citation accuracy ≥ 0.9
- [ ] Hallucination rate < 0.02

### Производительность
- [ ] p95 latency < 2s (простые)
- [ ] p95 latency < 10s (сложные)
- [ ] GPU utilization < 90%

### Безопасность
- [ ] Нет секретов в коде
- [ ] Нет PII в логах
- [ ] Все внешние вызовы логируются

## 🎯 КОНТРОЛЬНЫЕ ТОЧКИ

### Неделя 1
- [ ] Секреты перемещены в переменные окружения
- [ ] Добавлена валидация входных данных
- [ ] Обновлена схема хеширования паролей

### Неделя 2-3
- [ ] RAG система исправлена
- [ ] Чанкинг документов улучшен
- [ ] LoRA обучение оптимизировано

### Неделя 4
- [ ] Кэширование настроено
- [ ] БД оптимизирована
- [ ] Тесты добавлены

## 📞 ОТВЕТСТВЕННЫЕ

- **Безопасность:** DevOps Engineer
- **RAG система:** ML Engineer  
- **Производительность:** Backend Developer
- **Тестирование:** QA Engineer

## 📅 ВРЕМЕННЫЕ РАМКИ

- **Фаза 1:** 1-2 недели
- **Фаза 2:** 2-3 недели  
- **Фаза 3:** 1-2 недели
- **Фаза 4:** 1 неделя
- **ИТОГО:** 5-8 недель
