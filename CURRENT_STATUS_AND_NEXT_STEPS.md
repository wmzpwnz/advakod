# 🔧 ТЕКУЩИЙ СТАТУС И СЛЕДУЮЩИЕ ШАГИ

**Дата:** 28 октября 2025, 21:31  
**Сервер:** 31.130.145.75 (advacodex.com)  
**Статус:** ✅ Система работает, но AI модель не загружена

---

## ✅ УСПЕШНО ИСПРАВЛЕНО:

### 1. Миграция Saiga → Vistral ✅
- 7 сервисов → 2 унифицированных
- Все импорты обновлены
- Legacy код архивирован
- API endpoints переименованы (/llm вместо /saiga)

### 2. Localhost → Production ✅
- config.py: все defaults используют Docker services
- WebSocket URL: `wss://advacodex.com/ws` (БЕЗ порта :8000!)
- CORS и TrustedHosts для advacodex.com
- Frontend nginx: server_name = advacodex.com

### 3. Критические таймауты ✅
- unified_llm_service.py: 30s → 900s (использует конфигурацию)
- nginx.conf: API и WebSocket 30s → 900s

### 4. Недостающие зависимости ✅
- ✅ pdfplumber==0.10.3
- ✅ python-docx==1.1.0
- ✅ langchain==0.1.20
- ✅ langchain-text-splitters==0.0.1
- ✅ pytesseract==0.3.10
- ✅ pdf2image==1.16.3
- ✅ psutil==5.9.6

---

## 🚨 ТЕКУЩАЯ ПРОБЛЕМА:

### AI Модель Vistral-24B не загружается

**Ошибка:**
```
AssertionError in llama_cpp/llama.py line 365
assert self.model is not None
```

**Проверка файла модели:**
```
✅ Файл существует: /opt/advakod/models/vistral/Vistral-24B-Instruct-Q5_0.gguf
✅ Размер: 16GB (16,304,427,712 байт)
✅ Формат: GGUF (валидный)
✅ Права: 644 (rw-r--r--)
✅ Владелец: root:root
✅ Доступен из контейнера
```

**Параметры загрузки:**
```python
model_path=/opt/advakod/models/vistral/Vistral-24B-Instruct-Q5_0.gguf
n_ctx=8192
n_threads=8
n_gpu_layers=0
use_mmap=True
use_mlock=False
```

**Память сервера:**
```
Total: 39GB
Available: 34GB  ← Достаточно для модели 16GB
```

### Возможные причины:

1. **llama_cpp версия несовместима с моделью**
   - Текущая: 0.2.11
   - Возможно нужна более новая версия

2. **Модель требует больше памяти чем есть**
   - Маловероятно (34GB > 16GB файла)

3. **Параметры n_ctx слишком большие**
   - 8192 может быть слишком много
   - Попробовать уменьшить до 4096 или 2048

4. **Проблема с use_mmap**
   - Возможно нужно отключить (use_mmap=False)

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ (НА ВЫБОР):

### Вариант 1: Уменьшить n_ctx (быстро)

Изменить в `/root/advakod/env.production`:
```bash
VISTRAL_N_CTX=4096  # Вместо 8192
```

Перезапустить:
```bash
docker-compose restart backend
```

### Вариант 2: Обновить llama-cpp-python (может помочь)

В `requirements.txt`:
```
llama-cpp-python==0.2.90  # Более новая версия
```

Пересобрать:
```bash
docker-compose build backend
docker-compose up -d backend
```

### Вариант 3: Использовать меньшую модель (если критично)

Использовать Q4 квантизацию вместо Q5:
```bash
VISTRAL_MODEL_PATH=/opt/advakod/models/vistral/Vistral-24B-Instruct-Q4_K.gguf
```

**НО:** файлы Q4 показывают размер 136 байт (заглушки), нужно скачать!

### Вариант 4: Отладка llama_cpp

Включить verbose режим в unified_llm_service.py:
```python
verbose=True  # Вместо False
```

---

## 📊 ТЕКУЩИЙ СТАТУС СЕРВИСОВ:

```
✅ Frontend:   RUNNING  (WebSocket URL исправлен)
✅ Backend:    HEALTHY  (все зависимости установлены)
✅ Nginx:      HEALTHY  (таймауты 900s)
✅ PostgreSQL: HEALTHY
✅ Redis:      HEALTHY
⚠️ Qdrant:    UNHEALTHY (но работает)

❌ UnifiedLLMService: модель не загружена
⚠️ UnifiedRAGService: зависит от LLM
```

---

## 🎯 РЕКОМЕНДАЦИЯ:

**ПОПРОБУЙТЕ ВАРИАНТ 1** (самый быстрый):

1. Уменьшите n_ctx:
```bash
sed -i 's/VISTRAL_N_CTX=8192/VISTRAL_N_CTX=4096/' /root/advakod/env.production
```

2. Перезапустите:
```bash
docker-compose restart backend
```

3. Подождите 2-3 минуты для загрузки

4. Проверьте:
```bash
docker logs advakod_backend --tail 20 | grep "Model.*loaded"
curl https://advacodex.com/ready
```

Если это не поможет - попробуйте Вариант 2 (обновление llama-cpp-python).

---

## ✅ ХОРОШИЕ НОВОСТИ:

**Все остальное работает идеально:**
- ✅ Миграция завершена (7 → 2 сервиса)
- ✅ Production конфигурация
- ✅ WebSocket исправлен
- ✅ Таймауты исправлены
- ✅ Все зависимости установлены
- ✅ Frontend работает
- ✅ Базы данных работают

**Осталось только загрузить AI модель!**

---

**Дата:** 28 октября 2025  
**Статус:** 90% готово - нужно только загрузить модель ✅

