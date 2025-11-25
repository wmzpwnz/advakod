#!/bin/bash

# 🚀 Скрипт быстрого деплоя АДВАКОД в облако
# Поддерживает: DigitalOcean, AWS, GCP, Hetzner

set -e

# Цвета
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

# Проверка аргументов
if [ $# -eq 0 ]; then
    echo "Использование: $0 <provider> [domain]"
    echo ""
    echo "Провайдеры:"
    echo "  digitalocean  - DigitalOcean Droplet"
    echo "  aws          - AWS EC2"
    echo "  gcp          - Google Cloud Platform"
    echo "  hetzner      - Hetzner Cloud (рекомендуется)"
    echo ""
    echo "Примеры:"
    echo "  $0 hetzner yourdomain.com"
    echo "  $0 digitalocean"
    exit 1
fi

PROVIDER=$1
DOMAIN=${2:-"localhost"}

# Функция установки Docker
install_docker() {
    log_info "Установка Docker..."
    
    if command -v docker &> /dev/null; then
        log_success "Docker уже установлен"
        return
    fi
    
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # Добавляем пользователя в группу docker
    sudo usermod -aG docker $USER
    
    log_success "Docker установлен"
}

# Функция установки Docker Compose
install_docker_compose() {
    log_info "Установка Docker Compose..."
    
    if command -v docker-compose &> /dev/null; then
        log_success "Docker Compose уже установлен"
        return
    fi
    
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    log_success "Docker Compose установлен"
}

# Функция настройки firewall
setup_firewall() {
    log_info "Настройка firewall..."
    
    if command -v ufw &> /dev/null; then
        sudo ufw --force enable
        sudo ufw allow 22    # SSH
        sudo ufw allow 80    # HTTP
        sudo ufw allow 443   # HTTPS
        sudo ufw deny 8000   # API только через Nginx
        log_success "Firewall настроен"
    else
        log_warning "UFW не найден, настройте firewall вручную"
    fi
}

# Функция создания .env для продакшена
create_production_env() {
    log_info "Создание .env для продакшена..."
    
    # Генерируем безопасные пароли
    SECRET_KEY=$(openssl rand -base64 32)
    POSTGRES_PASSWORD=$(openssl rand -base64 16)
    
    cat > .env.production << EOF
# ПРОДАКШЕН НАСТРОЙКИ АДВАКОД
PROJECT_NAME="АДВАКОД - ИИ-Юрист для РФ"
VERSION="1.0.0"
ENVIRONMENT="production"
DEBUG=false

# PostgreSQL база данных
DATABASE_URL="postgresql://advakod:${POSTGRES_PASSWORD}@postgres:5432/advakod_db"
POSTGRES_HOST="postgres"
POSTGRES_PORT=5432
POSTGRES_USER="advakod"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD}"
POSTGRES_DB="advakod_db"

# Qdrant векторная база данных
QDRANT_HOST="qdrant"
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME="legal_documents"

# Безопасность
SECRET_KEY="${SECRET_KEY}"
ACCESS_TOKEN_EXPIRE_MINUTES=240

# Кеширование
REDIS_URL="redis://redis:6379"

# CORS (обновите на ваши домены)
BACKEND_CORS_ORIGINS="https://${DOMAIN},https://www.${DOMAIN}"

# Мониторинг
SENTRY_DSN=""
EOF
    
    log_success ".env.production создан"
}

# Функция настройки Nginx
setup_nginx() {
    log_info "Настройка Nginx..."
    
    cat > nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }
    
    upstream frontend {
        server frontend:3000;
    }
    
    server {
        listen 80;
        server_name ${DOMAIN} www.${DOMAIN};
        
        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # API
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # WebSocket
        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
    }
}
EOF
    
    log_success "Nginx настроен"
}

# Функция создания Docker Compose для продакшена
create_docker_compose() {
    log_info "Создание docker-compose.prod.yml..."
    
    cat > docker-compose.prod.yml << EOF
version: '3.8'

services:
  # PostgreSQL база данных
  postgres:
    image: postgres:15-alpine
    container_name: advakod_postgres
    environment:
      POSTGRES_DB: advakod_db
      POSTGRES_USER: advakod
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - advakod_network

  # Qdrant векторная база данных
  qdrant:
    image: qdrant/qdrant:v1.7.0
    container_name: advakod_qdrant
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped
    networks:
      - advakod_network

  # Redis для кеширования
  redis:
    image: redis:7-alpine
    container_name: advakod_redis
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - advakod_network

  # Backend
  backend:
    build: ./backend
    container_name: advakod_backend
    environment:
      - DATABASE_URL=postgresql://advakod:\${POSTGRES_PASSWORD}@postgres:5432/advakod_db
      - REDIS_URL=redis://redis:6379
      - QDRANT_HOST=qdrant
    depends_on:
      - postgres
      - redis
      - qdrant
    restart: unless-stopped
    networks:
      - advakod_network

  # Frontend
  frontend:
    build: ./frontend
    container_name: advakod_frontend
    environment:
      - REACT_APP_API_URL=https://${DOMAIN}/api
      - REACT_APP_WS_URL=wss://${DOMAIN}/ws
    restart: unless-stopped
    networks:
      - advakod_network

  # Nginx
  nginx:
    image: nginx:alpine
    container_name: advakod_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
    networks:
      - advakod_network

volumes:
  postgres_data:
  qdrant_data:
  redis_data:

networks:
  advakod_network:
    driver: bridge
EOF
    
    log_success "docker-compose.prod.yml создан"
}

# Функция запуска сервисов
start_services() {
    log_info "Запуск сервисов..."
    
    # Копируем .env
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

# Функция настройки SSL
setup_ssl() {
    if [ "$DOMAIN" = "localhost" ]; then
        log_warning "SSL пропущен для localhost"
        return
    fi
    
    log_info "Настройка SSL сертификата..."
    
    # Устанавливаем Certbot
    sudo apt update
    sudo apt install -y certbot python3-certbot-nginx
    
    # Получаем сертификат
    sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
    
    # Настраиваем автообновление
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
    
    log_success "SSL сертификат настроен"
}

# Функция создания администратора
create_admin() {
    log_info "Создание администратора..."
    
    # Ждем запуска базы данных
    sleep 10
    
    # Создаем администратора
    docker exec advakod_backend python create_admin.py
    
    log_success "Администратор создан"
}

# Основная функция
main() {
    echo "🚀 АДВАКОД - Деплой в облако"
    echo "=============================="
    echo "Провайдер: $PROVIDER"
    echo "Домен: $DOMAIN"
    echo ""
    
    # Проверяем права root
    if [ "$EUID" -eq 0 ]; then
        log_error "Не запускайте скрипт от root! Используйте обычного пользователя."
        exit 1
    fi
    
    # Устанавливаем зависимости
    install_docker
    install_docker_compose
    setup_firewall
    
    # Настраиваем приложение
    create_production_env
    setup_nginx
    create_docker_compose
    
    # Запускаем сервисы
    start_services
    create_admin
    
    # Настраиваем SSL если нужно
    if [ "$DOMAIN" != "localhost" ]; then
        setup_ssl
    fi
    
    echo ""
    log_success "🎉 Деплой завершен успешно!"
    echo ""
    echo "🌐 Доступ к сервисам:"
    if [ "$DOMAIN" = "localhost" ]; then
        echo "- Frontend: http://localhost"
        echo "- API: http://localhost/api"
        echo "- API Docs: http://localhost/api/docs"
    else
        echo "- Frontend: https://$DOMAIN"
        echo "- API: https://$DOMAIN/api"
        echo "- API Docs: https://$DOMAIN/api/docs"
    fi
    echo ""
    echo "📋 Следующие шаги:"
    echo "1. Настройте DNS записи для домена"
    echo "2. Проверьте работу всех сервисов"
    echo "3. Настройте мониторинг"
    echo "4. Создайте бэкапы"
    echo ""
    echo "🔧 Управление:"
    echo "- Логи: docker-compose -f docker-compose.prod.yml logs -f"
    echo "- Перезапуск: docker-compose -f docker-compose.prod.yml restart"
    echo "- Остановка: docker-compose -f docker-compose.prod.yml down"
}

# Запуск
main "$@"
