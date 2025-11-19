#!/bin/bash

# 🚀 СКРИПТ ЗАГРУЗКИ ЛУЧШИХ МОДЕЛЕЙ ОТ ILYAGUSEV
# Автоматическая загрузка и настройка моделей для проекта АДВАКОД

set -e

echo "🔍 АНАЛИЗ ЛУЧШИХ МОДЕЛЕЙ ОТ ILYAGUSEV"
echo "======================================"
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Определяем директорию для моделей
MODELS_DIR="/Users/macbook/llama.cpp/models"
mkdir -p "$MODELS_DIR"

echo -e "${BLUE}📊 ТОП МОДЕЛИ ОТ ILYAGUSEV:${NC}"
echo ""
echo "1. ⭐⭐⭐ Saiga Llama 3.1 8B (ЛУЧШАЯ ДЛЯ ВАШЕГО MAC!)"
echo "   - Размер: ~5 GB (Q4_K_M)"
echo "   - Параметры: 8B"
echo "   - Архитектура: Llama 3.1 (новейшая!)"
echo "   - Русский: Отлично"
echo "   - Качество: Превосходное"
echo "   - Скорость: Быстрая"
echo ""
echo "2. ⭐⭐ Saiga Mistral 7B"
echo "   - Размер: ~4 GB (Q4_K_M)"
echo "   - Параметры: 7B"
echo "   - Архитектура: Mistral (старая)"
echo "   - Русский: Хорошо"
echo "   - Качество: Хорошее"
echo ""
echo "3. ⭐ Saiga Nemo 12B"
echo "   - Размер: ~7 GB (Q4_K_M)"
echo "   - Параметры: 12B"
echo "   - Архитектура: Nemo"
echo "   - Русский: Отлично"
echo "   - Качество: Отличное"
echo ""

# Функция для загрузки модели
download_model() {
    local model_name=$1
    local model_url=$2
    local model_file=$3
    
    echo -e "${YELLOW}📥 Загрузка $model_name...${NC}"
    
    if [ -f "$MODELS_DIR/$model_file" ]; then
        echo -e "${GREEN}✅ Модель уже загружена: $model_file${NC}"
        return 0
    fi
    
    echo "URL: $model_url"
    echo "Путь: $MODELS_DIR/$model_file"
    
    # Загрузка с помощью curl
    curl -L -o "$MODELS_DIR/$model_file" "$model_url" \
        --progress-bar \
        --retry 3 \
        --retry-delay 5 \
        --max-time 3600
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Модель загружена успешно!${NC}"
        return 0
    else
        echo -e "${RED}❌ Ошибка загрузки модели${NC}"
        return 1
    fi
}

# Меню выбора модели
echo ""
echo -e "${BLUE}Выберите модель для загрузки:${NC}"
echo "1) Saiga Llama 3.1 8B (РЕКОМЕНДУЕТСЯ)"
echo "2) Saiga Mistral 7B (текущая)"
echo "3) Saiga Nemo 12B"
echo "4) Все модели"
echo "0) Выход"
echo ""
read -p "Ваш выбор (1-4): " choice

case $choice in
    1)
        echo ""
        echo -e "${GREEN}🚀 ЗАГРУЗКА SAIGA LLAMA 3.1 8B${NC}"
        echo "=================================="
        
        # Saiga Llama 3.1 8B - ЛУЧШАЯ МОДЕЛЬ!
        MODEL_NAME="saiga_llama3_8b_q4_K_M.gguf"
        MODEL_URL="https://huggingface.co/IlyaGusev/saiga_llama3_8b_gguf/resolve/main/model-q4_K_M.gguf"
        
        download_model "Saiga Llama 3.1 8B" "$MODEL_URL" "$MODEL_NAME"
        
        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✅ МОДЕЛЬ ГОТОВА К ИСПОЛЬЗОВАНИЮ!${NC}"
            echo ""
            echo "📝 Обновите конфигурацию в backend/.env:"
            echo ""
            echo "SAIGA_MODEL_PATH=$MODELS_DIR/$MODEL_NAME"
            echo "SAIGA_N_CTX=8192"
            echo "SAIGA_N_THREADS=8"
            echo ""
            echo "🔧 Или выполните автоматическую настройку:"
            echo "./configure_model.sh llama3"
        fi
        ;;
        
    2)
        echo ""
        echo -e "${YELLOW}📥 ЗАГРУЗКА SAIGA MISTRAL 7B${NC}"
        echo "================================"
        
        MODEL_NAME="saiga_mistral_7b_q4_K.gguf"
        MODEL_URL="https://huggingface.co/IlyaGusev/saiga_mistral_7b_gguf/resolve/main/model-q4_K.gguf"
        
        download_model "Saiga Mistral 7B" "$MODEL_URL" "$MODEL_NAME"
        
        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✅ МОДЕЛЬ ГОТОВА!${NC}"
            echo ""
            echo "📝 Путь к модели:"
            echo "SAIGA_MODEL_PATH=$MODELS_DIR/$MODEL_NAME"
        fi
        ;;
        
    3)
        echo ""
        echo -e "${YELLOW}📥 ЗАГРУЗКА SAIGA NEMO 12B${NC}"
        echo "==============================="
        
        MODEL_NAME="saiga_nemo_12b_q4_K_M.gguf"
        MODEL_URL="https://huggingface.co/IlyaGusev/saiga_nemo_12b_gguf/resolve/main/model-q4_K_M.gguf"
        
        download_model "Saiga Nemo 12B" "$MODEL_URL" "$MODEL_NAME"
        
        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✅ МОДЕЛЬ ГОТОВА!${NC}"
            echo ""
            echo "📝 Путь к модели:"
            echo "SAIGA_MODEL_PATH=$MODELS_DIR/$MODEL_NAME"
        fi
        ;;
        
    4)
        echo ""
        echo -e "${BLUE}📥 ЗАГРУЗКА ВСЕХ МОДЕЛЕЙ${NC}"
        echo "========================="
        
        # Llama 3.1 8B
        download_model "Saiga Llama 3.1 8B" \
            "https://huggingface.co/IlyaGusev/saiga_llama3_8b_gguf/resolve/main/model-q4_K_M.gguf" \
            "saiga_llama3_8b_q4_K_M.gguf"
        
        # Mistral 7B
        download_model "Saiga Mistral 7B" \
            "https://huggingface.co/IlyaGusev/saiga_mistral_7b_gguf/resolve/main/model-q4_K.gguf" \
            "saiga_mistral_7b_q4_K.gguf"
        
        # Nemo 12B
        download_model "Saiga Nemo 12B" \
            "https://huggingface.co/IlyaGusev/saiga_nemo_12b_gguf/resolve/main/model-q4_K_M.gguf" \
            "saiga_nemo_12b_q4_K_M.gguf"
        
        echo ""
        echo -e "${GREEN}✅ ВСЕ МОДЕЛИ ЗАГРУЖЕНЫ!${NC}"
        ;;
        
    0)
        echo "Выход..."
        exit 0
        ;;
        
    *)
        echo -e "${RED}❌ Неверный выбор${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}🎉 ГОТОВО!${NC}"
echo ""
echo "📂 Модели находятся в: $MODELS_DIR"
echo ""
echo "🔧 Следующие шаги:"
echo "1. Обновите backend/.env с путем к модели"
echo "2. Перезапустите сервер: ./START_SERVER.sh"
echo "3. Проверьте работу: curl http://localhost:8000/health"
echo ""
