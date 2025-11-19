#!/bin/bash

# 🚀 Скрипт загрузки Vistral-24B-Instruct-GGUF
# Совместим с llama-cpp-python

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Проверяем аргументы
MODEL_DIR="${1:-/opt/advakod/models}"

log_info "🚀 Загружаем Vistral-24B-Instruct-GGUF..."
log_info "📁 Директория: $MODEL_DIR"

# Создаем директорию
mkdir -p "$MODEL_DIR"

# URL модели (GGUF версия, совместимая с llama-cpp-python)
MODEL_URL="https://huggingface.co/Vikhrmodels/Vistral-24B-Instruct-GGUF/resolve/main/vistral-24b-instruct-q4_K_M.gguf"
MODEL_FILE="vistral-24b-instruct-q4_K_M.gguf"
MODEL_PATH="$MODEL_DIR/$MODEL_FILE"

# Проверяем, существует ли уже модель
if [ -f "$MODEL_PATH" ]; then
    log_warning "Модель уже существует: $MODEL_PATH"
    read -p "Перезаписать? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Отменено пользователем"
        exit 0
    fi
fi

# Проверяем доступное место на диске
AVAILABLE_SPACE=$(df "$MODEL_DIR" | awk 'NR==2 {print $4}')
REQUIRED_SPACE=20000000  # 20GB в KB

if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
    log_error "Недостаточно места на диске!"
    log_error "Доступно: $(($AVAILABLE_SPACE / 1024 / 1024)) GB"
    log_error "Требуется: $((REQUIRED_SPACE / 1024 / 1024)) GB"
    exit 1
fi

# Проверяем RAM
TOTAL_RAM=$(free -m | awk 'NR==2{print $2}')
if [ "$TOTAL_RAM" -lt 24000 ]; then
    log_warning "Внимание: Модель требует минимум 24 GB RAM"
    log_warning "Доступно: ${TOTAL_RAM} MB"
    log_warning "Рекомендуется сервер с 32+ GB RAM"
fi

log_info "📥 Загружаем модель из HuggingFace..."
log_info "URL: $MODEL_URL"

# Загружаем модель с прогресс-баром
if command -v wget >/dev/null 2>&1; then
    wget --progress=bar:force -O "$MODEL_PATH" "$MODEL_URL"
elif command -v curl >/dev/null 2>&1; then
    curl -L --progress-bar -o "$MODEL_PATH" "$MODEL_URL"
else
    log_error "Не найдены wget или curl для загрузки"
    exit 1
fi

# Проверяем размер файла
if [ -f "$MODEL_PATH" ]; then
    FILE_SIZE=$(stat -c%s "$MODEL_PATH")
    FILE_SIZE_GB=$((FILE_SIZE / 1024 / 1024 / 1024))
    
    if [ "$FILE_SIZE_GB" -lt 10 ]; then
        log_error "Файл слишком маленький: ${FILE_SIZE_GB} GB"
        log_error "Возможно, загрузка не удалась"
        rm -f "$MODEL_PATH"
        exit 1
    fi
    
    log_success "Модель загружена успешно!"
    log_success "Размер: ${FILE_SIZE_GB} GB"
    log_success "Путь: $MODEL_PATH"
    
    # Создаем символическую ссылку для совместимости
    ln -sf "$MODEL_PATH" "$MODEL_DIR/vistral-24b.gguf"
    log_success "Создана ссылка: $MODEL_DIR/vistral-24b.gguf"
    
else
    log_error "Ошибка загрузки модели"
    exit 1
fi

log_success "🎉 Vistral-24B-Instruct-GGUF готов к использованию!"
log_info "📝 Для использования обновите конфигурацию:"
log_info "   VISTRAL_MODEL_PATH=$MODEL_PATH"
log_info "   VISTRAL_N_CTX=8192"
log_info "   VISTRAL_N_THREADS=8"
log_info "   VISTRAL_MAX_CONCURRENCY=1"
