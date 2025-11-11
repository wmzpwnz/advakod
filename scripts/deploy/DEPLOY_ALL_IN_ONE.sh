#!/bin/bash
# 🚀 МАСТЕР-СКРИПТ ПОЛНОГО РАЗВЕРТЫВАНИЯ АДВАКОД
# Этот скрипт делает ВСЁ автоматически от начала до конца

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_step() { echo -e "${PURPLE}🔹 $1${NC}"; }

clear
echo -e "${PURPLE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║        🚀 АДВАКОД - ПОЛНОЕ АВТОМАТИЧЕСКОЕ РАЗВЕРТЫВАНИЕ   ║"
echo "║                                                            ║"
echo "║        AI-Юрист с Vistral-24B + Голосовое управление      ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

log_info "Этот скрипт выполнит:"
log_info "  1. Настройку сервера"
log_info "  2. Загрузку моделей Vistral-24B + Borealis"
log_info "  3. Настройку проекта"
log_info "  4. Запуск Docker контейнеров"
echo ""
log_warning "Время выполнения: 30-60 минут"
echo ""
read -p "Продолжить? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Отменено пользователем"
    exit 0
fi

# ============================================
# ШАГ 1: НАСТРОЙКА СЕРВЕРА
# ============================================

log_step "ШАГ 1/4: Настройка сервера"
echo ""

log_info "Проверяем ресурсы..."
TOTAL_RAM=$(free -m | awk 'NR==2{print $2}')
CPU_CORES=$(nproc)
DISK_SPACE=$(df / | awk 'NR==2{print $4}')

log_info "  CPU: $CPU_CORES ядер"
log_info "  RAM: $TOTAL_RAM MB"
log_info "  Диск: $(($DISK_SPACE / 1024 / 1024)) GB"

if [ "$TOTAL_RAM" -lt 35000 ]; then
    log_error "Недостаточно RAM! Нужно минимум 40 GB"
    exit 1
fi

log_success "Ресурсы: OK"

log_info "Обновляем систему..."
apt update -qq
apt upgrade -y -qq

log_info "Устанавливаем базовые пакеты..."
apt install -y -qq curl wget git htop ufw fail2ban build-essential git-lfs

log_info "Устанавливаем Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
fi

log_info "Устанавливаем Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

log_info "Настраиваем firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

log_info "Создаем swap (8 GB)..."
if [ ! -f /swapfile ]; then
    fallocate -l 8G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

log_info "Создаем директории..."
mkdir -p /opt/advakod/{models,backups,logs,uploads,ssl}

log_success "Сервер настроен!"
echo ""

# ============================================
# ШАГ 2: ЗАГРУЗКА МОДЕЛЕЙ
# ============================================

log_step "ШАГ 2/4: Загрузка моделей (20-40 минут)"
echo ""

log_info "Устанавливаем git-lfs..."
git lfs install

# Vistral-24B
log_info "Загружаем Vistral-24B-Instruct-GGUF..."
VISTRAL_DIR="/opt/advakod/models/vistral"

if [ -d "$VISTRAL_DIR" ] && [ "$(ls -A $VISTRAL_DIR/*.gguf 2>/dev/null)" ]; then
    log_success "Vistral-24B уже загружена"
else
    rm -rf "$VISTRAL_DIR"
    log_info "Клонируем репозиторий (это займет время)..."
    GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/Vikhrmodels/Vistral-24B-Instruct-GGUF "$VISTRAL_DIR"
    
    cd "$VISTRAL_DIR"
    
    log_info "Загружаем GGUF файлы..."
    # Пробуем загрузить Q4_K_M квантизацию
    if git lfs ls-files | grep -q "q4_k_m.gguf"; then
        git lfs pull --include="*q4_k_m.gguf"
    elif git lfs ls-files | grep -q "q4_0.gguf"; then
        git lfs pull --include="*q4_0.gguf"
    else
        git lfs pull --include="*.gguf" | head -n 1
    fi
    
    VISTRAL_FILE=$(find "$VISTRAL_DIR" -name "*.gguf" -type f | head -n 1)
    if [ -z "$VISTRAL_FILE" ]; then
        log_error "Не удалось загрузить Vistral-24B"
        exit 1
    fi
    
    log_success "Vistral-24B загружена!"
fi

# Создаем символическую ссылку
VISTRAL_FILE=$(find "$VISTRAL_DIR" -name "*.gguf" -type f | head -n 1)
ln -sf "$VISTRAL_FILE" "/opt/advakod/models/vistral-24b.gguf"

# Borealis
log_info "Загружаем Borealis (Speech-to-Text)..."
BOREALIS_DIR="/opt/advakod/models/borealis"

if [ -d "$BOREALIS_DIR/.git" ]; then
    log_success "Borealis уже загружена"
else
    rm -rf "$BOREALIS_DIR"
    git clone https://huggingface.co/Vikhrmodels/Borealis "$BOREALIS_DIR"
fi

log_success "Модели загружены!"
echo ""

# ============================================
# ШАГ 3: НАСТРОЙКА ПРОЕКТА
# ============================================

log_step "ШАГ 3/4: Настройка проекта"
echo ""

cd /opt/advakod

# Создаем .env файл
log_info "Создаем конфигурацию..."
cat > .env << 'ENVEOF'
# Основные настройки
PROJECT_NAME="АДВАКОД - ИИ-Юрист для РФ"
VERSION="2.0.0"
ENVIRONMENT=production
DEBUG=false

# База данных PostgreSQL
DATABASE_URL=postgresql://advakod:AdvakodSecurePass2024!@postgres:5432/advakod_db
POSTGRES_USER=advakod
POSTGRES_PASSWORD=AdvakodSecurePass2024!
POSTGRES_DB=advakod_db

# Vistral-24B модель
VISTRAL_MODEL_PATH=/opt/advakod/models/vistral-24b.gguf
VISTRAL_N_CTX=8192
VISTRAL_N_THREADS=10
VISTRAL_MAX_CONCURRENCY=2
VISTRAL_INFERENCE_TIMEOUT=900

# Borealis (Speech-to-Text)
BOREALIS_MODEL_PATH=/opt/advakod/models/borealis/
BOREALIS_ENABLED=true

# Qdrant векторная база
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=legal_documents

# Redis кэширование
REDIS_URL=redis://redis:6379
CACHE_TTL_DEFAULT=3600
CACHE_TTL_AI_RESPONSE=7200

# JWT безопасность
SECRET_KEY=AdvakodSecretKey2024WithNumbers123AndLettersABC456DEF789GHI
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
ENVEOF

log_success "Конфигурация создана!"

# Проверяем наличие docker-compose.prod.yml
if [ ! -f "docker-compose.prod.yml" ]; then
    log_warning "docker-compose.prod.yml не найден!"
    log_info "Скопируйте проект на сервер:"
    log_info "  scp -r backend frontend docker-compose.prod.yml nginx.conf root@31.130.145.75:/opt/advakod/"
    log_info ""
    log_info "После копирования запустите этот скрипт снова"
    exit 1
fi

echo ""

# ============================================
# ШАГ 4: ЗАПУСК DOCKER
# ============================================

log_step "ШАГ 4/4: Запуск Docker контейнеров"
echo ""

log_info "Запускаем все сервисы..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
docker-compose -f docker-compose.prod.yml up -d

log_info "Ожидаем загрузки моделей (5-10 минут)..."
log_info "Следим за логами..."

# Показываем логи в течение 2 минут
timeout 120 docker-compose -f docker-compose.prod.yml logs -f backend || true

echo ""
log_success "Docker контейнеры запущены!"
echo ""

# ============================================
# ФИНАЛЬНАЯ ПРОВЕРКА
# ============================================

log_step "ФИНАЛЬНАЯ ПРОВЕРКА"
echo ""

log_info "Проверяем статус контейнеров..."
docker-compose -f docker-compose.prod.yml ps

echo ""
log_info "Проверяем health endpoint..."
sleep 10

if curl -s http://localhost/api/v1/health | grep -q "healthy"; then
    log_success "API работает!"
else
    log_warning "API еще загружается, подождите 5-10 минут"
fi

echo ""
echo -e "${PURPLE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║                  🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!              ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

log_success "АДВАКОД успешно развернут!"
echo ""
log_info "📊 Информация:"
log_info "   🌐 API: http://31.130.145.75/api/v1"
log_info "   🔧 Health: http://31.130.145.75/api/v1/health"
log_info "   📝 Docs: http://31.130.145.75/docs"
echo ""
log_info "📝 Полезные команды:"
log_info "   Логи: docker-compose -f docker-compose.prod.yml logs -f backend"
log_info "   Статус: docker-compose -f docker-compose.prod.yml ps"
log_info "   Перезапуск: docker-compose -f docker-compose.prod.yml restart"
echo ""
log_info "🎤 Функции:"
log_info "   ✅ Текстовый чат с AI-юристом"
log_info "   ✅ Голосовое управление (Borealis)"
log_info "   ✅ RAG система"
log_info "   ✅ Векторная база данных"
echo ""
log_success "Готово к работе! 🚀"
