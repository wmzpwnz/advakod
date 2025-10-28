#!/bin/bash

# Скрипт скачивания и установки Saiga Llama 8B
# Разработчик: Багбеков Азиз | Компания "Аврамир"

set -e

echo "🚀 Установка Saiga Llama 8B"
echo "================================"
echo ""

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

MODEL_DIR="/Users/macbook/llama.cpp/models"
MODEL_NAME="saiga_llama3_8b_q4_K.gguf"
MODEL_PATH="$MODEL_DIR/$MODEL_NAME"
MODEL_URL="https://huggingface.co/IlyaGusev/saiga_llama3_8b_gguf/resolve/main/model-q4_K.gguf"

echo -e "${BLUE}📁 Директория: $MODEL_DIR${NC}"
echo -e "${BLUE}📦 Модель: $MODEL_NAME${NC}"
echo -e "${BLUE}🔗 URL: $MODEL_URL${NC}"
echo ""

# Проверяем директорию
if [ ! -d "$MODEL_DIR" ]; then
    echo -e "${RED}❌ Директория $MODEL_DIR не найдена!${NC}"
    exit 1
fi

# Проверяем, не установлена ли уже
if [ -f "$MODEL_PATH" ]; then
    echo -e "${GREEN}✅ Модель уже установлена!${NC}"
    ls -lh "$MODEL_PATH"
    echo ""
    echo "Хотите переустановить? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "Отмена."
        exit 0
    fi
    rm "$MODEL_PATH"
fi

# Проверяем wget
if ! command -v wget &> /dev/null; then
    echo -e "${RED}❌ wget не установлен!${NC}"
    echo "Установите: brew install wget"
    exit 1
fi

echo -e "${BLUE}📥 Скачивание модели...${NC}"
echo "Это займет несколько минут (~5 GB)"
echo ""

cd "$MODEL_DIR"

# Скачиваем
wget --progress=bar:force "$MODEL_URL" -O "$MODEL_NAME"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Модель скачана успешно!${NC}"
    ls -lh "$MODEL_PATH"
else
    echo -e "${RED}❌ Ошибка скачивания!${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}🔧 Обновление конфигурации...${NC}"

# Обновляем .env
ENV_FILE="/Users/macbook/Desktop/advakod/backend/.env"

if [ -f "$ENV_FILE" ]; then
    # Удаляем старую строку если есть
    sed -i '' '/SAIGA_MODEL_PATH/d' "$ENV_FILE"
fi

# Добавляем новую
echo "SAIGA_MODEL_PATH=$MODEL_PATH" >> "$ENV_FILE"

echo -e "${GREEN}✅ Конфигурация обновлена${NC}"
echo ""

echo -e "${BLUE}🔄 Перезапуск backend...${NC}"

# Останавливаем старый процесс
pkill -f "python.*main.py" || true
sleep 2

# Запускаем новый
cd /Users/macbook/Desktop/advakod/backend
source venv/bin/activate
nohup python3 main.py > ../backend.log 2>&1 &
BACKEND_PID=$!

echo -e "${GREEN}✅ Backend перезапущен (PID: $BACKEND_PID)${NC}"
echo ""

# Ждем запуска
echo "⏳ Ожидание загрузки модели..."
sleep 10

# Проверяем
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✅ Backend работает${NC}"
    echo ""
    echo "🔍 Проверка модели:"
    curl -s http://localhost:8000/health | python3 -m json.tool || echo "Backend еще загружается..."
else
    echo -e "${RED}❌ Backend не запустился!${NC}"
    echo "Проверьте логи: tail -f /Users/macbook/Desktop/advakod/backend.log"
    exit 1
fi

echo ""
echo "================================"
echo -e "${GREEN}🎉 УСТАНОВКА ЗАВЕРШЕНА!${NC}"
echo "================================"
echo ""
echo "📊 Информация о модели:"
echo "   Название: Saiga Llama 8B"
echo "   Размер: $(ls -lh $MODEL_PATH | awk '{print $5}')"
echo "   Путь: $MODEL_PATH"
echo ""
echo "🌐 Сайт:"
echo "   Frontend: http://localhost:3000"
echo "   Backend: http://localhost:8000"
echo ""
echo "📋 Логи:"
echo "   tail -f /Users/macbook/Desktop/advakod/backend.log"
echo ""
echo "👨‍💻 Разработчик: Багбеков Азиз | Компания \"Аврамир\""
echo "================================"
