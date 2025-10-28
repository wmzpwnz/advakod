#!/bin/bash

# 🔧 АВТОМАТИЧЕСКАЯ НАСТРОЙКА МОДЕЛИ
# Обновляет конфигурацию backend/.env для выбранной модели

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

MODELS_DIR="/Users/macbook/llama.cpp/models"
ENV_FILE="backend/.env"

# Проверяем аргумент
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ Укажите модель: llama3, mistral или nemo${NC}"
    echo "Использование: ./configure_model.sh [llama3|mistral|nemo]"
    exit 1
fi

MODEL_TYPE=$1

case $MODEL_TYPE in
    llama3)
        MODEL_NAME="saiga_llama3_8b_q4_K_M.gguf"
        MODEL_PATH="$MODELS_DIR/$MODEL_NAME"
        N_CTX=8192
        N_THREADS=8
        echo -e "${GREEN}🚀 Настройка Saiga Llama 3.1 8B${NC}"
        ;;
        
    mistral)
        MODEL_NAME="saiga_mistral_7b_q4_K.gguf"
        MODEL_PATH="$MODELS_DIR/$MODEL_NAME"
        N_CTX=8192
        N_THREADS=8
        echo -e "${YELLOW}🔧 Настройка Saiga Mistral 7B${NC}"
        ;;
        
    nemo)
        MODEL_NAME="saiga_nemo_12b_q4_K_M.gguf"
        MODEL_PATH="$MODELS_DIR/$MODEL_NAME"
        N_CTX=8192
        N_THREADS=8
        echo -e "${BLUE}⚙️ Настройка Saiga Nemo 12B${NC}"
        ;;
        
    *)
        echo -e "${RED}❌ Неизвестная модель: $MODEL_TYPE${NC}"
        echo "Доступные: llama3, mistral, nemo"
        exit 1
        ;;
esac

# Проверяем существование модели
if [ ! -f "$MODEL_PATH" ]; then
    echo -e "${RED}❌ Модель не найдена: $MODEL_PATH${NC}"
    echo "Сначала загрузите модель: ./DOWNLOAD_BEST_MODELS.sh"
    exit 1
fi

# Создаем backup .env
if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${GREEN}✅ Создан backup: $ENV_FILE.backup${NC}"
fi

# Обновляем или создаем .env
if [ -f "$ENV_FILE" ]; then
    # Обновляем существующий файл
    sed -i.tmp "s|^SAIGA_MODEL_PATH=.*|SAIGA_MODEL_PATH=$MODEL_PATH|" "$ENV_FILE"
    sed -i.tmp "s|^SAIGA_N_CTX=.*|SAIGA_N_CTX=$N_CTX|" "$ENV_FILE"
    sed -i.tmp "s|^SAIGA_N_THREADS=.*|SAIGA_N_THREADS=$N_THREADS|" "$ENV_FILE"
    rm -f "$ENV_FILE.tmp"
else
    # Создаем новый файл
    cat > "$ENV_FILE" << EOF
# AI Model Configuration
SAIGA_MODEL_PATH=$MODEL_PATH
SAIGA_N_CTX=$N_CTX
SAIGA_N_THREADS=$N_THREADS
SAIGA_N_GPU_LAYERS=0
SAIGA_INFERENCE_TIMEOUT=600
SAIGA_MAX_CONCURRENCY=2
EOF
fi

echo ""
echo -e "${GREEN}✅ КОНФИГУРАЦИЯ ОБНОВЛЕНА!${NC}"
echo ""
echo "📝 Настройки:"
echo "  Модель: $MODEL_NAME"
echo "  Путь: $MODEL_PATH"
echo "  Контекст: $N_CTX токенов"
echo "  Потоки: $N_THREADS"
echo ""
echo "🔄 Перезапустите сервер:"
echo "  ./START_SERVER.sh"
echo ""
