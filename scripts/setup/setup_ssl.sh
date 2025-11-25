#!/bin/bash

# Скрипт автоматической настройки SSL для АДВАКОД
# Использует Let's Encrypt Certbot
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

# Настройки
DOMAIN="advacodex.com"
EMAIL="admin@advacodex.com"
NGINX_CONFIG="/etc/nginx/nginx.conf"

# Проверка аргументов
if [ $# -ge 1 ]; then
    DOMAIN=$1
fi

if [ $# -ge 2 ]; then
    EMAIL=$2
fi

log_info "🔒 Настройка SSL для домена: $DOMAIN"
log_info "Email: $EMAIL"

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    log_error "Скрипт должен запускаться от root"
    exit 1
fi

# Обновление системы
log_info "Обновление системы..."
apt-get update

# Установка Certbot
log_info "Установка Certbot..."
if ! command -v certbot &> /dev/null; then
    apt-get install -y certbot python3-certbot-nginx
    log_success "✅ Certbot установлен"
else
    log_info "Certbot уже установлен"
fi

# Проверка DNS
log_info "Проверка DNS записей..."
if nslookup "$DOMAIN" | grep -q "89.23.98.167"; then
    log_success "✅ DNS запись корректна"
else
    log_warning "⚠️ DNS запись может быть не настроена"
    log_info "Убедитесь, что A запись $DOMAIN указывает на 89.23.98.167"
fi

# Проверка доступности домена
log_info "Проверка доступности домена..."
if curl -s --connect-timeout 10 "http://$DOMAIN" > /dev/null; then
    log_success "✅ Домен доступен"
else
    log_warning "⚠️ Домен может быть недоступен"
    log_info "Убедитесь, что Nginx запущен и домен настроен"
fi

# Создание временной конфигурации Nginx для Certbot
log_info "Создание временной конфигурации Nginx..."
cat > /etc/nginx/sites-available/advacodex-temp << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    location / {
        return 200 'Temporary server for SSL setup';
        add_header Content-Type text/plain;
    }
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
}
EOF

# Создание символической ссылки
ln -sf /etc/nginx/sites-available/advacodex-temp /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Перезапуск Nginx
log_info "Перезапуск Nginx..."
systemctl reload nginx

# Получение SSL сертификата
log_info "Получение SSL сертификата..."
if certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" \
    --non-interactive --agree-tos --email "$EMAIL" \
    --redirect; then
    log_success "✅ SSL сертификат получен успешно"
else
    log_error "❌ Ошибка получения SSL сертификата"
    log_info "Проверьте:"
    log_info "1. DNS записи настроены корректно"
    log_info "2. Домен доступен по HTTP"
    log_info "3. Порт 80 открыт"
    exit 1
fi

# Настройка автообновления
log_info "Настройка автообновления сертификата..."
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
log_success "✅ Автообновление настроено"

# Проверка SSL
log_info "Проверка SSL сертификата..."
if curl -s --connect-timeout 10 "https://$DOMAIN" > /dev/null; then
    log_success "✅ HTTPS работает корректно"
else
    log_warning "⚠️ HTTPS может быть недоступен"
fi

# Очистка временных файлов
log_info "Очистка временных файлов..."
rm -f /etc/nginx/sites-enabled/advacodex-temp
rm -f /etc/nginx/sites-available/advacodex-temp

# Информация о сертификате
log_info "Информация о сертификате:"
certbot certificates

log_success "🎉 SSL настроен успешно!"
log_info "Домен: https://$DOMAIN"
log_info "Сертификат: /etc/letsencrypt/live/$DOMAIN/"
log_info "Автообновление: настроено"

echo ""
log_info "Следующие шаги:"
log_info "1. Обновите nginx.conf для использования SSL"
log_info "2. Перезапустите Docker контейнеры"
log_info "3. Проверьте работу HTTPS"
