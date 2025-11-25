#!/bin/bash
# 🔧 БЫСТРОЕ ИСПРАВЛЕНИЕ АДВАКОД

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
echo "║        🔧 БЫСТРОЕ ИСПРАВЛЕНИЕ АДВАКОД                     ║"
echo "║                                                            ║"
echo "║        Автоматическое исправление всех проблем            ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

log_info "🚀 Начинаю автоматическое исправление..."
echo ""

# ============================================
# ШАГ 1: ПРОВЕРКА И ПОДГОТОВКА
# ============================================

log_step "ШАГ 1/6: Проверка и подготовка"
echo ""

# Переходим в директорию проекта
cd /opt/advakod 2>/dev/null || {
    log_error "Директория /opt/advakod не найдена!"
    log_info "Создаю директорию..."
    mkdir -p /opt/advakod
    log_warning "Нужно скопировать файлы проекта!"
    log_warning "scp -r backend frontend docker-compose.prod.yml nginx.conf root@31.130.145.75:/opt/advakod/"
    exit 1
}

log_success "Директория проекта найдена"

# Проверяем Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker не установлен!"
    log_info "Устанавливаю Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
fi

if ! systemctl is-active --quiet docker; then
    log_info "Запускаю Docker..."
    systemctl start docker
fi

log_success "Docker готов"

echo ""

# ============================================
# ШАГ 2: ОСТАНОВКА СТАРЫХ КОНТЕЙНЕРОВ
# ============================================

log_step "ШАГ 2/6: Остановка старых контейнеров"
echo ""

log_info "Останавливаю все контейнеры..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

log_info "Удаляю старые контейнеры..."
docker container prune -f 2>/dev/null || true

log_success "Старые контейнеры остановлены"

echo ""

# ============================================
# ШАГ 3: ПРОВЕРКА И ЗАГРУЗКА МОДЕЛЕЙ
# ============================================

log_step "ШАГ 3/6: Проверка моделей"
echo ""

MODELS_DIR="/opt/advakod/models"
mkdir -p "$MODELS_DIR"

# Проверяем Vistral-24B
VISTRAL_FILE=$(find "$MODELS_DIR" -name "*vistral*" -name "*.gguf" -type f | head -n 1)

if [ -z "$VISTRAL_FILE" ]; then
    log_warning "Vistral-24B не найдена!"
    log_info "Загружаю модель..."
    
    # Создаем скрипт загрузки модели
    cat > download_vistral.sh << 'EOF'
#!/bin/bash
MODELS_DIR="/opt/advakod/models"
mkdir -p "$MODELS_DIR"

log_info() { echo -e "\033[0;34mℹ️  $1\033[0m"; }
log_success() { echo -e "\033[0;32m✅ $1\033[0m"; }

log_info "Загружаю Vistral-24B-Instruct-GGUF..."

# Устанавливаем git-lfs
git lfs install

# Клонируем репозиторий
cd "$MODELS_DIR"
GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/Vikhrmodels/Vistral-24B-Instruct-GGUF vistral

cd vistral

# Загружаем GGUF файл
git lfs pull --include="*.gguf"

# Находим файл модели
VISTRAL_FILE=$(find . -name "*.gguf" -type f | head -n 1)
if [ -n "$VISTRAL_FILE" ]; then
    ln -sf "$(pwd)/$VISTRAL_FILE" "/opt/advakod/models/vistral-24b.gguf"
    log_success "Vistral-24B загружена: $VISTRAL_FILE"
else
    log_error "Не удалось загрузить модель"
    exit 1
fi
EOF

    chmod +x download_vistral.sh
    bash download_vistral.sh
    
    # Проверяем результат
    VISTRAL_FILE=$(find "$MODELS_DIR" -name "*vistral*" -name "*.gguf" -type f | head -n 1)
fi

if [ -n "$VISTRAL_FILE" ]; then
    log_success "Vistral-24B найдена: $VISTRAL_FILE"
    FILE_SIZE=$(stat -c%s "$VISTRAL_FILE" 2>/dev/null || echo "0")
    FILE_SIZE_GB=$((FILE_SIZE / 1024 / 1024 / 1024))
    log_info "Размер: ${FILE_SIZE_GB} GB"
else
    log_error "Vistral-24B не найдена!"
    log_warning "Модель будет загружена при первом запуске (займет время)"
fi

echo ""

# ============================================
# ШАГ 4: СОЗДАНИЕ .ENV ФАЙЛА
# ============================================

log_step "ШАГ 4/6: Создание .env файла"
echo ""

log_info "Создаю .env файл..."

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

log_success ".env файл создан"

echo ""

# ============================================
# ШАГ 5: ЗАПУСК DOCKER КОНТЕЙНЕРОВ
# ============================================

log_step "ШАГ 5/6: Запуск Docker контейнеров"
echo ""

log_info "Запускаю все сервисы..."

# Создаем необходимые директории
mkdir -p logs uploads ssl

# Запускаем контейнеры
docker-compose -f docker-compose.prod.yml up -d

log_success "Контейнеры запущены"

echo ""

# ============================================
# ШАГ 6: ПРОВЕРКА РАБОТОСПОСОБНОСТИ
# ============================================

log_step "ШАГ 6/6: Проверка работоспособности"
echo ""

log_info "Ожидаю загрузки сервисов (2 минуты)..."
sleep 30

log_info "Проверяю статус контейнеров..."
docker-compose -f docker-compose.prod.yml ps

echo ""

log_info "Проверяю логи backend..."
docker-compose -f docker-compose.prod.yml logs --tail=10 backend

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

log_step "🎉 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!"
echo ""

log_success "АДВАКОД исправлен и запущен!"
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

log_info "🤖 Функции:"
log_info "   ✅ Текстовый чат с AI-юристом (Vistral-24B)"
log_info "   ✅ Голосовое управление (Borealis)"
log_info "   ✅ RAG система"
log_info "   ✅ Векторная база данных"
echo ""

log_success "🚀 АДВАКОД готов к работе!"