#!/bin/bash

# Настройка SSL сертификатов для HTTPS
echo "🔒 НАСТРОЙКА SSL СЕРТИФИКАТОВ"
echo "=============================="

# Создаем директорию для SSL
mkdir -p /root/advakod/ssl

# Генерируем самоподписанный сертификат (для тестирования)
echo "🔧 Генерация самоподписанного SSL сертификата..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /root/advakod/ssl/private.key \
    -out /root/advakod/ssl/certificate.crt \
    -subj "/C=RU/ST=Moscow/L=Moscow/O=Advakod/OU=IT/CN=advacodex.com"

echo "✅ SSL сертификат создан!"

# Обновляем nginx.conf для HTTPS
echo "🔄 Обновление nginx.conf для HTTPS..."

# Используем существующую nginx конфигурацию с SSL
echo "✅ Используем существующую nginx.conf с SSL поддержкой!"
echo "ℹ️  SSL уже настроен в nginx.conf и nginx.strict.conf"
echo "🔄 Перезапуск nginx с SSL..."

# Перезапуск nginx
cd /root/advakod
docker-compose restart nginx

echo "✅ SSL настроен!"
echo "🌐 Сайт доступен по HTTPS: https://advacodex.com"
echo "⚠️  Для продакшена замените самоподписанный сертификат на Let's Encrypt"
