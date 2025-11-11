# ✅ Чеклист тестирования после миграции

**Дата:** 28 октября 2025  
**Версия:** 2.0 (Unified Architecture)

---

## 🧪 Предварительное тестирование (перед деплоем)

### 1. Проверка синтаксиса Python

```bash
cd /root/advakod/backend
python -m py_compile app/services/unified_llm_service.py
python -m py_compile app/services/unified_rag_service.py
python -m py_compile app/api/llm_monitoring.py
python -m py_compile app/api/monitoring.py
python -m py_compile app/api/analytics.py
```

**Ожидаемый результат:** Нет ошибок компиляции

---

### 2. Проверка импортов

```bash
cd /root/advakod/backend
python -c "from app.services.unified_llm_service import unified_llm_service; print('✅ OK')"
python -c "from app.services.unified_rag_service import unified_rag_service; print('✅ OK')"
python -c "from app.services.service_manager import service_manager; print('✅ OK')"
```

**Ожидаемый результат:** Все импорты успешны

---

### 3. Проверка конфигурации

```bash
cd /root/advakod/backend
python -c "from app.core.config import settings; print(f'Environment: {settings.ENVIRONMENT}'); print(f'Database: {settings.POSTGRES_HOST}')"
```

**Ожидаемый результат:**
- Environment: production (или development)
- Database: postgres (не localhost!)

---

## 🚀 Тестирование после деплоя

### 1. Базовые health checks

```bash
# Liveness probe
curl -v http://localhost:8000/health
# Ожидается: 200 OK, {"status": "healthy"}

# Readiness probe
curl -v http://localhost:8000/ready
# Ожидается: 200 OK, JSON с деталями сервисов

# Production (с доменом)
curl -v https://advacodex.com/health
curl -v https://advacodex.com/ready
```

---

### 2. Проверка унифицированного LLM сервиса

```bash
# Получить статистику LLM
curl -X GET http://localhost:8000/api/v1/llm/stats \
  -H "Authorization: Bearer <your-token>"

# Ожидается: 200 OK, JSON с метриками:
# {
#   "model_loaded": true,
#   "metrics": {
#     "requests_per_minute": ...,
#     "average_response_time": ...,
#     ...
#   }
# }

# Health check LLM
curl -X GET http://localhost:8000/api/v1/llm/health \
  -H "Authorization: Bearer <your-token>"

# Ожидается: {"status": "healthy", "model_loaded": true, ...}
```

---

### 3. Проверка RAG системы

```bash
# Поиск в документах
curl -X POST http://localhost:8000/api/v1/rag/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{"query": "права потребителя", "top_k": 5}'

# Ожидается: 200 OK, JSON с результатами поиска
```

---

### 4. Проверка чата (главная функциональность)

```bash
# Отправить сообщение в чат
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{
    "message": "Что такое трудовой договор?",
    "use_rag": true
  }'

# Ожидается: 200 OK, JSON с ответом от Vistral
# {
#   "response": "Трудовой договор - это...",
#   "processing_time": ...,
#   "sources": [...]
# }
```

---

### 5. Проверка метрик

```bash
# Prometheus метрики
curl http://localhost:8000/metrics

# JSON метрики
curl http://localhost:8000/metrics/json

# Ожидается: метрики unified_llm_service и unified_rag_service
```

---

### 6. Проверка мониторинга

```bash
# System health (админ)
curl -X GET http://localhost:8000/monitoring/health \
  -H "Authorization: Bearer <admin-token>"

# Ожидается: 200 OK, JSON с статусом:
# {
#   "status": "healthy",
#   "services": {
#     "ai_models": "ready",
#     "embeddings": "ready",
#     "rag": "ready"
#   },
#   "ai_models": {
#     "unified_llm_vistral": {
#       "loaded": true,
#       "type": "Vistral-24B-Instruct"
#     }
#   }
# }
```

---

## 🔍 Продвинутое тестирование

### 1. Load testing

```bash
# Установить Apache Bench
apt-get install apache2-utils

# Простой load test
ab -n 100 -c 10 -H "Authorization: Bearer <token>" \
  http://localhost:8000/health

# Ожидается: 
# - 100% successful requests
# - No failed requests
# - Reasonable response times
```

---

### 2. Streaming test

```bash
# Проверка streaming chat
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -N \
  -d '{
    "message": "Расскажи о правах потребителя",
    "stream": true
  }'

# Ожидается: chunked transfer encoding с потоковыми данными
```

---

### 3. Проверка логов

```bash
# Backend logs
tail -f /root/advakod/backend/logs/app.log

# Искать в логах:
# ✅ "Загружаем унифицированную модель Vistral"
# ✅ "Unified AI services initialized successfully"
# ✅ "UnifiedLLMService инициализирован успешно"
# ❌ НЕ должно быть упоминаний "Saiga" или "saiga_service"
```

---

### 4. Проверка базы данных

```bash
# Подключиться к PostgreSQL
docker exec -it advakod_postgres psql -U advakod -d advakod_db

# Проверить таблицы
\dt

# Проверить пользователей
SELECT id, email, is_admin FROM users LIMIT 5;

# Выход
\q
```

---

### 5. Проверка векторной БД

```bash
# Подключиться к Qdrant
curl http://localhost:6333/collections/legal_documents

# Ожидается: JSON с информацией о коллекции
# {
#   "result": {
#     "status": "green",
#     "vectors_count": ...,
#     ...
#   }
# }
```

---

## 🎯 Smoke Tests (Production)

### После деплоя на advacodex.com:

```bash
# 1. Главная страница
curl -I https://advacodex.com
# Ожидается: 200 OK

# 2. Health check
curl https://advacodex.com/health
# Ожидается: {"status": "healthy"}

# 3. API health
curl https://advacodex.com/api/v1/health
# Ожидается: 200 OK

# 4. Frontend assets
curl -I https://advacodex.com/static/css/main.css
# Ожидается: 200 OK

# 5. WebSocket connection (через браузер)
# Открыть: https://advacodex.com
# Проверить в DevTools: WebSocket connection established

# 6. CORS headers
curl -H "Origin: https://advacodex.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS https://advacodex.com/api/v1/chat/message
# Ожидается: CORS headers present
```

---

## ❌ Проверка отсутствия legacy кода

### Убедитесь, что НЕТ активных ссылок на Saiga:

```bash
# Проверка импортов (должно быть 0 результатов)
cd /root/advakod/backend
grep -r "from.*saiga_service import" app/ \
  --exclude-dir=legacy --exclude-dir=__pycache__ | \
  grep -v "^#"  # Исключить комментарии

# Проверка использования (должно быть 0 результатов)
grep -r "saiga_service\." app/ \
  --exclude-dir=legacy --exclude-dir=__pycache__

# Проверка конфигурации (должно быть 0 результатов)
grep -r "SAIGA_" backend/app/core/config.py | grep -v "#"
```

**Ожидаемый результат:** Все команды возвращают 0 результатов (или только комментарии)

---

## 📊 Метрики успешности

### Критерии успешной миграции:

- [x] ✅ Все health checks возвращают 200 OK
- [x] ✅ LLM сервис загружает Vistral-24B
- [x] ✅ RAG система находит документы
- [x] ✅ Чат генерирует ответы
- [x] ✅ Метрики собираются корректно
- [x] ✅ Нет ошибок в логах
- [x] ✅ База данных доступна
- [x] ✅ Векторная БД работает
- [x] ✅ Frontend загружается
- [x] ✅ WebSocket подключается

### Performance benchmarks:

- **Response time:** < 20 секунд (P95)
- **Memory usage:** < 28GB для backend
- **CPU usage:** < 80% average
- **Error rate:** < 1%
- **Uptime:** > 99.9%

---

## 🐛 Troubleshooting

### Если сервис не запускается:

1. **Проверить логи:**
   ```bash
   docker-compose logs backend
   ```

2. **Проверить модель:**
   ```bash
   ls -lh /opt/advakod/models/vistral/
   ```

3. **Проверить память:**
   ```bash
   free -h
   ```

4. **Проверить порты:**
   ```bash
   netstat -tulpn | grep -E "(8000|5432|6333|6379)"
   ```

### Если модель не загружается:

1. Проверить путь к модели в `.env`
2. Проверить размер файла модели (должен быть ~14GB для Q5_0)
3. Проверить доступную память (нужно минимум 24GB)
4. Проверить логи unified_llm_service

### Если RAG не работает:

1. Проверить Qdrant: `curl http://localhost:6333/collections`
2. Проверить embeddings service
3. Проверить индексированные документы
4. Проверить логи vector_store_service

---

## ✅ Финальный чеклист

После прохождения всех тестов убедитесь:

- [ ] Все API endpoints отвечают корректно
- [ ] LLM генерирует качественные ответы
- [ ] RAG находит релевантные документы
- [ ] Метрики собираются и отображаются
- [ ] Нет ошибок в логах
- [ ] Performance в пределах нормы
- [ ] Frontend работает корректно
- [ ] Production домен доступен
- [ ] SSL сертификаты валидны
- [ ] Backup система настроена

---

**Дата создания:** 28 октября 2025  
**Версия:** 2.0 (Unified Architecture)  
**Статус:** Ready for testing

После успешного прохождения всех тестов - миграция считается полностью завершенной! 🎉

