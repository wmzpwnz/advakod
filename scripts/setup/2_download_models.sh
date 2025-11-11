#!/bin/bash
# 📥 Шаг 2: Загрузка моделей Vistral-24B + Borealis

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

log_info "📥 Загрузка моделей для AI-юриста"
log_info "📁 Директория: $MODEL_DIR"

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
log_info "📥 1/2: Загружаем Vistral-24B-Instruct-GGUF"
log_info "   Размер: ~15 GB"
log_info "   Время: 10-30 минут (зависит от скорости интернета)"
log_info "   Назначение: Основная модель AI-юриста"

VISTRAL_DIR="$MODEL_DIR/vistral"

# Клонируем репозиторий Vistral-24B-Instruct-GGUF
if [ -d "$VISTRAL_DIR/.git" ]; then
    log_success "Vistral-24B уже загружена"
    log_info "Обновляем..."
    cd "$VISTRAL_DIR"
    git pull
else
    log_info "Клонируем репозиторий Vistral-24B-GGUF..."
    rm -rf "$VISTRAL_DIR"
    
    # Клонируем с LFS для больших файлов
    git lfs install 2>/dev/null || true
    git clone https://huggingface.co/Vikhrmodels/Vistral-24B-Instruct-GGUF "$VISTRAL_DIR"
    
    cd "$VISTRAL_DIR"
    
    # Загружаем LFS файлы
    git lfs pull
fi

# Находим GGUF файл
VISTRAL_FILE=$(find "$VISTRAL_DIR" -name "*.gguf" -type f | head -n 1)

if [ -z "$VISTRAL_FILE" ]; then
    log_error "GGUF файл не найден в репозитории!"
    log_info "Попробуем загрузить напрямую..."
    
    # Пробуем альтернативные URL
    VISTRAL_FILE="$VISTRAL_DIR/vistral-24b-instruct.gguf"
    
    wget --progress=bar:force \
         --continue \
         --timeout=300 \
         --tries=3 \
         -O "$VISTRAL_FILE" \
         "https://huggingface.co/Vikhrmodels/Vistral-24B-Instruct-GGUF/resolve/main/vistral-24b-instruct.gguf" || \
    wget --progress=bar:force \
         --continue \
         --timeout=300 \
         --tries=3 \
         -O "$VISTRAL_FILE" \
         "https://huggingface.co/Vikhrmodels/Vistral-24B-Instruct-GGUF/resolve/main/ggml-model-q4_k_m.gguf" || \
    {
        log_error "Не удалось загрузить модель автоматически"
        log_info "Загрузите вручную с: https://huggingface.co/Vikhrmodels/Vistral-24B-Instruct-GGUF"
        exit 1
    }
fi
    
    # Проверяем размер
    FILE_SIZE=$(stat -c%s "$VISTRAL_FILE" 2>/dev/null || stat -f%z "$VISTRAL_FILE" 2>/dev/null)
    FILE_SIZE_GB=$((FILE_SIZE / 1024 / 1024 / 1024))
    
    if [ "$FILE_SIZE_GB" -lt 10 ]; then
        log_error "Файл слишком маленький: ${FILE_SIZE_GB} GB"
        log_error "Загрузка не удалась!"
        rm -f "$VISTRAL_FILE"
        exit 1
    fi
    
    log_success "Vistral-24B загружена! (${FILE_SIZE_GB} GB)"
fi

# Создаем символическую ссылку
ln -sf "$VISTRAL_FILE" "$MODEL_DIR/vistral-24b.gguf"
log_success "Создана ссылка: $MODEL_DIR/vistral-24b.gguf"

# ============================================
# МОДЕЛЬ 2: Borealis (Speech-to-Text)
# ============================================

log_info ""
log_info "📥 2/2: Загружаем Borealis (распознавание речи)"
log_info "   Размер: ~1-2 GB"
log_info "   Время: 2-5 минут"
log_info "   Назначение: Преобразование голоса в текст"

# Клонируем репозиторий Borealis
BOREALIS_DIR="$MODEL_DIR/borealis"

if [ -d "$BOREALIS_DIR/.git" ]; then
    log_success "Borealis уже загружена"
    log_info "Обновляем..."
    cd "$BOREALIS_DIR"
    git pull
else
    log_info "Клонируем репозиторий Borealis..."
    rm -rf "$BOREALIS_DIR"
    git clone https://huggingface.co/Vikhrmodels/Borealis "$BOREALIS_DIR"
fi

# Проверяем что файлы загружены
if [ -f "$BOREALIS_DIR/config.json" ]; then
    log_success "Borealis загружена!"
else
    log_error "Ошибка загрузки Borealis"
    log_info "Попробуйте загрузить вручную:"
    log_info "git clone https://huggingface.co/Vikhrmodels/Borealis $BOREALIS_DIR"
    exit 1
fi

# ============================================
# ФИНАЛИЗАЦИЯ
# ============================================

log_info ""
log_success "🎉 Все модели загружены!"
log_info ""
log_info "📊 Загруженные модели:"
log_info "   1. Vistral-24B-GGUF:"
log_info "      Путь: $VISTRAL_FILE"
FILE_SIZE=$(stat -c%s "$VISTRAL_FILE" 2>/dev/null || stat -f%z "$VISTRAL_FILE" 2>/dev/null)
FILE_SIZE_GB=$((FILE_SIZE / 1024 / 1024 / 1024))
log_info "      Размер: ${FILE_SIZE_GB} GB"
log_info ""
log_info "   2. Borealis (STT):"
log_info "      Путь: $BOREALIS_DIR"
BOREALIS_SIZE=$(du -sh "$BOREALIS_DIR" | cut -f1)
log_info "      Размер: $BOREALIS_SIZE"

log_info ""
log_info "💾 Использование памяти (ожидаемое):"
log_info "   Vistral-24B: ~24-28 GB RAM"
log_info "   Borealis:    ~2-4 GB RAM"
log_info "   Система:     ~2-3 GB RAM"
log_info "   ─────────────────────────────"
log_info "   ИТОГО:       ~28-35 GB из 40 GB"
log_info "   Резерв:      ~5-12 GB ✅"

log_info ""
log_info "📝 Следующий шаг:"
log_info "   Скопируйте проект на сервер и запустите:"
log_info "   bash 3_deploy_project.sh"
