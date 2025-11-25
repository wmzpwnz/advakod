#!/bin/bash

# 🚀 Скрипт развертывания АДВАКОД с Vistral-24B-Instruct
# Для облачных серверов с 32+ GB RAM

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Проверяем аргументы
SERVER_IP="${1:-89.23.98.167}"
SERVER_USER="${2:-root}"
SERVER_PASSWORD="${3:-}"

log_info "🚀 Развертывание АДВАКОД с Vistral-24B-Instruct"
log_info "🖥️  Сервер: $SERVER_IP"
log_info "👤 Пользователь: $SERVER_USER"

# Функция для выполнения команд на удаленном сервере
run_remote() {
    if [ -n "$SERVER_PASSWORD" ]; then
        sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "$1"
    else
        ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "$1"
    fi
}

# Функция для копирования файлов
copy_files() {
    if [ -n "$SERVER_PASSWORD" ]; then
        sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -r "$1" "$SERVER_USER@$SERVER_IP:$2"
    else
        scp -o StrictHostKeyChecking=no -r "$1" "$SERVER_USER@$SERVER_IP:$2"
    fi
}

log_info "📋 Проверяем требования к серверу..."

# Проверяем RAM на сервере
RAM_CHECK=$(run_remote "free -m | awk 'NR==2{print \$2}'")
if [ "$RAM_CHECK" -lt 24000 ]; then
    log_error "Недостаточно RAM на сервере!"
    log_error "Доступно: ${RAM_CHECK} MB"
    log_error "Требуется: 24000+ MB (24+ GB)"
    log_error "Рекомендуется сервер с 32+ GB RAM"
    exit 1
fi

log_success "RAM: ${RAM_CHECK} MB (достаточно)"

# Проверяем место на диске
DISK_CHECK=$(run_remote "df / | awk 'NR==2{print \$4}'")
if [ "$DISK_CHECK" -lt 50000000 ]; then
    log_error "Недостаточно места на диске!"
    log_error "Доступно: $(($DISK_CHECK / 1024 / 1024)) MB"
    log_error "Требуется: 50000+ MB (50+ GB)"
    exit 1
fi

log_success "Диск: $(($DISK_CHECK / 1024 / 1024)) MB (достаточно)"

log_info "🔧 Устанавливаем Docker и зависимости..."

# Устанавливаем Docker
run_remote "curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh && rm get-docker.sh"
run_remote "systemctl enable docker && systemctl start docker"

# Устанавливаем Docker Compose
run_remote "curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
run_remote "chmod +x /usr/local/bin/docker-compose"

# Устанавливаем дополнительные пакеты
run_remote "apt-get update && apt-get install -y curl wget git htop ufw fail2ban sshpass"

log_success "Docker и зависимости установлены"

log_info "📁 Создаем директории проекта..."

# Создаем директории
run_remote "mkdir -p /opt/advakod"
run_remote "mkdir -p /opt/advakod/models"
run_remote "mkdir -p /opt/advakod/backups"
run_remote "mkdir -p /opt/advakod/logs"

log_success "Директории созданы"

log_info "📦 Копируем файлы проекта..."

# Копируем основные файлы
copy_files "./backend" "/opt/advakod/"
copy_files "./frontend" "/opt/advakod/"
copy_files "./docker-compose.prod.yml" "/opt/advakod/"
copy_files "./nginx.conf" "/opt/advakod/"
copy_files "./env.production" "/opt/advakod/"
copy_files "./download_vistral_24b.sh" "/opt/advakod/"
copy_files "./*.sh" "/opt/advakod/"

log_success "Файлы скопированы"

log_info "🤖 Загружаем модель Vistral-24B-Instruct..."

# Загружаем модель
run_remote "cd /opt/advakod && chmod +x download_vistral_24b.sh && ./download_vistral_24b.sh /opt/advakod/models"

log_success "Модель загружена"

log_info "⚙️  Настраиваем окружение..."

# Создаем .env файл
run_remote "cd /opt/advakod && cp env.production .env"

# Настраиваем переменные для Vistral
run_remote "cd /opt/advakod && echo 'VISTRAL_MODEL_PATH=/opt/advakod/models/vistral-24b-instruct-q4_K_M.gguf' >> .env"
run_remote "cd /opt/advakod && echo 'VISTRAL_N_CTX=8192' >> .env"
run_remote "cd /opt/advakod && echo 'VISTRAL_N_THREADS=8' >> .env"
run_remote "cd /opt/advakod && echo 'VISTRAL_MAX_CONCURRENCY=1' >> .env"
run_remote "cd /opt/advakod && echo 'VISTRAL_INFERENCE_TIMEOUT=900' >> .env"

log_success "Окружение настроено"

log_info "🐳 Запускаем Docker контейнеры..."

# Запускаем сервисы
run_remote "cd /opt/advakod && docker-compose -f docker-compose.prod.yml up -d"

log_success "Контейнеры запущены"

log_info "⏳ Ожидаем загрузки модели (это может занять 5-10 минут)..."

# Ждем загрузки модели
sleep 60

# Проверяем статус
log_info "🔍 Проверяем статус сервисов..."

run_remote "cd /opt/advakod && docker-compose -f docker-compose.prod.yml ps"

log_info "🌐 Настраиваем SSL..."

# Настраиваем SSL
run_remote "cd /opt/advakod && chmod +x setup_ssl.sh && ./setup_ssl.sh advacodex.com admin@advacodex.com"

log_success "SSL настроен"

log_info "🔧 Настраиваем firewall..."

# Настраиваем firewall
run_remote "ufw allow 22/tcp"
run_remote "ufw allow 80/tcp"
run_remote "ufw allow 443/tcp"
run_remote "ufw --force enable"

log_success "Firewall настроен"

log_info "🧪 Тестируем развертывание..."

# Тестируем API
sleep 30
API_TEST=$(run_remote "curl -s -o /dev/null -w '%{http_code}' http://localhost/api/v1/health" || echo "000")

if [ "$API_TEST" = "200" ]; then
    log_success "✅ API работает корректно!"
else
    log_warning "⚠️  API может быть еще не готов (код: $API_TEST)"
    log_info "Проверьте логи: docker-compose -f docker-compose.prod.yml logs backend"
fi

log_success "🎉 Развертывание завершено!"
log_info "📊 Информация о развертывании:"
log_info "   🌐 URL: https://advacodex.com"
log_info "   🔧 API: https://advacodex.com/api/v1"
log_info "   🤖 Модель: Vistral-24B-Instruct"
log_info "   💾 RAM: ~24-28 GB из ${RAM_CHECK} MB"
log_info "   ⚡ Производительность: 10-30 сек на ответ"

log_info "📝 Полезные команды:"
log_info "   docker-compose -f docker-compose.prod.yml ps"
log_info "   docker-compose -f docker-compose.prod.yml logs -f backend"
log_info "   docker-compose -f docker-compose.prod.yml restart backend"

log_success "🚀 АДВАКОД с Vistral-24B готов к работе!"
