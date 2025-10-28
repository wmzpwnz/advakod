#!/bin/bash

# Оптимизированная загрузка проекта на сервер
# Исключает ненужные файлы и директории

echo "🚀 Оптимизированная загрузка проекта на сервер"
echo "=============================================="

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Проверка подключения к серверу
echo -e "${BLUE}🔍 Проверка подключения к серверу...${NC}"
if ! ssh -o ConnectTimeout=5 root@31.130.145.75 "echo 'Подключение успешно'" 2>/dev/null; then
    echo -e "${RED}❌ Не удается подключиться к серверу${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Подключение к серверу успешно${NC}"

# Создаем временную директорию для очищенного проекта
TEMP_DIR="/tmp/advakod_clean"
echo -e "${BLUE}📁 Создание временной директории...${NC}"
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Копируем только нужные файлы
echo -e "${BLUE}📋 Копирование файлов проекта...${NC}"

# Backend (исключаем .pyc, __pycache__, venv)
rsync -av --exclude='*.pyc' \
         --exclude='__pycache__' \
         --exclude='venv' \
         --exclude='.env' \
         --exclude='*.db' \
         --exclude='*.log' \
         --exclude='.DS_Store' \
         backend/ "$TEMP_DIR/backend/"

# Frontend (исключаем node_modules, build)
rsync -av --exclude='node_modules' \
         --exclude='build' \
         --exclude='dist' \
         --exclude='.next' \
         --exclude='.DS_Store' \
         frontend/ "$TEMP_DIR/frontend/"

# Конфигурационные файлы
cp docker-compose.prod.yml "$TEMP_DIR/"
cp nginx.conf "$TEMP_DIR/"
cp FINAL_DEPLOY.sh "$TEMP_DIR/"

# Добавляем data директорию если существует
if [ -d "data" ]; then
    echo -e "${BLUE}📊 Копирование data директории...${NC}"
    rsync -av data/ "$TEMP_DIR/data/"
fi

# Показываем размер очищенного проекта
echo -e "${BLUE}📊 Размер очищенного проекта:${NC}"
du -sh "$TEMP_DIR"

echo -e "${BLUE}📤 Загрузка на сервер...${NC}"

# Загружаем очищенный проект
scp -r "$TEMP_DIR"/* root@31.130.145.75:/opt/advakod/

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Загрузка завершена успешно!${NC}"
    
    # Очищаем временную директорию
    rm -rf "$TEMP_DIR"
    
    echo -e "${BLUE}🔧 Следующие шаги на сервере:${NC}"
    echo "1. Установите Python зависимости: cd /opt/advakod/backend && pip install -r requirements.txt"
    echo "2. Установите Node.js зависимости: cd /opt/advakod/frontend && npm install"
    echo "3. Запустите развертывание: ./FINAL_DEPLOY.sh"
else
    echo -e "${RED}❌ Ошибка загрузки${NC}"
    exit 1
fi
