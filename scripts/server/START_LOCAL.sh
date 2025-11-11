#!/bin/bash

# Скрипт запуска A2codex.com локально для тестирования
# Разработчик: Багбеков Азиз | Компания "Аврамир"

echo "🚀 Запуск A2codex.com локально"
echo "================================"
echo ""

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Проверяем, что мы в правильной директории
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Ошибка: Запустите скрипт из корневой директории проекта${NC}"
    exit 1
fi

echo -e "${BLUE}📊 Проверка системы...${NC}"

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 не установлен${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python3: $(python3 --version)${NC}"

# Проверка Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js не установлен${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Node.js: $(node --version)${NC}"

# Проверка npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm не установлен${NC}"
    exit 1
fi
echo -e "${GREEN}✅ npm: $(npm --version)${NC}"

echo ""
echo -e "${BLUE}🐍 Подготовка Backend...${NC}"

cd backend

# Проверка виртуального окружения
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Виртуальное окружение не найдено. Создаю...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo -e "${GREEN}✅ Виртуальное окружение активировано${NC}"

# Проверка зависимостей
echo "📦 Проверка зависимостей..."
pip list | grep -q fastapi
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Устанавливаю зависимости...${NC}"
    pip install -r requirements.txt
fi

# Проверка базы данных
echo "🗄️  Проверка базы данных..."
python3 -c "
from app.core.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
if 'response_feedback' in tables:
    print('✅ База данных готова')
else:
    print('❌ Таблицы не найдены! Запустите миграции.')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Проблема с базой данных${NC}"
    echo "Запустите: cd backend && alembic upgrade head"
    exit 1
fi

cd ..

echo ""
echo -e "${BLUE}🌐 Подготовка Frontend...${NC}"

cd frontend

# Проверка node_modules
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  node_modules не найдены. Устанавливаю...${NC}"
    npm install
else
    echo -e "${GREEN}✅ node_modules найдены${NC}"
fi

cd ..

echo ""
echo -e "${GREEN}✅ Все проверки пройдены!${NC}"
echo ""
echo "================================"
echo -e "${BLUE}🚀 ЗАПУСК СЕРВЕРОВ${NC}"
echo "================================"
echo ""
echo -e "${YELLOW}📝 Инструкции:${NC}"
echo "1. Backend запустится на http://localhost:8000"
echo "2. Frontend запустится на http://localhost:3000"
echo "3. Для остановки нажмите Ctrl+C в каждом терминале"
echo ""
echo -e "${YELLOW}⚠️  ВАЖНО: Откройте ДВА терминала!${NC}"
echo ""
echo "Терминал 1 (Backend):"
echo -e "${BLUE}cd backend && source venv/bin/activate && python3 main.py${NC}"
echo ""
echo "Терминал 2 (Frontend):"
echo -e "${BLUE}cd frontend && npm start${NC}"
echo ""
echo "================================"
echo ""
echo -e "${GREEN}🎉 Готово к запуску!${NC}"
echo ""
echo "Хотите запустить автоматически? (y/n)"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo ""
    echo -e "${BLUE}🚀 Запускаю серверы...${NC}"
    echo ""
    
    # Запуск backend в фоне
    echo -e "${BLUE}📡 Запуск Backend...${NC}"
    cd backend
    source venv/bin/activate
    python3 main.py > ../backend.log 2>&1 &
    BACKEND_PID=$!
    echo -e "${GREEN}✅ Backend запущен (PID: $BACKEND_PID)${NC}"
    echo "   Логи: tail -f backend.log"
    
    # Ждем запуска backend
    sleep 3
    
    # Запуск frontend в фоне
    echo -e "${BLUE}🌐 Запуск Frontend...${NC}"
    cd ../frontend
    PORT=3000 npm start > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo -e "${GREEN}✅ Frontend запущен (PID: $FRONTEND_PID)${NC}"
    echo "   Логи: tail -f frontend.log"
    
    cd ..
    
    echo ""
    echo "================================"
    echo -e "${GREEN}🎉 СЕРВЕРЫ ЗАПУЩЕНЫ!${NC}"
    echo "================================"
    echo ""
    echo "🌐 Откройте в браузере:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend API: http://localhost:8000/docs"
    echo ""
    echo "📊 Проверка:"
    echo "   Health: http://localhost:8000/health"
    echo "   Ready: http://localhost:8000/ready"
    echo ""
    echo "📋 Логи:"
    echo "   Backend: tail -f backend.log"
    echo "   Frontend: tail -f frontend.log"
    echo ""
    echo "🛑 Остановка:"
    echo "   kill $BACKEND_PID $FRONTEND_PID"
    echo "   или: pkill -f 'python.*main.py' && pkill -f 'node.*'"
    echo ""
    echo "Нажмите Enter для выхода..."
    read
else
    echo ""
    echo -e "${YELLOW}Запустите серверы вручную в двух терминалах:${NC}"
    echo ""
    echo "Терминал 1:"
    echo "cd backend && source venv/bin/activate && python3 main.py"
    echo ""
    echo "Терминал 2:"
    echo "cd frontend && npm start"
fi
