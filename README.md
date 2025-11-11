# ADVAKOD - ИИ-Юрист для РФ

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Node.js](https://img.shields.io/badge/node.js-16+-green.svg)

**ADVAKOD** - это интеллектуальная система юридической помощи на базе искусственного интеллекта, специально разработанная для работы с российским законодательством. Система использует современные технологии RAG (Retrieval-Augmented Generation) для обеспечения точных и актуальных правовых консультаций.

## 🚀 Основные возможности

### 🤖 ИИ-Юрист с RAG интеграцией
- **Многоязычные модели**: Поддержка Vistral, Borealis и других современных LLM
- **RAG система**: Интеллектуальный поиск по правовым документам
- **Контекстный анализ**: Понимание сложных юридических вопросов
- **Валидация ответов**: Автоматическая проверка корректности правовых консультаций

### 📚 База знаний
- **Кодексы РФ**: Полная интеграция основных правовых документов
- **Автоматическая обработка**: Парсинг и индексация PDF документов
- **Векторный поиск**: Быстрый поиск релевантной информации
- **Обновления**: Автоматическое обновление базы знаний

### 🎨 Современный интерфейс
- **Адаптивный дизайн**: Работа на всех устройствах
- **Темная/светлая тема**: Настраиваемый интерфейс
- **Реальное время**: WebSocket соединения для мгновенных обновлений
- **Доступность**: Соответствие стандартам WCAG

### 🔐 Безопасность и управление
- **RBAC система**: Ролевая модель доступа
- **Двухфакторная аутентификация**: Повышенная безопасность
- **Аудит действий**: Полное логирование операций
- **Шифрование**: Защита конфиденциальных данных

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   RAG System    │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (Vector DB)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebSocket     │    │   PostgreSQL    │    │   Document      │
│   Real-time     │    │   Database      │    │   Processing    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Технологический стек

### Backend
- **FastAPI** - Современный веб-фреймворк
- **PostgreSQL** - Основная база данных
- **Redis** - Кэширование и сессии
- **Celery** - Асинхронные задачи
- **Docker** - Контейнеризация

### Frontend
- **React 18** - Пользовательский интерфейс
- **Tailwind CSS** - Стилизация
- **WebSocket** - Реальное время
- **PWA** - Прогрессивное веб-приложение

### AI/ML
- **Vistral** - Основная языковая модель
- **Borealis** - Альтернативная модель
- **Sentence Transformers** - Эмбеддинги
- **FAISS** - Векторный поиск

## 📁 Структура проекта

```
/
├── README.md                    # Главная документация
├── .gitignore                   # Игнорируемые файлы
├── Makefile                     # Команды для удобного запуска
├── docker-compose.yml           # Основной compose
├── docker-compose.prod.yml      # Production compose
├── .env.example                 # Шаблон переменных окружения
│
├── scripts/                     # Все скрипты проекта
│   ├── setup/                   # Настройка сервера
│   ├── deploy/                  # Деплой
│   ├── models/                  # Работа с моделями
│   ├── server/                  # Управление сервером
│   ├── backup/                  # Бэкапы
│   ├── monitoring/              # Мониторинг
│   └── utils/                   # Утилиты
│
├── docs/                        # Вся документация
│   ├── getting-started/        # Быстрый старт
│   ├── deployment/             # Деплой
│   ├── architecture/           # Архитектура
│   ├── api/                    # API документация
│   ├── guides/                 # Гайды
│   ├── reports/                # Отчеты
│   ├── troubleshooting/        # Решение проблем
│   └── development/            # Разработка
│
├── backend/                     # Backend приложение
├── frontend/                    # Frontend приложение
└── openapi/                     # OpenAPI спецификации
```

**Важно**: 
- `nginx.conf` хранится на хосте в `/opt/advakod/config/nginx.conf` (не в репозитории)
- Все скрипты находятся в `scripts/` с подпапками по категориям
- Вся документация находится в `docs/` с подпапками по категориям

## 📦 Установка и запуск

### Предварительные требования
- Python 3.8+
- Node.js 16+
- PostgreSQL 13+
- Redis 6+

### Быстрый старт

1. **Клонирование репозитория**
```bash
git clone https://github.com/your-username/advakod.git
cd advakod
```

2. **Установка зависимостей**
```bash
npm run install-all
```

3. **Настройка окружения**
```bash
cp backend/env.example backend/.env
# Отредактируйте .env файл с вашими настройками
```

4. **Инициализация базы данных**
```bash
cd backend
python create_admin.py
```

5. **Запуск системы**
```bash
npm start
```

Система будет доступна по адресу:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Admin Panel: http://localhost:3000/admin

### Docker развертывание

```bash
# Продакшн развертывание
docker-compose -f docker-compose.prod.yml up -d

# Развертывание с мониторингом
docker-compose -f docker-compose.yml up -d
```

## 📖 Документация

- [API Документация](docs/API_UNIFIED_SERVICES.md)
- [Руководство по развертыванию](docs/DEPLOYMENT.md)
- [Админ панель](docs/ADMIN_PANEL_DOCUMENTATION.md)
- [Система модерации](docs/modules/MODERATION_SYSTEM_GUIDE.md)

## 🔧 Конфигурация

### Переменные окружения

Основные настройки в файле `backend/.env`:

```env
# База данных
DATABASE_URL=postgresql://user:password@localhost/advakod

# Redis
REDIS_URL=redis://localhost:6379

# AI модели
VISTRAL_MODEL_PATH=/path/to/vistral
BOREALIS_MODEL_PATH=/path/to/borealis

# Безопасность
SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret

# Мониторинг
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
```

## 🧪 Тестирование

```bash
# Запуск тестов
npm test

# Тесты безопасности
npm run test:security

# Тесты производительности
npm run test:performance
```

## 📊 Мониторинг

Система включает встроенный мониторинг:
- **Prometheus** - Метрики
- **Grafana** - Дашборды
- **Jaeger** - Трассировка
- **AlertManager** - Уведомления

## 🤝 Участие в разработке

1. Форкните репозиторий
2. Создайте ветку для новой функции (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📝 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 🆘 Поддержка

- **Документация**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-username/advakod/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/advakod/discussions)

## 🏆 Благодарности

- Команде разработки ADVAKOD
- Сообществу Open Source
- Всем контрибьюторам проекта

---

**ADVAKOD** - Делаем правовую помощь доступной для всех! 🇷🇺