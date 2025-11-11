#!/bin/bash

# 🚀 СКРИПТ ЗАПУСКА A2CODEX.COM
# Разработчик: Багбеков Азиз | Компания "Аврамир"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║                                                            ║${NC}"
echo -e "${PURPLE}║           🚀 ЗАПУСК A2CODEX.COM 🚀                        ║${NC}"
echo -e "${PURPLE}║                                                            ║${NC}"
echo -e "${PURPLE}║     ИИ-Юрист с системой обратной связи и модерации       ║${NC}"
echo -e "${PURPLE}║                                                            ║${NC}"
echo -e "${PURPLE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Разработчик: Багбеков Азиз | Компания \"Аврамир\"${NC}"
echo ""

# Проверка, что скрипт запущен из корневой директории проекта
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Ошибка: Запустите скрипт из корневой директории проекта!${NC}"
    exit 1
fi

# Функция для проверки, запущен ли процесс на порту
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0
    else
        return 1
    fi
}

# Проверка портов
echo -e "${BLUE}🔍 Проверка портов...${NC}"

if check_port 8000; then
    echo -e "${YELLOW}⚠️  Порт 8000 (Backend) уже занят${NC}"
    echo -e "${YELLOW}   Остановите процесс или используйте другой порт${NC}"
    read -p "Продолжить? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ Порт 8000 (Backend) свободен${NC}"
fi

if check_port 3000; then
    echo -e "${YELLOW}⚠️  Порт 3000 (Frontend) уже занят${NC}"
    echo -e "${YELLOW}   Остановите процесс или используйте другой порт${NC}"
    read -p "Продолжить? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ Порт 3000 (Frontend) свободен${NC}"
fi

echo ""

# Создание директорий для логов
mkdir -p logs

# Запуск Backend
echo -e "${BLUE}🔧 Запуск Backend...${NC}"
cd backend

# Проверка виртуального окружения
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Виртуальное окружение не найдено${NC}"
    echo -e "${BLUE}📦 Создание виртуального окружения...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo -e "${BLUE}📦 Установка зависимостей...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Запуск backend в фоне
echo -e "${GREEN}🚀 Запуск Backend на порту 8000...${NC}"
nohup python3 main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../logs/backend.pid
echo -e "${GREEN}✅ Backend запущен (PID: $BACKEND_PID)${NC}"

cd ..

# Ждем 3 секунды, чтобы backend успел запуститься
echo -e "${BLUE}⏳ Ожидание запуска Backend (3 сек)...${NC}"
sleep 3

# Проверка, что backend запустился
if check_port 8000; then
    echo -e "${GREEN}✅ Backend успешно запущен на http://localhost:8000${NC}"
else
    echo -e "${RED}❌ Backend не запустился! Проверьте логи: logs/backend.log${NC}"
    exit 1
fi

# Запуск Frontend
echo ""
echo -e "${BLUE}🎨 Запуск Frontend...${NC}"
cd frontend

# Проверка node_modules
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  node_modules не найдены${NC}"
    echo -e "${BLUE}📦 Установка зависимостей...${NC}"
    npm install
fi

# Запуск frontend в фоне
echo -e "${GREEN}🚀 Запуск Frontend на порту 3000...${NC}"
PORT=3000 nohup npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid
echo -e "${GREEN}✅ Frontend запущен (PID: $FRONTEND_PID)${NC}"

cd ..

# Ждем 5 секунд, чтобы frontend успел запуститься
echo -e "${BLUE}⏳ Ожидание запуска Frontend (5 сек)...${NC}"
sleep 5

# Проверка, что frontend запустился
if check_port 3000; then
    echo -e "${GREEN}✅ Frontend успешно запущен на http://localhost:3000${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend еще запускается... Подождите еще немного${NC}"
fi

echo ""
echo -e "${PURPLE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║                                                            ║${NC}"
echo -e "${PURPLE}║              🎉 СЕРВЕР УСПЕШНО ЗАПУЩЕН! 🎉               ║${NC}"
echo -e "${PURPLE}║                                                            ║${NC}"
echo -e "${PURPLE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}🌐 Сайт доступен по адресам:${NC}"
echo -e "${CYAN}   Frontend:     http://localhost:3000${NC}"
echo -e "${CYAN}   Backend API:  http://localhost:8000${NC}"
echo -e "${CYAN}   API Docs:     http://localhost:8000/docs${NC}"
echo ""
echo -e "${GREEN}📊 Новые функции:${NC}"
echo -e "${CYAN}   👍 👎 Кнопки оценки в чате${NC}"
echo -e "${CYAN}   🎯 Панель модерации:     http://localhost:3000/moderation${NC}"
echo -e "${CYAN}   📈 Аналитика модерации:  http://localhost:3000/moderation-dashboard${NC}"
echo ""
echo -e "${GREEN}📋 Управление сервером:${NC}"
echo -e "${CYAN}   Остановить:  ./STOP_SERVER.sh${NC}"
echo -e "${CYAN}   Логи Backend:  tail -f logs/backend.log${NC}"
echo -e "${CYAN}   Логи Frontend: tail -f logs/frontend.log${NC}"
echo ""
echo -e "${GREEN}🔧 PID процессов:${NC}"
echo -e "${CYAN}   Backend:  $BACKEND_PID (сохранен в logs/backend.pid)${NC}"
echo -e "${CYAN}   Frontend: $FRONTEND_PID (сохранен в logs/frontend.pid)${NC}"
echo ""
echo -e "${PURPLE}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}👨‍💻 Разработчик: Багбеков Азиз | Компания \"Аврамир\"${NC}"
echo -e "${CYAN}🌐 A2codex.com - Ваш ИИ-юрист готов к работе!${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════${NC}"
echo ""
