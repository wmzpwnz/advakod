#!/bin/bash
# 🔄 Скрипт восстановления проекта ADVAKOD из Git
# Использование: bash scripts/utils/restore_from_git.sh

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

GIT_REPO="git@github.com:wmzpwnz/advakod.git"
TAG="v2.0.0-stable"
PROJECT_DIR="advakod"

log_info "🔄 Восстановление проекта ADVAKOD из Git"
log_info "📦 Репозиторий: $GIT_REPO"
log_info "🏷️  Тег: $TAG"

# Проверяем наличие Git
if ! command -v git &> /dev/null; then
    log_error "Git не установлен! Установите: apt install git"
    exit 1
fi

# Клонируем репозиторий
if [ -d "$PROJECT_DIR" ]; then
    log_warning "Директория $PROJECT_DIR уже существует"
    read -p "Удалить и пересоздать? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Удаляем существующую директорию..."
        rm -rf "$PROJECT_DIR"
    else
        log_error "Отменено пользователем"
        exit 1
    fi
fi

log_info "📥 Клонируем репозиторий..."
git clone "$GIT_REPO" "$PROJECT_DIR"
cd "$PROJECT_DIR"

log_info "🏷️  Переключаемся на тег $TAG..."
git checkout "$TAG"

log_success "✅ Репозиторий клонирован"

# Создаем .env файлы из примеров
log_info "📝 Создаем .env файлы из примеров..."

if [ -f "backend/env.example" ]; then
    if [ ! -f "backend/.env" ]; then
        cp backend/env.example backend/.env
        log_success "Создан backend/.env из примера"
        log_warning "⚠️  Отредактируйте backend/.env с реальными значениями!"
    else
        log_warning "backend/.env уже существует, пропускаем"
    fi
fi

if [ -f "ENV_EXAMPLE.txt" ]; then
    log_info "Пример переменных окружения: ENV_EXAMPLE.txt"
fi

# Создаем необходимые директории
log_info "📁 Создаем необходимые директории..."
mkdir -p logs
mkdir -p uploads
mkdir -p media
mkdir -p temp
mkdir -p backups
mkdir -p /opt/advakod/models
mkdir -p /opt/advakod/config
mkdir -p /opt/advakod/logs
mkdir -p /opt/advakod/uploads

log_success "Директории созданы"

# Копируем примеры конфигураций
log_info "📋 Копируем примеры конфигураций..."

if [ -f "nginx_ssl.conf.example" ]; then
    if [ ! -f "/opt/advakod/config/nginx.conf" ]; then
        cp nginx_ssl.conf.example /opt/advakod/config/nginx.conf
        log_success "Скопирован nginx_ssl.conf.example -> /opt/advakod/config/nginx.conf"
        log_warning "⚠️  Отредактируйте /opt/advakod/config/nginx.conf под свои нужды!"
    fi
fi

if [ -f "unified_codex_system.service.example" ]; then
    log_info "Пример systemd service: unified_codex_system.service.example"
    log_info "Скопируйте в /etc/systemd/system/ если нужно"
fi

log_success "✅ Примеры конфигураций готовы"

# Устанавливаем права на скрипты
log_info "🔧 Устанавливаем права на скрипты..."
find scripts/ -type f -name "*.sh" -exec chmod +x {} \;
log_success "Права установлены"

# Проверяем зависимости
log_info "📦 Проверяем зависимости..."

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    log_success "Python: $PYTHON_VERSION"
else
    log_warning "Python3 не найден, установите: apt install python3 python3-pip"
fi

if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    log_success "Node.js: $NODE_VERSION"
else
    log_warning "Node.js не найден, установите: apt install nodejs npm"
fi

if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    log_success "Docker: $DOCKER_VERSION"
else
    log_warning "Docker не найден, установите: curl -fsSL https://get.docker.com | sh"
fi

# Финальная информация
log_info ""
log_success "🎉 Проект восстановлен из Git!"
log_info ""
log_info "📋 Следующие шаги:"
log_info ""
log_info "1. Настройте переменные окружения:"
log_info "   nano backend/.env"
log_info ""
log_info "2. Установите зависимости:"
log_info "   cd backend && pip install -r requirements.txt"
log_info "   cd ../frontend && npm install"
log_info ""
log_info "3. Настройте конфигурации:"
log_info "   nano /opt/advakod/config/nginx.conf"
log_info ""
log_info "4. Запустите через Docker:"
log_info "   docker-compose -f docker-compose.prod.yml up -d"
log_info ""
log_info "5. Или используйте скрипты:"
log_info "   bash scripts/setup/1_setup_server.sh"
log_info "   bash scripts/setup/2_download_models.sh"
log_info ""
log_warning "⚠️  Не забудьте:"
log_warning "   - Загрузить модели AI (если нужны)"
log_warning "   - Настроить SSL сертификаты (для продакшена)"
log_warning "   - Восстановить базы данных из бэкапов (если есть)"
log_info ""
log_success "✅ Готово! Проект готов к использованию."


