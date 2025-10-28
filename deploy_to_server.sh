#!/bin/bash

# Скрипт развертывания A2codex.com на production сервер
# Сервер: 31.130.145.75
# Разработчик: Багбеков Азиз | Компания "Аврамир"

set -e

SERVER="31.130.145.75"
SERVER_USER="root"
SERVER_PATH="/opt/a2codex"
PROJECT_NAME="a2codex"

echo "🚀 Развертывание A2codex.com на production сервер"
echo "=================================================="
echo "Сервер: $SERVER"
echo "Путь: $SERVER_PATH"
echo ""

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}📦 Шаг 1: Подготовка проекта к деплою${NC}"

# Создаем архив проекта (исключая ненужное)
echo "Создание архива проекта..."
tar -czf ${PROJECT_NAME}.tar.gz \
  --exclude='node_modules' \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='*.pyc' \
  --exclude='.DS_Store' \
  --exclude='backend/logs/*' \
  --exclude='backend/uploads/*' \
  --exclude='backend/data/chroma_db/*' \
  --exclude='backend/*.db' \
  --exclude='frontend/build' \
  .

echo -e "${GREEN}✅ Архив создан: ${PROJECT_NAME}.tar.gz${NC}"

echo -e "${BLUE}📤 Шаг 2: Загрузка на сервер${NC}"

# Загружаем архив на сервер
scp ${PROJECT_NAME}.tar.gz ${SERVER_USER}@${SERVER}:/tmp/

echo -e "${GREEN}✅ Файлы загружены на сервер${NC}"

echo -e "${BLUE}🔧 Шаг 3: Настройка сервера${NC}"

# Выполняем команды на сервере
ssh ${SERVER_USER}@${SERVER} << 'ENDSSH'

set -e

echo "🔧 Настройка сервера..."

# Создаем директорию проекта
mkdir -p /opt/a2codex
cd /opt/a2codex

# Распаковываем архив
echo "📦 Распаковка проекта..."
tar -xzf /tmp/a2codex.tar.gz -C /opt/a2codex
rm /tmp/a2codex.tar.gz

echo "✅ Проект распакован"

# Устанавливаем системные зависимости
echo "📥 Установка системных зависимостей..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv nodejs npm nginx redis-server postgresql postgresql-contrib

echo "✅ Системные зависимости установлены"

# Настройка PostgreSQL
echo "🗄️ Настройка PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE a2codex_db;" 2>/dev/null || echo "БД уже существует"
sudo -u postgres psql -c "CREATE USER a2codex WITH PASSWORD 'a2codex_secure_pass_2025';" 2>/dev/null || echo "Пользователь уже существует"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE a2codex_db TO a2codex;" 2>/dev/null

echo "✅ PostgreSQL настроен"

# Backend setup
echo "🐍 Настройка Backend..."
cd /opt/a2codex/backend

# Создаем виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Создаем .env файл
cat > .env << 'EOF'
# A2codex.com Production Configuration
SECRET_KEY=a2codex_super_secret_key_production_2025_very_long_and_secure_key_here
ENCRYPTION_KEY=a2codex_encryption_key_production_2025_very_long_and_secure_key
DATABASE_URL=postgresql://a2codex:a2codex_secure_pass_2025@localhost/a2codex_db
ENVIRONMENT=production
DEBUG=false
REDIS_URL=redis://localhost:6379/0

# Saiga Model
SAIGA_MODEL_PATH=/opt/models/saiga_mistral_7b_q4_K.gguf
SAIGA_N_CTX=4096
SAIGA_N_THREADS=4

# CORS
CORS_ORIGINS=https://a2codex.com,https://www.a2codex.com,http://31.130.145.75

# ChromaDB
CHROMA_DB_PATH=/opt/a2codex/backend/data/chroma_db
CHROMA_COLLECTION_NAME=legal_documents
EOF

echo "✅ Backend .env создан"

# Применяем миграции
echo "📊 Применение миграций..."
alembic upgrade head

# Инициализируем систему обратной связи
echo "🏷️ Инициализация системы обратной связи..."
python init_feedback_system.py

# Инициализируем RBAC
echo "🔐 Инициализация RBAC..."
python init_rbac.py 2>/dev/null || echo "RBAC уже инициализирован"

echo "✅ Backend настроен"

# Frontend setup
echo "🎨 Настройка Frontend..."
cd /opt/a2codex/frontend

# Создаем .env файл
cat > .env << 'EOF'
REACT_APP_API_URL=https://a2codex.com
REACT_APP_WS_URL=wss://a2codex.com
EOF

# Устанавливаем зависимости
npm install --silent

# Собираем production build
echo "🏗️ Сборка production build..."
npm run build

echo "✅ Frontend собран"

# Настройка Nginx
echo "🌐 Настройка Nginx..."
cat > /etc/nginx/sites-available/a2codex << 'NGINXCONF'
server {
    listen 80;
    server_name a2codex.com www.a2codex.com 31.130.145.75;

    # Frontend
    location / {
        root /opt/a2codex/frontend/build;
        try_files $uri $uri/ /index.html;
        
        # Кэширование статики
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 180s;
        proxy_connect_timeout 180s;
        proxy_send_timeout 180s;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }

    # Docs
    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    client_max_body_size 50M;
}
NGINXCONF

# Активируем конфигурацию
ln -sf /etc/nginx/sites-available/a2codex /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Проверяем конфигурацию
nginx -t

# Перезапускаем Nginx
systemctl restart nginx
systemctl enable nginx

echo "✅ Nginx настроен"

# Создаем systemd сервис для backend
echo "⚙️ Создание systemd сервиса..."
cat > /etc/systemd/system/a2codex-backend.service << 'SERVICECONF'
[Unit]
Description=A2codex Backend API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/a2codex/backend
Environment="PATH=/opt/a2codex/backend/venv/bin"
ExecStart=/opt/a2codex/backend/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICECONF

# Перезагружаем systemd
systemctl daemon-reload
systemctl enable a2codex-backend
systemctl restart a2codex-backend

echo "✅ Backend сервис создан и запущен"

# Проверка статуса
echo ""
echo "📊 Проверка статуса сервисов..."
systemctl status nginx --no-pager -l | head -5
systemctl status a2codex-backend --no-pager -l | head -5
systemctl status redis --no-pager -l | head -5
systemctl status postgresql --no-pager -l | head -5

echo ""
echo "✅ Все сервисы запущены"

ENDSSH

echo ""
echo "=================================================="
echo -e "${GREEN}🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО УСПЕШНО!${NC}"
echo "=================================================="
echo ""
echo "🌐 Сайт доступен по адресу:"
echo "   http://31.130.145.75"
echo "   http://a2codex.com (после настройки DNS)"
echo ""
echo "📋 Доступные URL:"
echo "   Frontend: http://31.130.145.75/"
echo "   Backend API: http://31.130.145.75/api/v1/"
echo "   API Docs: http://31.130.145.75/docs"
echo "   Модерация: http://31.130.145.75/moderation"
echo "   Аналитика: http://31.130.145.75/moderation-dashboard"
echo ""
echo "🔐 Следующие шаги:"
echo "   1. Настройте DNS для a2codex.com → 31.130.145.75"
echo "   2. Установите SSL сертификат (Let's Encrypt)"
echo "   3. Создайте админа: cd /opt/a2codex/backend && python create_admin.py"
echo "   4. Назначьте модераторов через админ-панель"
echo ""
echo "👨‍💻 Разработчик: Багбеков Азиз | Компания Аврамир"
echo "🌐 A2codex.com - Ваш ИИ-юрист готов к работе!"
echo "=================================================="

# Удаляем локальный архив
rm -f ${PROJECT_NAME}.tar.gz
