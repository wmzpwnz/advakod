#!/bin/bash

# Автоматический скрипт развертывания АДВАКОД на сервер
# Подключается к серверу, устанавливает зависимости и запускает приложение
# Автор: АДВАКОД Team
# Версия: 1.0

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Функции логирования
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Настройки сервера
SERVER_IP="89.23.98.167"
SERVER_USER="root"
SERVER_PASSWORD="k-^.V1Y-A#KuS6"
DOMAIN="advacodex.com"
PROJECT_DIR="/opt/advakod"

# Проверка аргументов
if [ $# -ge 1 ]; then
    SERVER_IP=$1
fi

if [ $# -ge 2 ]; then
    SERVER_USER=$2
fi

if [ $# -ge 3 ]; then
    SERVER_PASSWORD=$3
fi

log_info "🚀 Развертывание АДВАКОД на сервер"
log_info "Сервер: $SERVER_IP"
log_info "Пользователь: $SERVER_USER"
log_info "Домен: $DOMAIN"

# Проверка SSH подключения
log_info "Проверка SSH подключения..."
if ! sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "echo 'SSH подключение успешно'"; then
    log_error "❌ Не удается подключиться к серверу"
    log_info "Проверьте:"
    log_info "1. IP адрес сервера: $SERVER_IP"
    log_info "2. SSH доступ открыт"
    log_info "3. Пароль корректный"
    exit 1
fi

log_success "✅ SSH подключение работает"

# Установка sshpass если не установлен
if ! command -v sshpass &> /dev/null; then
    log_info "Установка sshpass..."
    if command -v brew &> /dev/null; then
        brew install hudochenkov/sshpass/sshpass
    elif command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y sshpass
    else
        log_error "❌ sshpass не установлен. Установите вручную"
        exit 1
    fi
fi

# Функция выполнения команд на сервере
run_remote() {
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "$@"
}

# Функция копирования файлов на сервер
copy_to_server() {
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -r "$1" "$SERVER_USER@$SERVER_IP:$2"
}

# Обновление системы
log_info "Обновление системы на сервере..."
run_remote "apt-get update && apt-get upgrade -y"

# Установка Docker
log_info "Установка Docker..."
if ! run_remote "command -v docker &> /dev/null"; then
    run_remote "curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh && rm get-docker.sh"
    run_remote "systemctl enable docker && systemctl start docker"
    log_success "✅ Docker установлен"
else
    log_info "Docker уже установлен"
fi

# Установка Docker Compose
log_info "Установка Docker Compose..."
if ! run_remote "command -v docker-compose &> /dev/null"; then
    run_remote "curl -L 'https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)' -o /usr/local/bin/docker-compose"
    run_remote "chmod +x /usr/local/bin/docker-compose"
    log_success "✅ Docker Compose установлен"
else
    log_info "Docker Compose уже установлен"
fi

# Установка дополнительных пакетов
log_info "Установка дополнительных пакетов..."
run_remote "apt-get install -y curl wget git htop ufw fail2ban"

# Настройка firewall
log_info "Настройка firewall..."
run_remote "ufw --force enable"
run_remote "ufw allow 22/tcp"
run_remote "ufw allow 80/tcp"
run_remote "ufw allow 443/tcp"
run_remote "ufw deny 8000/tcp"
log_success "✅ Firewall настроен"

# Создание директории проекта
log_info "Создание директории проекта..."
run_remote "mkdir -p $PROJECT_DIR"
run_remote "mkdir -p /opt/advakod/models"
run_remote "mkdir -p /opt/advakod/backups"
run_remote "mkdir -p /opt/advakod/logs"

# Копирование файлов проекта
log_info "Копирование файлов проекта..."
copy_to_server "./backend" "$PROJECT_DIR/"
copy_to_server "./frontend" "$PROJECT_DIR/"
copy_to_server "./docker-compose.prod.yml" "$PROJECT_DIR/"
copy_to_server "./nginx.conf" "$PROJECT_DIR/"
copy_to_server "./env.production" "$PROJECT_DIR/"
copy_to_server "./download_saiga_13b.sh" "$PROJECT_DIR/"
copy_to_server "./setup_ssl.sh" "$PROJECT_DIR/"
copy_to_server "./backup.sh" "$PROJECT_DIR/"

# Установка прав доступа
run_remote "chmod +x $PROJECT_DIR/*.sh"

# Генерация паролей
log_info "Генерация безопасных паролей..."
SECRET_KEY=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 16)
ENCRYPTION_KEY=$(openssl rand -base64 32)

# Создание .env файла на сервере
log_info "Создание .env файла на сервере..."
run_remote "cat > $PROJECT_DIR/.env << EOF
# ПРОДАКШЕН НАСТРОЙКИ АДВАКОД
PROJECT_NAME=\"АДВАКОД - ИИ-Юрист для РФ\"
VERSION=\"1.0.0\"
ENVIRONMENT=\"production\"
DEBUG=false

# PostgreSQL база данных
DATABASE_URL=\"postgresql://advakod:${POSTGRES_PASSWORD}@postgres:5432/advakod_db\"
POSTGRES_HOST=\"postgres\"
POSTGRES_PORT=5432
POSTGRES_USER=\"advakod\"
POSTGRES_PASSWORD=\"${POSTGRES_PASSWORD}\"
POSTGRES_DB=\"advakod_db\"

# Qdrant векторная база данных
QDRANT_HOST=\"qdrant\"
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=\"legal_documents\"

# Saiga 13B модель
SAIGA_MODEL_PATH=\"/opt/advakod/models/saiga_mistral_13b_q4_K_M.gguf\"
SAIGA_N_CTX=4096
SAIGA_N_THREADS=6
SAIGA_N_GPU_LAYERS=0
SAIGA_INFERENCE_TIMEOUT=300
SAIGA_MAX_CONCURRENCY=1
SAIGA_TOKEN_MARGIN=128
SAIGA_REPEAT_PENALTY=1.1
SAIGA_STOP_TOKENS=\"\"
LOG_PROMPTS=false

# Безопасность
SECRET_KEY=\"${SECRET_KEY}\"
ACCESS_TOKEN_EXPIRE_MINUTES=240
ENCRYPTION_KEY=\"${ENCRYPTION_KEY}\"

# CORS
BACKEND_CORS_ORIGINS=\"https://${DOMAIN},https://www.${DOMAIN}\"

# Кеширование
REDIS_URL=\"redis://redis:6379\"
CACHE_TTL_DEFAULT=3600
CACHE_TTL_AI_RESPONSE=7200
CACHE_TTL_USER_PROFILE=1800

# Таймауты для разных типов AI-анализа
AI_DOCUMENT_ANALYSIS_TIMEOUT=300
AI_CHAT_RESPONSE_TIMEOUT=120
AI_COMPLEX_ANALYSIS_TIMEOUT=600
AI_EMBEDDINGS_TIMEOUT=60

# Настройки токенов для AI-анализа
AI_DOCUMENT_ANALYSIS_TOKENS=30000
AI_CHAT_RESPONSE_TOKENS=4000
AI_COMPLEX_ANALYSIS_TOKENS=20000
AI_EMBEDDINGS_TOKENS=1000

# Мониторинг
SENTRY_DSN=\"\"
JAEGER_ENDPOINT=\"\"

# Резервное копирование
BACKUP_DIR=\"./backups\"
MAX_BACKUPS=30
BACKUP_INTERVAL_HOURS=6

# Домен
DOMAIN=\"${DOMAIN}\"
API_URL=\"https://${DOMAIN}/api/v1\"
WS_URL=\"wss://${DOMAIN}/ws\"

# SSL
SSL_CERT_PATH=\"/etc/nginx/ssl/certificate.crt\"
SSL_KEY_PATH=\"/etc/nginx/ssl/private.key\"
EOF"

# Загрузка модели Saiga 13B
log_info "Загрузка модели Saiga 13B..."
run_remote "cd $PROJECT_DIR && ./download_saiga_13b.sh /opt/advakod/models"

# Запуск сервисов
log_info "Запуск Docker контейнеров..."
run_remote "cd $PROJECT_DIR && docker-compose -f docker-compose.prod.yml up -d"

# Ожидание запуска сервисов
log_info "Ожидание запуска сервисов (2 минуты)..."
sleep 120

# Проверка статуса сервисов
log_info "Проверка статуса сервисов..."
if run_remote "cd $PROJECT_DIR && docker-compose -f docker-compose.prod.yml ps | grep -q 'Up'"; then
    log_success "✅ Сервисы запущены успешно"
else
    log_error "❌ Ошибка запуска сервисов"
    run_remote "cd $PROJECT_DIR && docker-compose -f docker-compose.prod.yml logs"
    exit 1
fi

# Настройка SSL
log_info "Настройка SSL сертификата..."
run_remote "cd $PROJECT_DIR && ./setup_ssl.sh $DOMAIN admin@$DOMAIN"

# Настройка автоматических бэкапов
log_info "Настройка автоматических бэкапов..."
run_remote "echo '0 3 * * * $PROJECT_DIR/backup.sh' | crontab -"

# Создание администратора
log_info "Создание администратора..."
run_remote "cd $PROJECT_DIR && docker exec advakod_backend python create_admin.py"

# Финальная проверка
log_info "Финальная проверка системы..."

# Проверка доступности API
if run_remote "curl -f http://localhost/api/v1/health"; then
    log_success "✅ API доступен"
else
    log_warning "⚠️ API может быть недоступен"
fi

# Проверка SSL
if run_remote "curl -f https://$DOMAIN/api/v1/health"; then
    log_success "✅ HTTPS работает"
else
    log_warning "⚠️ HTTPS может быть недоступен"
fi

log_success "🎉 Развертывание завершено успешно!"
echo ""
log_info "🌐 Доступ к сервисам:"
log_info "- Frontend: https://$DOMAIN"
log_info "- API: https://$DOMAIN/api/v1"
log_info "- API Docs: https://$DOMAIN/api/docs"
log_info "- Health Check: https://$DOMAIN/api/v1/health"
echo ""
log_info "📋 Следующие шаги:"
log_info "1. Настройте DNS записи для домена $DOMAIN"
log_info "2. Проверьте работу всех сервисов"
log_info "3. Создайте первого пользователя"
log_info "4. Настройте мониторинг"
echo ""
log_info "🔧 Управление:"
log_info "- Логи: ssh $SERVER_USER@$SERVER_IP 'cd $PROJECT_DIR && docker-compose -f docker-compose.prod.yml logs -f'"
log_info "- Перезапуск: ssh $SERVER_USER@$SERVER_IP 'cd $PROJECT_DIR && docker-compose -f docker-compose.prod.yml restart'"
log_info "- Остановка: ssh $SERVER_USER@$SERVER_IP 'cd $PROJECT_DIR && docker-compose -f docker-compose.prod.yml down'"
echo ""
log_info "🔑 Пароли (сохраните в безопасном месте):"
log_info "- PostgreSQL: $POSTGRES_PASSWORD"
log_info "- SECRET_KEY: $SECRET_KEY"
log_info "- ENCRYPTION_KEY: $ENCRYPTION_KEY"
