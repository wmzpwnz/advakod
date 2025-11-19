#!/bin/bash

# Скрипт скачивания Saiga 13B модели
# Разработчик: Багбеков Азиз | Компания "Аврамир"

echo "📥 Скачивание Saiga Mistral 13B модели"
echo "========================================"
echo ""

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Директория для моделей
MODEL_DIR="$HOME/llama.cpp/models"
MODEL_FILE="saiga_mistral_13b_q4_K.gguf"
MODEL_PATH="$MODEL_DIR/$MODEL_FILE"

echo -e "${BLUE}📁 Директория: $MODEL_DIR${NC}"
echo -e "${BLUE}📄 Файл: $MODEL_FILE${NC}"
echo ""

# Проверяем директорию
if [ ! -d "$MODEL_DIR" ]; then
    echo -e "${YELLOW}⚠️  Директория не найдена. Создаю...${NC}"
    mkdir -p "$MODEL_DIR"
fi

# Проверяем, не скачана ли уже модель
if [ -f "$MODEL_PATH" ]; then
    FILE_SIZE=$(ls -lh "$MODEL_PATH" | awk '{print $5}')
    echo -e "${GREEN}✅ Модель уже скачана!${NC}"
    echo -e "   Размер: $FILE_SIZE"
    echo ""
    echo "Хотите скачать заново? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "Отменено."
        exit 0
    fi
    rm "$MODEL_PATH"
fi

echo -e "${BLUE}🌐 Выберите метод скачивания:${NC}"
echo "1. HuggingFace CLI (рекомендуется)"
echo "2. wget"
echo "3. curl"
echo ""
echo -n "Ваш выбор (1-3): "
read -r choice

case $choice in
    1)
        echo ""
        echo -e "${BLUE}📦 Установка huggingface-cli...${NC}"
        pip3 install -q huggingface-hub
        
        echo -e "${BLUE}📥 Скачивание через HuggingFace CLI...${NC}"
        echo -e "${YELLOW}⏳ Это займет 10-30 минут в зависимости от скорости интернета${NC}"
        echo ""
        
        huggingface-cli download IlyaGusev/saiga_mistral_13b_gguf \
            "$MODEL_FILE" \
            --local-dir "$MODEL_DIR" \
            --local-dir-use-symlinks False
        ;;
    2)
        if ! command -v wget &> /dev/null; then
            echo -e "${RED}❌ wget не установлен${NC}"
            echo "Установите: brew install wget"
            exit 1
        fi
        
        echo -e "${BLUE}📥 Скачивание через wget...${NC}"
        echo -e "${YELLOW}⏳ Это займет 10-30 минут в зависимости от скорости интернета${NC}"
        echo ""
        
        cd "$MODEL_DIR"
        wget --progress=bar:force \
            "https://huggingface.co/IlyaGusev/saiga_mistral_13b_gguf/resolve/main/$MODEL_FILE"
        ;;
    3)
        echo -e "${BLUE}📥 Скачивание через curl...${NC}"
        echo -e "${YELLOW}⏳ Это займет 10-30 минут в зависимости от скорости интернета${NC}"
        echo ""
        
        curl -L --progress-bar \
            -o "$MODEL_PATH" \
            "https://huggingface.co/IlyaGusev/saiga_mistral_13b_gguf/resolve/main/$MODEL_FILE"
        ;;
    *)
        echo -e "${RED}❌ Неверный выбор${NC}"
        exit 1
        ;;
esac

echo ""
echo "========================================"

# Проверяем результат
if [ -f "$MODEL_PATH" ]; then
    FILE_SIZE=$(ls -lh "$MODEL_PATH" | awk '{print $5}')
    echo -e "${GREEN}✅ МОДЕЛЬ УСПЕШНО СКАЧАНА!${NC}"
    echo ""
    echo "📊 Информация:"
    echo "   Путь: $MODEL_PATH"
    echo "   Размер: $FILE_SIZE"
    echo ""
    
    # Проверяем размер (должно быть ~8-10 GB)
    FILE_SIZE_BYTES=$(stat -f%z "$MODEL_PATH" 2>/dev/null || stat -c%s "$MODEL_PATH" 2>/dev/null)
    MIN_SIZE=$((7 * 1024 * 1024 * 1024))  # 7 GB
    
    if [ "$FILE_SIZE_BYTES" -lt "$MIN_SIZE" ]; then
        echo -e "${RED}⚠️  ВНИМАНИЕ: Файл слишком маленький!${NC}"
        echo "   Ожидается: ~8-10 GB"
        echo "   Получено: $FILE_SIZE"
        echo ""
        echo "Возможно, скачивание прервалось. Попробуйте еще раз."
        exit 1
    fi
    
    echo -e "${BLUE}🔧 Следующие шаги:${NC}"
    echo ""
    echo "1. Обновить конфигурацию:"
    echo "   nano backend/.env"
    echo ""
    echo "   Добавить:"
    echo "   SAIGA_MODEL_PATH=$MODEL_PATH"
    echo ""
    echo "2. Перезапустить backend:"
    echo "   pkill -f 'python.*main.py'"
    echo "   cd backend && source venv/bin/activate && python3 main.py"
    echo ""
    echo "3. Проверить:"
    echo "   curl http://localhost:8000/health"
    echo ""
    echo -e "${GREEN}🎉 Готово!${NC}"
else
    echo -e "${RED}❌ ОШИБКА: Файл не найден${NC}"
    echo "Попробуйте другой метод скачивания"
    exit 1
fi
