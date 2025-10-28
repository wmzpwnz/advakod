# A2codeX - ИИ-Юрист для РФ

## 🚀 Описание

A2codeX (advacode.com) - это интеллектуальная система юридической помощи на базе искусственного интеллекта, специально разработанная для российского законодательства. Система использует передовые технологии RAG (Retrieval-Augmented Generation) и обученные модели для предоставления точных и актуальных юридических консультаций.

## ✨ Основные возможности

- **ИИ-консультации** - Получение юридических консультаций на русском языке
- **RAG система** - Поиск релевантных документов и законов
- **Документооборот** - Загрузка и анализ юридических документов
- **Админ-панель** - Управление системой и пользователями
- **2FA безопасность** - Двухфакторная аутентификация
- **WebSocket чат** - Реальное время общения с ИИ
- **LoRA обучение** - Настройка моделей под специфику

## 🏗️ Архитектура (v2.0 - Unified)

### 🎯 Унифицированная AI-архитектура (Обновлено: 28 октября 2025)

Проект полностью мигрирован на унифицированную архитектуру для улучшения производительности и упрощения управления:

**2 основных AI-сервиса вместо 7:**
- ✅ **UnifiedLLMService** (Vistral-24B-Instruct) - единый сервис для работы с языковыми моделями
- ✅ **UnifiedRAGService** - унифицированная система RAG с гибридным поиском
- ✅ **ServiceManager** - централизованное управление жизненным циклом сервисов
- ✅ **UnifiedMonitoringService** - единая система мониторинга и метрик

**Преимущества новой архитектуры:**
- ⚡ -30% потребление памяти
- 🚀 Поддержка более мощной модели (Vistral-24B вместо Saiga-7B)
- 📊 Централизованные метрики производительности
- 🔄 Автоматическое восстановление при сбоях
- 🎯 Унифицированный API

**Legacy сервисы:** Все старые Saiga сервисы архивированы в `backend/app/services/legacy/`

### Backend (Python/FastAPI)
- **FastAPI** - Современный веб-фреймворк
- **SQLAlchemy** - ORM для работы с БД
- **Vistral-24B-Instruct** - Мощная русскоязычная языковая модель (24B параметров)
- **Qdrant** - Векторная база данных для RAG
- **PostgreSQL** - Основная база данных
- **Redis** - Кэширование
- **Celery** - Фоновые задачи
- **ServiceManager** - Управление AI-сервисами

### Frontend (React)
- **React 18** - Пользовательский интерфейс
- **Tailwind CSS** - Стилизация
- **Axios** - HTTP клиент
- **WebSocket** - Реальное время

## 🚀 Быстрый запуск

### Предварительные требования
- Python 3.11+
- Node.js 18+
- Redis
- PostgreSQL (для продакшена)

### Установка

1. **Клонирование репозитория**
```bash
git clone <repository-url>
cd advakod
```

2. **Настройка Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

3. **Настройка Frontend**
```bash
cd frontend
npm install
```

4. **Настройка переменных окружения**
```bash
# Создайте файл backend/.env
SECRET_KEY=your-secret-key-here-minimum-32-characters
ENCRYPTION_KEY=your-encryption-key-here-minimum-32-characters
DATABASE_URL=sqlite:///./ai_lawyer.db
ENVIRONMENT=development
DEBUG=true
```

5. **Запуск системы**
```bash
# Запуск Backend
cd backend
python main.py

# Запуск Frontend (в другом терминале)
cd frontend
npm start
```

## 🌐 Доступные URL

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Документация:** http://localhost:8000/docs
- **Админ-панель:** http://localhost:3000/admin-login

## 🔧 Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `SECRET_KEY` | JWT секретный ключ (мин. 32 символа) | Обязательно |
| `ENCRYPTION_KEY` | Ключ шифрования (мин. 32 символа) | Обязательно |
| `DATABASE_URL` | URL базы данных | `sqlite:///./ai_lawyer.db` |
| `ENVIRONMENT` | Окружение (development/production) | `development` |
| `DEBUG` | Режим отладки | `true` |
| `REDIS_URL` | URL Redis | `redis://localhost:6379` |

### Настройка модели

Укажите путь к модели Saiga Mistral 7B в переменной `SAIGA_MODEL_PATH`:

```bash
SAIGA_MODEL_PATH=/path/to/saiga_mistral_7b_q4_K.gguf
```

## 🔒 Безопасность

- **JWT токены** - Аутентификация пользователей
- **2FA** - Двухфакторная аутентификация для админов
- **Шифрование данных** - Защита чувствительной информации
- **Rate limiting** - Защита от DDoS атак
- **XSS защита** - Защита от межсайтовых скриптов
- **SQL injection защита** - Защита от SQL инъекций

## 📊 Мониторинг

- **Логирование** - Детальные логи всех операций
- **Аудит безопасности** - Отслеживание событий безопасности
- **Метрики производительности** - Мониторинг системы
- **Health checks** - Проверка состояния сервисов

## 🚀 Развертывание

### Docker (Рекомендуется)

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f
```

### Продакшен

1. **Настройка переменных окружения**
```bash
export ENVIRONMENT=production
export DEBUG=false
export SECRET_KEY=your-production-secret-key
export ENCRYPTION_KEY=your-production-encryption-key
export DATABASE_URL=postgresql://user:password@localhost/advakod_db
```

2. **Запуск с Gunicorn**
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

## 🧪 Тестирование

```bash
# Backend тесты
cd backend
pytest

# Frontend тесты
cd frontend
npm test
```

## 📈 Производительность

- **Время ответа:** 2-8 секунд (CPU)
- **Параллельность:** 1-2 запроса (CPU)
- **Память:** 4-6 GB RAM
- **Кэширование:** Redis для ускорения

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

## 📄 Лицензия

MIT License

## 📞 Поддержка

Для получения поддержки обращайтесь к команде разработки.

---

**A2codex.com** - Ваш персональный ИИ-правовед 24/7! 🏛️⚖️

## 👨‍💻 Разработчик

**Багбеков Азиз**  
Компания: **"Аврамир"**  
Сайт: [A2codex.com](https://a2codex.com)