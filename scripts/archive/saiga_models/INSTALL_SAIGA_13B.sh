#!/bin/bash

# Скрипт установки Saiga 13B модели
# Разработчик: Багбеков Азиз | Компания "Аврамир"

set -e

echo "🚀 Установка Saiga 13B модели"
echo "================================"
echo ""

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

MODEL_DIR="/Users/macbook/llama.cpp/models"
MODEL_NAME="saiga_mistral_13b_q4_K.gguf"
MODEL_PATH="$MODEL_DIR/$MODEL_NAME"

echo -e "${BLUE}📁 Директория моделей: $MODEL_DIR${NC}"
echo -e "${BLUE}📦 Модель: $MODEL_NAME${NC}"
echo ""

# Проверяем директорию
if [ ! -d "$MODEL_DIR" ]; then
    echo -e "${RED}❌ Директория $MODEL_DIR не найдена!${NC}"
    exit 1
fi

# Проверяем, не установлена ли уже
if [ -f "$MODEL_PATH" ]; then
    echo -e "${GREEN}✅ Модель уже установлена!${NC}"
    echo "Путь: $MODEL_PATH"
    ls -lh "$MODEL_PATH"
    exit 0
fi

echo -e "${YELLOW}⚠️  Saiga 13B модель НЕ найдена в HuggingFace!${NC}"
echo ""
echo "Доступные варианты:"
echo ""
echo "1️⃣  Saiga Mistral 7B (уже установлена) - 4.1 GB"
echo "   ✅ Быстрая"
echo "   ✅ Хорошее качество"
echo "   ✅ Работает на Mac"
echo ""
echo "2️⃣  Saiga Llama 13B - ~8 GB"
echo "   📦 Больше размер"
echo "   🐌 Медленнее"
echo "   🎯 Лучше качество"
echo ""
echo "3️⃣  Альтернативы:"
echo "   - Mistral 7B Instruct"
echo "   - Llama 2 13B"
echo "   - OpenChat 3.5"
echo ""

echo -e "${BLUE}🔍 Поиск доступных моделей...${NC}"
echo ""

# Ссылки на модели
echo "📥 Ссылки для скачивания:"
echo ""
echo "Saiga Llama 13B:"
echo "https://huggingface.co/IlyaGusev/saiga_llama3_8b_gguf"
echo ""
echo "Mistral 7B Instruct:"
echo "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
echo ""
echo "Llama 2 13B:"
echo "https://huggingface.co/TheBloke/Llama-2-13B-chat-GGUF"
echo ""

echo -e "${YELLOW}📝 Инструкция по установке:${NC}"
echo ""
echo "1. Перейдите на HuggingFace:"
echo "   https://huggingface.co/IlyaGusev"
echo ""
echo "2. Найдите нужную модель (Saiga 13B или аналог)"
echo ""
echo "3. Скачайте файл .gguf (Q4_K_M рекомендуется)"
echo ""
echo "4. Переместите в директорию:"
echo "   $MODEL_DIR"
echo ""
echo "5. Обновите конфигурацию:"
echo "   backend/.env"
echo "   SAIGA_MODEL_PATH=$MODEL_PATH"
echo ""
echo "6. Перезапустите backend"
echo ""

echo -e "${GREEN}💡 РЕКОМЕНДАЦИЯ:${NC}"
echo ""
echo "Используйте текущую Saiga 7B!"
echo "Она достаточно хороша для юридических консультаций."
echo "Система обратной связи поможет улучшить качество ответов."
echo ""
echo "Если нужна 13B модель - скачайте вручную с HuggingFace."
echo ""
