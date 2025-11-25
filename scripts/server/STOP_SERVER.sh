#!/bin/bash

# 🛑 СКРИПТ ОСТАНОВКИ A2CODEX.COM
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
echo -e "${PURPLE}║           🛑 ОСТАНОВКА A2CODEX.COM 🛑                     ║${NC}"
echo -e "${PURPLE}║                                                            ║${NC}"
echo -e "${PURPLE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Остановка Backend
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    echo -e "${BLUE}🔧 Остановка Backend (PID: $BACKEND_PID)...${NC}"
    
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        echo -e "${GREEN}✅ Backend остановлен${NC}"
    else
        echo -e "${YELLOW}⚠️  Backend уже остановлен${NC}"
    fi
    
    rm logs/backend.pid
else
    echo -e "${YELLOW}⚠️  PID файл Backend не найден${NC}"
    # Пытаемся найти процесс по имени
    BACKEND_PID=$(pgrep -f "python.*main.py")
    if [ ! -z "$BACKEND_PID" ]; then
        echo -e "${BLUE}🔧 Найден процесс Backend (PID: $BACKEND_PID), останавливаем...${NC}"
        kill $BACKEND_PID
        echo -e "${GREEN}✅ Backend остановлен${NC}"
    fi
fi

# Остановка Frontend
if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    echo -e "${BLUE}🎨 Остановка Frontend (PID: $FRONTEND_PID)...${NC}"
    
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        echo -e "${GREEN}✅ Frontend остановлен${NC}"
    else
        echo -e "${YELLOW}⚠️  Frontend уже остановлен${NC}"
    fi
    
    rm logs/frontend.pid
else
    echo -e "${YELLOW}⚠️  PID файл Frontend не найден${NC}"
    # Пытаемся найти процесс по имени
    FRONTEND_PID=$(pgrep -f "npm.*start")
    if [ ! -z "$FRONTEND_PID" ]; then
        echo -e "${BLUE}🎨 Найден процесс Frontend (PID: $FRONTEND_PID), останавливаем...${NC}"
        kill $FRONTEND_PID
        echo -e "${GREEN}✅ Frontend остановлен${NC}"
    fi
fi

# Дополнительная очистка - убиваем все процессы на портах 8000 и 3000
echo ""
echo -e "${BLUE}🧹 Дополнительная очистка портов...${NC}"

# Порт 8000 (Backend)
PORT_8000_PID=$(lsof -ti:8000)
if [ ! -z "$PORT_8000_PID" ]; then
    echo -e "${YELLOW}⚠️  Найден процесс на порту 8000 (PID: $PORT_8000_PID)${NC}"
    kill -9 $PORT_8000_PID 2>/dev/null
    echo -e "${GREEN}✅ Порт 8000 освобожден${NC}"
fi

# Порт 3000 (Frontend)
PORT_3000_PID=$(lsof -ti:3000)
if [ ! -z "$PORT_3000_PID" ]; then
    echo -e "${YELLOW}⚠️  Найден процесс на порту 3000 (PID: $PORT_3000_PID)${NC}"
    kill -9 $PORT_3000_PID 2>/dev/null
    echo -e "${GREEN}✅ Порт 3000 освобожден${NC}"
fi

echo ""
echo -e "${PURPLE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║                                                            ║${NC}"
echo -e "${PURPLE}║              ✅ СЕРВЕР УСПЕШНО ОСТАНОВЛЕН! ✅             ║${NC}"
echo -e "${PURPLE}║                                                            ║${NC}"
echo -e "${PURPLE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Для повторного запуска используйте: ./START_SERVER.sh${NC}"
echo ""
