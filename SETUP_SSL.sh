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

# Создаем новый nginx.conf с HTTPS
cat > /root/advakod/nginx_ssl.conf << 'EOF'
# Конфигурация Nginx для АДВАКОД с SSL
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;
    
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    upstream backend {
        server advakod_backend:8000;
        keepalive 32;
    }
    
    upstream frontend {
        server advakod_frontend:3000;
    }
    
    # HTTP сервер - редирект на HTTPS
    server {
        listen 80;
        server_name advacodex.com www.advacodex.com;
        return 301 https://$server_name$request_uri;
    }
    
    # HTTPS сервер
    server {
        listen 443 ssl http2;
        server_name advacodex.com www.advacodex.com;
        
        # SSL сертификаты
        ssl_certificate /etc/nginx/ssl/certificate.crt;
        ssl_certificate_key /etc/nginx/ssl/private.key;
        
        # SSL настройки
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;
        
        # HSTS
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        
        # Безопасность
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        
        # Статические файлы
        location /static/ {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
        
        # Медиа файлы
        location /media/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            expires 1M;
            add_header Cache-Control "public";
        }
        
        # API endpoints
        location /api/v1/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $host;
            
            proxy_connect_timeout 60s;
            proxy_send_timeout 900s;
            proxy_read_timeout 900s;
        }
        
        # WebSocket соединения
        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $host;
            
            proxy_connect_timeout 60s;
            proxy_send_timeout 900s;
            proxy_read_timeout 900s;
        }
        
        # Health check
        location /health {
            access_log off;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $host;
        }
        
        # Frontend приложение
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF

echo "✅ SSL конфигурация создана!"
echo "🔄 Перезапуск nginx с SSL..."

# Перезапуск nginx
cd /root/advakod
docker-compose restart nginx

echo "✅ SSL настроен!"
echo "🌐 Сайт доступен по HTTPS: https://localhost"
echo "⚠️  Для продакшена замените самоподписанный сертификат на Let's Encrypt"
