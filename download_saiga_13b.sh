#!/bin/bash

# Скрипт загрузки модели Saiga 13B с HuggingFace
# Автор: АДВАКОД Team
# Версия: 1.0

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Функции логирования
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Настройки
MODEL_REPO="IlyaGusev/saiga_mistral_13b_gguf"
MODEL_FILE="saiga_mistral_13b_q4_K_M.gguf"
MODELS_DIR="/opt/advakod/models"
FALLBACK_MODEL="saiga_mistral_13b_q3_K_M.gguf"

# Проверка аргументов
if [ $# -eq 1 ]; then
    MODELS_DIR=$1
fi

log_info "🚀 Загрузка модели Saiga 13B"
log_info "Репозиторий: $MODEL_REPO"
log_info "Файл модели: $MODEL_FILE"
log_info "Директория: $MODELS_DIR"

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    log_error "Скрипт должен запускаться от root для создания директорий"
    exit 1
fi

# Создание директории для моделей
log_info "Создание директории для моделей..."
mkdir -p "$MODELS_DIR"
chmod 755 "$MODELS_DIR"

# Проверка наличия huggingface-cli
if ! command -v huggingface-cli &> /dev/null; then
    log_info "Установка huggingface-hub..."
    pip install huggingface-hub
fi

# Проверка свободного места
AVAILABLE_SPACE=$(df "$MODELS_DIR" | awk 'NR==2 {print $4}')
REQUIRED_SPACE=10000000  # 10GB в KB

if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
    log_error "Недостаточно места на диске. Требуется минимум 10GB"
    exit 1
fi

log_info "Доступно места: $(($AVAILABLE_SPACE / 1024 / 1024))GB"

# Загрузка основной модели
log_info "Загрузка модели $MODEL_FILE..."
cd "$MODELS_DIR"

if huggingface-cli download "$MODEL_REPO" "$MODEL_FILE" --local-dir .; then
    log_success "✅ Модель $MODEL_FILE загружена успешно"
    
    # Проверка размера файла
    FILE_SIZE=$(du -h "$MODEL_FILE" | cut -f1)
    log_info "Размер файла: $FILE_SIZE"
    
    # Проверка целостности (базовая)
    if [ -f "$MODEL_FILE" ] && [ -s "$MODEL_FILE" ]; then
        log_success "✅ Файл модели корректен"
    else
        log_error "❌ Файл модели поврежден или пуст"
        exit 1
    fi
    
else
    log_warning "⚠️ Не удалось загрузить $MODEL_FILE"
    log_info "Попытка загрузки fallback модели $FALLBACK_MODEL..."
    
    if huggingface-cli download "$MODEL_REPO" "$FALLBACK_MODEL" --local-dir .; then
        log_success "✅ Fallback модель $FALLBACK_MODEL загружена успешно"
        MODEL_FILE="$FALLBACK_MODEL"
    else
        log_error "❌ Не удалось загрузить ни одну модель"
        exit 1
    fi
fi

# Установка прав доступа
chmod 644 "$MODEL_FILE"
chown -R 1000:1000 "$MODELS_DIR"  # Для Docker контейнера

# Создание символической ссылки для совместимости
ln -sf "$MODEL_FILE" "saiga_mistral_13b.gguf"

log_success "🎉 Модель Saiga 13B готова к использованию!"
log_info "Путь к модели: $MODELS_DIR/$MODEL_FILE"
log_info "Символическая ссылка: $MODELS_DIR/saiga_mistral_13b.gguf"

# Проверка использования памяти
log_info "Рекомендации по использованию:"
log_info "- Минимум 12GB RAM для модели"
log_info "- SAIGA_N_CTX=4096 (для экономии памяти)"
log_info "- SAIGA_N_THREADS=6 (оставить 2 потока для системы)"
log_info "- SAIGA_MAX_CONCURRENCY=1 (критично при 16GB RAM)"

echo ""
log_success "✅ Загрузка завершена успешно!"
