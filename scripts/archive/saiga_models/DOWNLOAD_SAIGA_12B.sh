#!/bin/bash

# Скрипт скачивания Saiga 12B модели
# Разработчик: Багбеков Азиз | Компания "Аврамир"

set -e

echo "🚀 Установка Saiga 12B"
echo "================================"
echo ""

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

MODEL_DIR="/Users/macbook/llama.cpp/models"

echo "Выберите модель:"
echo ""
echo "1️⃣  Saiga Nemo 12B (рекомендуется)"
echo "   - Размер: ~7 GB"
echo "   - Качество: Отличное"
echo "   - Русский язык: Отлично"
echo ""
echo "2️⃣  Saiga Gemma 12B"
echo "   - Размер: ~7 GB"
echo "   - Качество: Отличное"
echo "   - Русский язык: Отлично"
echo ""
echo "Введите номер (1 или 2):"
read -r choice

case $choice in
  1)
    MODEL_NAME="saiga_nemo_12b_q4_K.gguf"
    MODEL_URL="https://huggingface.co/IlyaGusev/saiga_nemo_12b_gguf/resolve/main/model-q4_K.gguf"
    echo -e "${GREEN}✅ Выбрана Saiga Nemo 12B${NC}"
    ;;
  2)
    MODEL_NAME="saiga_gemma3_12b_q4_K.gguf"
    MODEL_URL="https://huggingface.co/IlyaGusev/saiga_gemma3_12b_gguf/resolve/main/model-q4_K.gguf"
    echo -e "${GREEN}✅ Выбрана Saiga Gemma 12B${NC}"
    ;;
  *)
    echo -e "${RED}❌ Неверный выбор!${NC}"
    exit 1
    ;;
esac

MODEL_PATH="$MODEL_DIR/$MODEL_NAME"

echo ""
echo -e "${BLUE}📁 Директория: $MODEL_DIR${NC}"
echo -e "${BLUE}📦 Модель: $MODEL_NAME${NC}"
echo -e "${BLUE}🔗 URL: $MODEL_URL${NC}"
echo ""

# Проверяем, не установлена ли уже
if [ -f "$MODEL_PATH" ]; then
    echo -e "${GREEN}✅ Модель уже установлена!${NC}"
    ls -lh "$MODEL_PATH"
    exit 0
fi

echo -e "${BLUE}📥 Скачивание модели...${NC}"
echo "Это займет несколько минут (~7 GB)"
echo ""

cd "$MODEL_DIR"

# Скачиваем через curl
curl -L --progress-bar "$MODEL_URL" -o "$MODEL_NAME"

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

ENV_FILE="/Users/macbook/Desktop/advakod/backend/.env"

# Удаляем старую строку
if [ -f "$ENV_FILE" ]; then
    sed -i '' '/SAIGA_MODEL_PATH/d' "$ENV_FILE"
fi

# Добавляем новую
echo "SAIGA_MODEL_PATH=$MODEL_PATH" >> "$ENV_FILE"

echo -e "${GREEN}✅ Конфигурация обновлена${NC}"
echo ""

echo -e "${BLUE}🔄 Перезапуск backend...${NC}"

# Останавливаем
pkill -f "python.*main.py" || true
sleep 2

# Запускаем
cd /Users/macbook/Desktop/advakod/backend
source venv/bin/activate
nohup python3 main.py > ../backend.log 2>&1 &
BACKEND_PID=$!

echo -e "${GREEN}✅ Backend перезапущен (PID: $BACKEND_PID)${NC}"
echo ""
echo "⏳ Ожидание загрузки модели (это займет 1-2 минуты)..."
sleep 15

# Проверяем
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✅ Backend работает${NC}"
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
echo "📊 Информация:"
echo "   Модель: $MODEL_NAME"
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
