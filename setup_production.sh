#!/bin/bash

# Скрипт настройки продакшен-среды для АДВАКОД

echo "🚀 Настройка продакшен-среды АДВАКОД..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка зависимостей
check_dependencies() {
    log_info "Проверка зависимостей..."
    
    # Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен. Установите Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose не установлен. Установите Docker Compose"
        exit 1
    fi
    
    log_success "Все зависимости установлены"
}

# Создание .env файла для продакшена
create_production_env() {
    log_info "Создание .env файла для продакшена..."
    
    # Генерируем случайный SECRET_KEY
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    POSTGRES_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
    
    cat > .env.production << EOF
# ПРОДАКШЕН НАСТРОЙКИ АДВАКОД
PROJECT_NAME="АДВАКОД - ИИ-Юрист для РФ"
VERSION="1.0.0"
ENVIRONMENT="production"
DEBUG=false

# PostgreSQL база данных
DATABASE_URL="postgresql://advakod:${POSTGRES_PASSWORD}@localhost:5432/advakod_db"
POSTGRES_HOST="localhost"
POSTGRES_PORT=5432
POSTGRES_USER="advakod"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD}"
POSTGRES_DB="advakod_db"

# Qdrant векторная база данных
QDRANT_HOST="localhost"
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME="legal_documents"

# Безопасность
SECRET_KEY="${SECRET_KEY}"
ACCESS_TOKEN_EXPIRE_MINUTES=240

# Кеширование
REDIS_URL="redis://localhost:6379"

# Резервное копирование
BACKUP_DIR="./backups"
MAX_BACKUPS=30
BACKUP_INTERVAL_HOURS=6

# Мониторинг
SENTRY_DSN=""  # Добавьте ваш Sentry DSN для мониторинга ошибок

# CORS (обновите на ваши домены)
BACKEND_CORS_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
EOF

    log_success ".env.production создан с безопасными настройками"
    log_warning "ВАЖНО: Обновите BACKEND_CORS_ORIGINS на ваши домены!"
    log_warning "ВАЖНО: Добавьте SENTRY_DSN для мониторинга ошибок!"
}

# Запуск продакшен-сервисов
start_production_services() {
    log_info "Запуск продакшен-сервисов..."
    
    # Копируем .env файл
    cp .env.production .env
    
    # Запускаем сервисы
    docker-compose -f docker-compose.prod.yml up -d
    
    log_info "Ожидание запуска сервисов..."
    sleep 30
    
    # Проверяем статус
    if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        log_success "Сервисы запущены успешно"
    else
        log_error "Ошибка запуска сервисов"
        docker-compose -f docker-compose.prod.yml logs
        exit 1
    fi
}

# Миграция базы данных
migrate_database() {
    log_info "Применение миграций базы данных..."
    
    cd backend
    
    # Устанавливаем зависимости
    pip install -r requirements.txt
    
    # Применяем миграции
    alembic upgrade head
    
    cd ..
    
    log_success "Миграции применены"
}

# Создание первого администратора
create_admin() {
    log_info "Создание администратора..."
    
    cd backend
    python3 create_admin.py
    cd ..
    
    log_success "Администратор создан"
}

# Основная функция
main() {
    echo "🎯 АДВАКОД - Настройка продакшен-среды"
    echo "========================================="
    
    check_dependencies
    create_production_env
    start_production_services
    migrate_database
    create_admin
    
    echo ""
    log_success "🎉 Продакшен-среда настроена успешно!"
    echo ""
    echo "📋 Следующие шаги:"
    echo "1. Обновите BACKEND_CORS_ORIGINS в .env.production"
    echo "2. Добавьте SSL сертификаты в папку ./ssl/"
    echo "3. Настройте Nginx конфигурацию"
    echo "4. Добавьте SENTRY_DSN для мониторинга"
    echo "5. Настройте автоматические бэкапы"
    echo ""
    echo "🌐 Доступ к сервисам:"
    echo "- Frontend: http://localhost (через Nginx)"
    echo "- API: http://localhost:8000"
    echo "- API Docs: http://localhost:8000/docs"
    echo "- Мониторинг: http://localhost:8000/api/v1/monitoring/health"
    echo "- PostgreSQL: localhost:5432"
    echo "- Qdrant: http://localhost:6333"
    echo "- Redis: localhost:6379"
}

# Запуск
main "$@"
