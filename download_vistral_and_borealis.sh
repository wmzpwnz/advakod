#!/bin/bash
# 🚀 Скрипт загрузки Vistral-24B-GGUF + Borealis (голосовое управление)
# Для сервера с 32 GB RAM

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

MODEL_DIR="${1:-/opt/advakod/models}"

log_info "🚀 Загружаем модели для AI-юриста с голосовым управлением"
log_info "📁 Директория: $MODEL_DIR"

# Создаем директории
mkdir -p "$MODEL_DIR"
mkdir -p "$MODEL_DIR/vistral"
mkdir -p "$MODEL_DIR/borealis"

# Проверяем RAM
TOTAL_RAM=$(free -m | awk 'NR==2{print $2}')
if [ "$TOTAL_RAM" -lt 28000 ]; then
    log_warning "Внимание: Доступно ${TOTAL_RAM} MB RAM"
    log_warning "Рекомендуется минимум 32 GB для обеих моделей"
    log_warning "Продолжить? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        log_info "Отменено пользователем"
        exit 0
    fi
fi

log_success "RAM: ${TOTAL_RAM} MB (достаточно)"

# Проверяем место на диске
AVAILABLE_SPACE=$(df "$MODEL_DIR" | awk 'NR==2 {print $4}')
REQUIRED_SPACE=20000000  # 20GB
if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
    log_error "Недостаточно места на диске!"
    log_error "Доступно: $(($AVAILABLE_SPACE / 1024 / 1024)) GB"
    log_error "Требуется: 20+ GB"
    exit 1
fi

log_success "Диск: $(($AVAILABLE_SPACE / 1024 / 1024)) GB (достаточно)"

# ============================================
# МОДЕЛЬ 1: Vistral-24B-Instruct-GGUF
# ============================================

log_info ""
log_info "📥 1/2: Загружаем Vistral-24B-Instruct-GGUF (основная модель)"
log_info "Размер: ~15 GB | Время: 10-30 минут"

VISTRAL_URL="https://huggingface.co/Vikhrmodels/Vistral-24B-Instruct-GGUF/resolve/main/vistral-24b-instruct-q4_k_m.gguf"
VISTRAL_FILE="$MODEL_DIR/vistral/vistral-24b-instruct-q4_k_m.gguf"

if [ -f "$VISTRAL_FILE" ]; then
    log_warning "Vistral уже загружена: $VISTRAL_FILE"
    FILE_SIZE=$(stat -c%s "$VISTRAL_FILE" 2>/dev/null || stat -f%z "$VISTRAL_FILE" 2>/dev/null)
    FILE_SIZE_GB=$((FILE_SIZE / 1024 / 1024 / 1024))
    
    if [ "$FILE_SIZE_GB" -lt 10 ]; then
        log_warning "Файл слишком маленький (${FILE_SIZE_GB} GB), перезагружаем..."
        rm -f "$VISTRAL_FILE"
    else
        log_success "Размер: ${FILE_SIZE_GB} GB (OK)"
        log_info "Пропускаем загрузку Vistral"
    fi
fi

if [ ! -f "$VISTRAL_FILE" ]; then
    log_info "Загружаем Vistral-24B..."
    
    if command -v wget >/dev/null 2>&1; then
        wget --progress=bar:force -O "$VISTRAL_FILE" "$VISTRAL_URL"
    elif command -v curl >/dev/null 2>&1; then
        curl -L --progress-bar -o "$VISTRAL_FILE" "$VISTRAL_URL"
    else
        log_error "Не найдены wget или curl"
        exit 1
    fi
    
    # Проверяем размер
    FILE_SIZE=$(stat -c%s "$VISTRAL_FILE" 2>/dev/null || stat -f%z "$VISTRAL_FILE" 2>/dev/null)
    FILE_SIZE_GB=$((FILE_SIZE / 1024 / 1024 / 1024))
    
    if [ "$FILE_SIZE_GB" -lt 10 ]; then
        log_error "Файл слишком маленький: ${FILE_SIZE_GB} GB"
        rm -f "$VISTRAL_FILE"
        exit 1
    fi
    
    log_success "Vistral-24B загружена! Размер: ${FILE_SIZE_GB} GB"
fi

# ============================================
# МОДЕЛЬ 2: Borealis (Speech-to-Text)
# ============================================

log_info ""
log_info "📥 2/2: Загружаем Borealis (распознавание речи)"
log_info "Размер: ~1-2 GB | Время: 2-5 минут"

# Borealis может быть в разных форматах, проверим доступные файлы
BOREALIS_BASE_URL="https://huggingface.co/Vikhrmodels/Borealis/resolve/main"

# Попробуем загрузить GGUF версию (если есть)
BOREALIS_GGUF="$MODEL_DIR/borealis/borealis.gguf"
BOREALIS_GGUF_URL="$BOREALIS_BASE_URL/borealis.gguf"

# Или PyTorch версию
BOREALIS_PT="$MODEL_DIR/borealis/pytorch_model.bin"
BOREALIS_PT_URL="$BOREALIS_BASE_URL/pytorch_model.bin"

BOREALIS_CONFIG="$MODEL_DIR/borealis/config.json"
BOREALIS_CONFIG_URL="$BOREALIS_BASE_URL/config.json"

log_info "Пробуем загрузить Borealis GGUF версию..."

if command -v wget >/dev/null 2>&1; then
    wget --progress=bar:force -O "$BOREALIS_GGUF" "$BOREALIS_GGUF_URL" 2>/dev/null || {
        log_warning "GGUF версия не найдена, пробуем PyTorch..."
        rm -f "$BOREALIS_GGUF"
        
        # Загружаем PyTorch версию
        wget --progress=bar:force -O "$BOREALIS_PT" "$BOREALIS_PT_URL"
        wget --progress=bar:force -O "$BOREALIS_CONFIG" "$BOREALIS_CONFIG_URL"
    }
elif command -v curl >/dev/null 2>&1; then
    curl -L --progress-bar -o "$BOREALIS_GGUF" "$BOREALIS_GGUF_URL" 2>/dev/null || {
        log_warning "GGUF версия не найдена, пробуем PyTorch..."
        rm -f "$BOREALIS_GGUF"
        
        # Загружаем PyTorch версию
        curl -L --progress-bar -o "$BOREALIS_PT" "$BOREALIS_PT_URL"
        curl -L --progress-bar -o "$BOREALIS_CONFIG" "$BOREALIS_CONFIG_URL"
    }
fi

if [ -f "$BOREALIS_GGUF" ] || [ -f "$BOREALIS_PT" ]; then
    log_success "Borealis загружена!"
else
    log_warning "Не удалось загрузить Borealis автоматически"
    log_info "Загрузите вручную с: https://huggingface.co/Vikhrmodels/Borealis"
fi

# ============================================
# ФИНАЛИЗАЦИЯ
# ============================================

log_info ""
log_success "🎉 Загрузка завершена!"
log_info ""
log_info "📊 Загруженные модели:"
log_info "   1. Vistral-24B-GGUF: $VISTRAL_FILE"
if [ -f "$BOREALIS_GGUF" ]; then
    log_info "   2. Borealis (GGUF): $BOREALIS_GGUF"
elif [ -f "$BOREALIS_PT" ]; then
    log_info "   2. Borealis (PyTorch): $BOREALIS_PT"
fi

log_info ""
log_info "📝 Использование памяти:"
log_info "   Vistral-24B: ~24-28 GB RAM"
log_info "   Borealis:    ~2-4 GB RAM"
log_info "   ─────────────────────────"
log_info "   ИТОГО:       ~26-32 GB RAM"

log_info ""
log_info "⚙️  Настройте конфигурацию:"
log_info "   VISTRAL_MODEL_PATH=$VISTRAL_FILE"
log_info "   BOREALIS_MODEL_PATH=$MODEL_DIR/borealis/"

log_info ""
log_success "✅ Готово к использованию!"
