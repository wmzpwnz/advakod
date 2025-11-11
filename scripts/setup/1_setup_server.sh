#!/bin/bash
# 🔧 Шаг 1: Настройка сервера
# Конфигурация: 10 CPU, 40 GB RAM, 200 GB NVMe

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

log_info "🚀 Настройка сервера для АДВАКОД с Vistral-24B + Borealis"
log_info "📊 Конфигурация: 10 CPU, 40 GB RAM, 200 GB NVMe"

# Проверяем что мы root
if [ "$EUID" -ne 0 ]; then 
    log_error "Запустите скрипт от root: sudo bash $0"
    exit 1
fi

# Проверяем ресурсы
log_info "📋 Проверяем ресурсы сервера..."

TOTAL_RAM=$(free -m | awk 'NR==2{print $2}')
CPU_CORES=$(nproc)
DISK_SPACE=$(df / | awk 'NR==2{print $4}')

log_info "   CPU: $CPU_CORES ядер"
log_info "   RAM: $TOTAL_RAM MB"
log_info "   Диск: $(($DISK_SPACE / 1024 / 1024)) GB"

if [ "$TOTAL_RAM" -lt 35000 ]; then
    log_error "Недостаточно RAM! Нужно минимум 40 GB"
    exit 1
fi

if [ "$CPU_CORES" -lt 8 ]; then
    log_warning "Мало CPU ядер (рекомендуется 10+)"
fi

log_success "Ресурсы: OK"

# Обновляем систему
log_info "📦 Обновляем систему..."
apt update -qq
apt upgrade -y -qq
log_success "Система обновлена"

# Устанавливаем базовые пакеты
log_info "📦 Устанавливаем базовые пакеты..."
apt install -y -qq \
    curl \
    wget \
    git \
    htop \
    ufw \
    fail2ban \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

log_success "Базовые пакеты установлены"

# Устанавливаем Docker
log_info "🐳 Устанавливаем Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
    log_success "Docker установлен"
else
    log_success "Docker уже установлен"
fi

# Устанавливаем Docker Compose
log_info "🐳 Устанавливаем Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    log_success "Docker Compose установлен"
else
    log_success "Docker Compose уже установлен"
fi

# Проверяем версии
DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f4 | cut -d',' -f1)
log_info "   Docker: $DOCKER_VERSION"
log_info "   Docker Compose: $COMPOSE_VERSION"

# Настраиваем firewall
log_info "🔥 Настраиваем firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw --force enable
log_success "Firewall настроен"

# Настраиваем fail2ban
log_info "🛡️  Настраиваем fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban
log_success "Fail2ban настроен"

# Создаем swap (8 GB для подстраховки)
log_info "💾 Настраиваем swap (8 GB)..."
if [ ! -f /swapfile ]; then
    fallocate -l 8G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    log_success "Swap создан (8 GB)"
else
    log_success "Swap уже существует"
fi

# Оптимизируем параметры системы
log_info "⚙️  Оптимизируем параметры системы..."
cat >> /etc/sysctl.conf << EOF

# Оптимизация для AI моделей
vm.swappiness=10
vm.vfs_cache_pressure=50
net.core.somaxconn=1024
net.ipv4.tcp_max_syn_backlog=2048
fs.file-max=65536
EOF

sysctl -p > /dev/null 2>&1
log_success "Параметры оптимизированы"

# Создаем директории проекта
log_info "📁 Создаем директории проекта..."
mkdir -p /opt/advakod
mkdir -p /opt/advakod/models
mkdir -p /opt/advakod/models/vistral
mkdir -p /opt/advakod/models/borealis
mkdir -p /opt/advakod/backups
mkdir -p /opt/advakod/logs
mkdir -p /opt/advakod/uploads
mkdir -p /opt/advakod/ssl

# Устанавливаем права
chown -R root:root /opt/advakod
chmod -R 755 /opt/advakod
chmod 700 /opt/advakod/ssl

log_success "Директории созданы"

# Устанавливаем Python зависимости (для локальных скриптов)
log_info "🐍 Устанавливаем Python..."
apt install -y -qq python3 python3-pip python3-venv
log_success "Python установлен"

# Финальная проверка
log_info ""
log_success "🎉 Сервер настроен!"
log_info ""
log_info "📊 Итоговая конфигурация:"
log_info "   ✅ Docker: установлен"
log_info "   ✅ Docker Compose: установлен"
log_info "   ✅ Firewall: настроен (22, 80, 443)"
log_info "   ✅ Fail2ban: активен"
log_info "   ✅ Swap: 8 GB"
log_info "   ✅ Директории: созданы"
log_info ""
log_info "📝 Следующий шаг:"
log_info "   Запустите: bash 2_download_models.sh"
