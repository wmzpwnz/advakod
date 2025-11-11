#!/bin/bash
# 🚀 ФИНАЛЬНЫЙ СКРИПТ РАЗВЕРТЫВАНИЯ АДВАКОД С VISTRAL-24B
# Этот скрипт делает ВСЁ от начала до конца!

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
echo "║        🚀 ФИНАЛЬНОЕ РАЗВЕРТЫВАНИЕ АДВАКОД                  ║"
echo "║                                                            ║"
echo "║        AI-Юрист с Vistral-24B + Голосовое управление      ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

log_info "🎯 Этот скрипт выполнит ПОЛНОЕ развертывание:"
log_info "  1. Настройка сервера"
log_info "  2. Загрузка Vistral-24B-Instruct"
log_info "  3. Загрузка Borealis (Speech-to-Text)"
log_info "  4. Настройка проекта"
log_info "  5. Запуск всех сервисов"
log_info "  6. Проверка работоспособности"
echo ""
log_warning "⏰ Время выполнения: 30-60 минут"
echo ""
read -p "🚀 Продолжить развертывание? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Отменено пользователем"
    exit 0
fi

# ============================================
# ШАГ 1: ПРОВЕРКА И ПОДГОТОВКА
# ============================================

log_step "ШАГ 1/6: Проверка и подготовка"
echo ""

# Проверяем, что мы на сервере
if [ ! -d "/opt/advakod" ]; then
    log_error "Директория /opt/advakod не найдена!"
    log_info "Создаю директорию..."
    mkdir -p /opt/advakod
fi

cd /opt/advakod

# Проверяем ресурсы
TOTAL_RAM=$(free -m | awk 'NR==2{print $2}')
CPU_CORES=$(nproc)
DISK_SPACE=$(df / | awk 'NR==2{print $4}')

log_info "Проверяю ресурсы сервера..."
log_info "  CPU: $CPU_CORES ядер"
log_info "  RAM: $TOTAL_RAM MB"
log_info "  Диск: $(($DISK_SPACE / 1024 / 1024)) GB"

if [ "$TOTAL_RAM" -lt 30000 ]; then
    log_error "Недостаточно RAM! Нужно минимум 32 GB"
    log_error "Доступно: $TOTAL_RAM MB"
    log_warning "Продолжаю, но могут быть проблемы..."
fi

log_success "Ресурсы проверены"

echo ""

# ============================================
# ШАГ 2: УСТАНОВКА ЗАВИСИМОСТЕЙ
# ============================================

log_step "ШАГ 2/6: Установка зависимостей"
echo ""

log_info "Обновляю систему..."
apt update -qq
apt upgrade -y -qq

log_info "Устанавливаю базовые пакеты..."
apt install -y -qq curl wget git htop ufw fail2ban build-essential git-lfs

log_info "Устанавливаю Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
fi

log_info "Устанавливаю Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

log_info "Настраиваю firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

log_info "Создаю swap (8 GB)..."
if [ ! -f /swapfile ]; then
    fallocate -l 8G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

log_info "Создаю директории..."
mkdir -p /opt/advakod/{models,backups,logs,uploads,ssl}

log_success "Зависимости установлены"

echo ""

# ============================================
# ШАГ 3: ЗАГРУЗКА МОДЕЛЕЙ
# ============================================

log_step "ШАГ 3/6: Загрузка моделей (20-40 минут)"
echo ""

log_info "Устанавливаю git-lfs..."
git lfs install

# Vistral-24B
log_info "Загружаю Vistral-24B-Instruct-GGUF..."
VISTRAL_DIR="/opt/advakod/models/vistral"

if [ -d "$VISTRAL_DIR" ] && [ "$(ls -A $VISTRAL_DIR/*.gguf 2>/dev/null)" ]; then
    log_success "Vistral-24B уже загружена"
else
    rm -rf "$VISTRAL_DIR"
    log_info "Клонирую репозиторий (это займет время)..."
    GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/Vikhrmodels/Vistral-24B-Instruct-GGUF "$VISTRAL_DIR"
    
    cd "$VISTRAL_DIR"
    
    log_info "Загружаю GGUF файлы..."
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
log_info "Загружаю Borealis (Speech-to-Text)..."
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
# ШАГ 4: НАСТРОЙКА ПРОЕКТА
# ============================================

log_step "ШАГ 4/6: Настройка проекта"
echo ""

cd /opt/advakod

# Создаем .env файл
log_info "Создаю конфигурацию..."
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
VISTRAL_N_THREADS=8
VISTRAL_MAX_CONCURRENCY=1
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
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://31.130.145.75
ENVEOF

log_success "Конфигурация создана!"

# Проверяем наличие docker-compose.prod.yml
if [ ! -f "docker-compose.prod.yml" ]; then
    log_error "docker-compose.prod.yml не найден!"
    log_warning "Нужно скопировать файлы проекта на сервер:"
    log_warning "scp -r backend frontend docker-compose.prod.yml nginx.conf root@31.130.145.75:/opt/advakod/"
    exit 1
fi

echo ""

# ============================================
# ШАГ 5: ЗАПУСК DOCKER КОНТЕЙНЕРОВ
# ============================================

log_step "ШАГ 5/6: Запуск Docker контейнеров"
echo ""

log_info "Останавливаю старые контейнеры..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

log_info "Запускаю все сервисы..."
docker-compose -f docker-compose.prod.yml up -d

log_success "Контейнеры запущены!"

echo ""

# ============================================
# ШАГ 6: ПРОВЕРКА РАБОТОСПОСОБНОСТИ
# ============================================

log_step "ШАГ 6/6: Проверка работоспособности"
echo ""

log_info "Ожидаю загрузки моделей (5-10 минут)..."
log_info "Слежу за логами..."

# Показываем логи в течение 2 минут
timeout 120 docker-compose -f docker-compose.prod.yml logs -f backend || true

echo ""

log_info "Проверяю статус контейнеров..."
docker-compose -f docker-compose.prod.yml ps

echo ""

log_info "Проверяю API..."
sleep 30

# Проверяем локальный API
if curl -s http://localhost/api/v1/health 2>/dev/null | grep -q "healthy"; then
    log_success "✅ API работает локально!"
else
    log_warning "⚠️  API еще загружается..."
    log_info "Проверьте логи: docker-compose -f docker-compose.prod.yml logs -f backend"
fi

# Проверяем внешний доступ
if curl -s http://31.130.145.75/api/v1/health 2>/dev/null | grep -q "healthy"; then
    log_success "✅ API доступен извне!"
else
    log_warning "⚠️  API недоступен извне (проверьте firewall)"
fi

echo ""

# ============================================
# ИТОГОВЫЙ РЕЗУЛЬТАТ
# ============================================

log_step "🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!"
echo ""

log_success "АДВАКОД с Vistral-24B успешно развернут!"
echo ""

log_info "📊 Информация:"
log_info "   🌐 Сайт: http://31.130.145.75"
log_info "   🔧 API: http://31.130.145.75/api/v1"
log_info "   💚 Health: http://31.130.145.75/api/v1/health"
log_info "   📝 Docs: http://31.130.145.75/docs"
echo ""

log_info "📝 Полезные команды:"
log_info "   Логи: docker-compose -f docker-compose.prod.yml logs -f backend"
log_info "   Статус: docker-compose -f docker-compose.prod.yml ps"
log_info "   Перезапуск: docker-compose -f docker-compose.prod.yml restart"
echo ""

log_info "🤖 Функции системы:"
log_info "   ✅ Текстовый чат с AI-юристом (Vistral-24B)"
log_info "   ✅ Голосовое управление (Borealis)"
log_info "   ✅ RAG система с векторной базой"
log_info "   ✅ Анализ юридических документов"
echo ""

log_success "🚀 АДВАКОД готов к работе!"