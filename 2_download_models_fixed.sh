#!/bin/bash
# 📥 Исправленный скрипт загрузки моделей

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

MODEL_DIR="/opt/advakod/models"

log_info "📥 Загрузка моделей для AI-юриста (исправленная версия)"

# Устанавливаем git-lfs если нет
if ! command -v git-lfs &> /dev/null; then
    log_info "Устанавливаем git-lfs..."
    apt install -y git-lfs
    git lfs install
fi

# ============================================
# МОДЕЛЬ 1: Vistral-24B-Instruct-GGUF
# ============================================

log_info ""
log_info "📥 1/2: Загружаем Vistral-24B-Instruct-GGUF"

VISTRAL_DIR="$MODEL_DIR/vistral"

if [ -d "$VISTRAL_DIR" ] && [ "$(ls -A $VISTRAL_DIR/*.gguf 2>/dev/null)" ]; then
    log_success "Vistral-24B уже загружена"
    VISTRAL_FILE=$(ls $VISTRAL_DIR/*.gguf | head -n 1)
    FILE_SIZE=$(du -sh "$VISTRAL_FILE" | cut -f1)
    log_info "Размер: $FILE_SIZE"
else
    log_info "Клонируем репозиторий Vistral-24B..."
    rm -rf "$VISTRAL_DIR"
    
    # Клонируем репозиторий
    GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/Vikhrmodels/Vistral-24B-Instruct-GGUF "$VISTRAL_DIR"
    
    cd "$VISTRAL_DIR"
    
    # Находим GGUF файлы
    log_info "Доступные файлы модели:"
    git lfs ls-files | grep ".gguf"
    
    # Загружаем самый компактный GGUF файл (Q4_K_M или Q4_0)
    log_info "Загружаем модель (это займет 15-30 минут)..."
    
    # Пробуем найти Q4_K_M квантизацию
    if git lfs ls-files | grep -q "q4_k_m.gguf"; then
        git lfs pull --include="*q4_k_m.gguf"
    elif git lfs ls-files | grep -q "q4_0.gguf"; then
        git lfs pull --include="*q4_0.gguf"
    else
        # Загружаем первый найденный GGUF
        FIRST_GGUF=$(git lfs ls-files | grep ".gguf" | head -n 1 | awk '{print $3}')
        log_info "Загружаем: $FIRST_GGUF"
        git lfs pull --include="$FIRST_GGUF"
    fi
    
    # Проверяем что файл загружен
    VISTRAL_FILE=$(find "$VISTRAL_DIR" -name "*.gguf" -type f | head -n 1)
    
    if [ -z "$VISTRAL_FILE" ]; then
        log_error "Не удалось загрузить GGUF файл!"
        log_info "Попробуйте загрузить вручную:"
        log_info "cd $VISTRAL_DIR && git lfs pull"
        exit 1
    fi
    
    FILE_SIZE=$(du -sh "$VISTRAL_FILE" | cut -f1)
    log_success "Vistral-24B загружена! Размер: $FILE_SIZE"
fi

# Создаем символическую ссылку
VISTRAL_FILE=$(find "$VISTRAL_DIR" -name "*.gguf" -type f | head -n 1)
ln -sf "$VISTRAL_FILE" "$MODEL_DIR/vistral-24b.gguf"
log_success "Создана ссылка: $MODEL_DIR/vistral-24b.gguf"

# ============================================
# МОДЕЛЬ 2: Borealis (Speech-to-Text)
# ============================================

log_info ""
log_info "📥 2/2: Загружаем Borealis (распознавание речи)"

BOREALIS_DIR="$MODEL_DIR/borealis"

if [ -d "$BOREALIS_DIR/.git" ]; then
    log_success "Borealis уже загружена"
else
    log_info "Клонируем репозиторий Borealis..."
    rm -rf "$BOREALIS_DIR"
    git clone https://huggingface.co/Vikhrmodels/Borealis "$BOREALIS_DIR"
fi

if [ -f "$BOREALIS_DIR/config.json" ]; then
    log_success "Borealis загружена!"
    BOREALIS_SIZE=$(du -sh "$BOREALIS_DIR" | cut -f1)
    log_info "Размер: $BOREALIS_SIZE"
else
    log_error "Ошибка загрузки Borealis"
fi

# ============================================
# ФИНАЛИЗАЦИЯ
# ============================================

log_info ""
log_success "🎉 Модели загружены!"
log_info ""
log_info "📊 Загруженные модели:"
log_info "   1. Vistral-24B:"
log_info "      $VISTRAL_FILE"
log_info "   2. Borealis:"
log_info "      $BOREALIS_DIR"

log_info ""
log_info "📝 Следующий шаг:"
log_info "   Скопируйте проект на сервер и запустите Docker"
