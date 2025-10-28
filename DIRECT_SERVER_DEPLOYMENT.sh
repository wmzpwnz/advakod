#!/bin/bash

# Скрипт для ПРЯМОГО выполнения на сервере через веб-консоль
# Этот скрипт нужно запустить НАПРЯМУЮ на сервере 89.23.98.167
# Автор: АДВАКОД Team

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

log_info "🚀 Прямое развертывание АДВАКОД на сервере"
log_info "Домен: advacodex.com"

# Обновление системы
log_info "Обновление системы..."
apt-get update && apt-get upgrade -y

# Установка Docker
log_info "Установка Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
    log_success "✅ Docker установлен"
else
    log_info "Docker уже установлен"
fi

# Установка Docker Compose
log_info "Установка Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    log_success "✅ Docker Compose установлен"
else
    log_info "Docker Compose уже установлен"
fi

# Установка дополнительных пакетов
log_info "Установка дополнительных пакетов..."
apt-get install -y curl wget git htop ufw python3-pip

# Установка huggingface-cli
log_info "Установка huggingface-cli..."
pip3 install huggingface-hub

# Создание директорий
log_info "Создание директорий..."
mkdir -p /opt/advakod/models
mkdir -p /opt/advakod/backups
mkdir -p /opt/advakod/logs

# Загрузка модели Saiga 13B
log_info "Загрузка модели Saiga 13B (это займет время)..."
cd /opt/advakod/models
huggingface-cli download IlyaGusev/saiga_mistral_13b_gguf saiga_mistral_13b_q4_K_M.gguf --local-dir .
log_success "✅ Модель загружена"

# Генерация паролей
log_info "Генерация паролей..."
SECRET_KEY=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 16)
ENCRYPTION_KEY=$(openssl rand -base64 32)

log_info "📝 Созданные пароли:"
echo "SECRET_KEY: $SECRET_KEY"
echo "POSTGRES_PASSWORD: $POSTGRES_PASSWORD"
echo "ENCRYPTION_KEY: $ENCRYPTION_KEY"
echo ""
log_warning "⚠️ СОХРАНИТЕ ЭТИ ПАРОЛИ В БЕЗОПАСНОМ МЕСТЕ!"

log_success "🎉 Базовая подготовка завершена!"
log_info "Теперь загрузите файлы проекта в /opt/advakod/"
