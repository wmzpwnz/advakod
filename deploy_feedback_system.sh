#!/bin/bash

# Скрипт развертывания системы обратной связи для A2codex.com
# Дата: 21.10.2025

set -e

echo "🚀 Развертывание системы обратной связи для A2codex.com"
echo "=================================================="

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Проверка что мы в корне проекта
if [ ! -f "backend/main.py" ]; then
    echo -e "${RED}❌ Ошибка: Запустите скрипт из корня проекта${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Шаг 1: Проверка зависимостей${NC}"
cd backend

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 не установлен${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 найден${NC}"

# Проверка виртуального окружения
if [ ! -d "venv" ]; then
    echo -e "${BLUE}🔧 Создание виртуального окружения...${NC}"
    python3 -m venv venv
fi

# Активация виртуального окружения
source venv/bin/activate

# Установка зависимостей
echo -e "${BLUE}📥 Установка зависимостей...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo -e "${GREEN}✅ Зависимости установлены${NC}"

# Шаг 2: Применение миграций
echo -e "${BLUE}📊 Шаг 2: Применение миграций БД${NC}"

# Проверка что alembic настроен
if [ ! -f "alembic.ini" ]; then
    echo -e "${RED}❌ alembic.ini не найден${NC}"
    exit 1
fi

# Применяем миграции
alembic upgrade head

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Миграции применены успешно${NC}"
else
    echo -e "${RED}❌ Ошибка применения миграций${NC}"
    exit 1
fi

# Шаг 3: Инициализация категорий проблем
echo -e "${BLUE}🏷️  Шаг 3: Инициализация категорий проблем${NC}"

python init_feedback_system.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Категории проблем инициализированы${NC}"
else
    echo -e "${RED}❌ Ошибка инициализации категорий${NC}"
    exit 1
fi

# Шаг 4: Проверка frontend
echo -e "${BLUE}🎨 Шаг 4: Проверка frontend${NC}"
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}📥 Установка npm зависимостей...${NC}"
    npm install
fi

echo -e "${GREEN}✅ Frontend готов${NC}"

# Шаг 5: Проверка конфигурации
echo -e "${BLUE}⚙️  Шаг 5: Проверка конфигурации${NC}"
cd ../backend

if [ ! -f ".env" ]; then
    echo -e "${RED}⚠️  Файл .env не найден${NC}"
    echo -e "${BLUE}📝 Создание .env из примера...${NC}"
    
    if [ -f "env.example" ]; then
        cp env.example .env
        echo -e "${GREEN}✅ Создан .env файл. ВАЖНО: Настройте SECRET_KEY и ENCRYPTION_KEY!${NC}"
    else
        echo -e "${RED}❌ env.example не найден${NC}"
        exit 1
    fi
fi

# Проверка обязательных переменных
if ! grep -q "SECRET_KEY=" .env || ! grep -q "ENCRYPTION_KEY=" .env; then
    echo -e "${RED}⚠️  ВНИМАНИЕ: Настройте SECRET_KEY и ENCRYPTION_KEY в .env файле!${NC}"
fi

echo -e "${GREEN}✅ Конфигурация проверена${NC}"

# Шаг 6: Тестовый запуск
echo -e "${BLUE}🧪 Шаг 6: Проверка работоспособности${NC}"

# Проверяем что можем импортировать модели
python -c "from app.models.feedback import ResponseFeedback, ModerationReview; print('✅ Модели импортируются корректно')"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Ошибка импорта моделей${NC}"
    exit 1
fi

# Проверяем API
python -c "from app.api.feedback import router as feedback_router; from app.api.moderation import router as moderation_router; print('✅ API роутеры импортируются корректно')"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Ошибка импорта API${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Все проверки пройдены${NC}"

# Финальный отчет
echo ""
echo "=================================================="
echo -e "${GREEN}🎉 СИСТЕМА ОБРАТНОЙ СВЯЗИ РАЗВЕРНУТА УСПЕШНО!${NC}"
echo "=================================================="
echo ""
echo "📋 Что было сделано:"
echo "  ✅ Применены миграции БД (6 новых таблиц)"
echo "  ✅ Инициализированы категории проблем (8 шт.)"
echo "  ✅ Проверены зависимости"
echo "  ✅ Проверена конфигурация"
echo "  ✅ Проверена работоспособность"
echo ""
echo "🚀 Следующие шаги:"
echo "  1. Запустите backend: cd backend && python main.py"
echo "  2. Запустите frontend: cd frontend && npm start"
echo "  3. Назначьте модераторов через админ-панель"
echo "  4. Откройте /moderation для начала модерации"
echo ""
echo "📚 Документация:"
echo "  - FEEDBACK_SYSTEM_README.md - Полное руководство"
echo "  - .kiro/specs/feedback-moderation-system/ - Спецификации"
echo ""
echo "🌐 A2codex.com - Ваш ИИ-юрист готов к работе!"
echo ""
echo "👨‍💻 Разработчик: Багбеков Азиз"
echo "🏢 Компания: Аврамир"
echo "=================================================="
