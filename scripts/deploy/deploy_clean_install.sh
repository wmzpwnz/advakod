#!/bin/bash

# Полная переустановка A2codex.com на production сервер
# Сервер: 31.130.145.75
# Разработчик: Багбеков Азиз | Компания "Аврамир"

set -e

SERVER="31.130.145.75"
SERVER_USER="root"
SERVER_PASS="pG4Ju#i+i5+UPd"
SERVER_PATH="/opt/a2codex"
PROJECT_NAME="a2codex"

echo "🚀 Полная переустановка A2codex.com"
echo "=================================================="
echo "⚠️  ВНИМАНИЕ: Старые файлы будут удалены!"
echo "Сервер: $SERVER"
echo "Путь: $SERVER_PATH"
echo ""

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

read -p "Продолжить? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Отменено"
    exit 0
fi

echo ""
echo -e "${BLUE}📦 Шаг 1: Подготовка проекта${NC}"

# Создаем архив проекта
echo "Создание архива..."
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

echo -e "${GREEN}✅ Архив создан${NC}"

echo -e "${BLUE}🗑️  Шаг 2: Удаление старых файлов на сервере${NC}"

# Подключаемся к серверу и удаляем старые файлы
sshpass -p "$SERVER_PASS" ssh ${SERVER_USER}@${SERVER} << 'ENDSSH'

set -e

echo "🗑️ Остановка старых сервисов..."

# Останавливаем сервисы если они запущены
systemctl stop a2codex-backend 2>/dev/null || echo "Сервис не запущен"
systemctl disable a2codex-backend 2>/dev/null || echo "Сервис не был включен"

# Останавливаем процессы Python если запущены
pkill -f "python.*main.py" 2>/dev/null || echo "Процессы Python не найдены"
pkill -f "uvicorn" 2>/dev/null || echo "Uvicorn не запущен"

echo "✅ Старые сервисы остановлены"

echo "🗑️ Удаление старых файлов..."

# Создаем backup если директория существует
if [ -d "/opt/a2codex" ]; then
    BACKUP_DIR="/opt/backups/a2codex_$(date +%Y%m%d_%H%M%S)"
    mkdir -p /opt/backups
    echo "📦 Создание backup в $BACKUP_DIR..."
    mv /opt/a2codex $BACKUP_DIR
    echo "✅ Backup создан: $BACKUP_DIR"
else
    echo "Старая директория не найдена, пропускаем backup"
fi

# Удаляем старый systemd сервис
rm -f /etc/systemd/system/a2codex-backend.service
rm -f /etc/systemd/system/advakod-backend.service
systemctl daemon-reload

# Удаляем старую конфигурацию Nginx
rm -f /etc/nginx/sites-enabled/a2codex
rm -f /etc/nginx/sites-enabled/advakod
rm -f /etc/nginx/sites-available/a2codex
rm -f /etc/nginx/sites-available/advakod

echo "✅ Старые файлы удалены"

ENDSSH

echo -e "${GREEN}✅ Сервер очищен${NC}"

echo -e "${BLUE}📤 Шаг 3: Загрузка нового проекта${NC}"

# Загружаем архив
sshpass -p "$SERVER_PASS" scp ${PROJECT_NAME}.tar.gz ${SERVER_USER}@${SERVER}:/tmp/

echo -e "${GREEN}✅ Проект загружен${NC}"

echo -e "${BLUE}🔧 Шаг 4: Установка и настройка${NC}"

# Устанавливаем и настраиваем проект
sshpass -p "$SERVER_PASS" ssh ${SERVER_USER}@${SERVER} << 'ENDSSH'

set -e

echo "🔧 Установка проекта..."

# Создаем директорию
mkdir -p /opt/a2codex
cd /opt/a2codex

# Распаковываем
echo "📦 Распаковка..."
tar -xzf /tmp/a2codex.tar.gz -C /opt/a2codex
rm /tmp/a2codex.tar.gz

echo "✅ Проект распакован"

# Устанавливаем системные зависимости
echo "📥 Проверка системных зависимостей..."
apt-get update -qq

# Проверяем что установлено
command -v python3 >/dev/null 2>&1 || apt-get install -y python3 python3-pip python3-venv
command -v node >/dev/null 2>&1 || apt-get install -y nodejs npm
command -v nginx >/dev/null 2>&1 || apt-get install -y nginx
command -v redis-server >/dev/null 2>&1 || apt-get install -y redis-server
command -v psql >/dev/null 2>&1 || apt-get install -y postgresql postgresql-contrib

echo "✅ Системные зависимости готовы"

# Настройка PostgreSQL
echo "🗄️ Настройка PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql

sudo -u postgres psql << 'SQLEOF'
-- Создаем БД если не существует
SELECT 'CREATE DATABASE a2codex_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'a2codex_db')\gexec

-- Создаем пользователя если не существует
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'a2codex') THEN
    CREATE USER a2codex WITH PASSWORD 'a2codex_secure_pass_2025';
  END IF;
END
$$;

-- Даем права
GRANT ALL PRIVILEGES ON DATABASE a2codex_db TO a2codex;
SQLEOF

echo "✅ PostgreSQL настроен"

# Запускаем Redis
echo "🔴 Запуск Redis..."
systemctl start redis-server
systemctl enable redis-server

echo "✅ Redis запущен"

# Backend setup
echo "🐍 Настройка Backend..."
cd /opt/a2codex/backend

# Создаем виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
echo "📥 Установка Python зависимостей..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "✅ Python зависимости установлены"

# Создаем необходимые директории
mkdir -p logs uploads data/chroma_db documents

# Создаем .env файл
cat > .env << 'EOF'
# A2codex.com Production Configuration
# Разработчик: Багбеков Азиз | Компания "Аврамир"

SECRET_KEY=a2codex_super_secret_key_production_2025_very_long_and_secure_key_here_minimum_32_chars
ENCRYPTION_KEY=a2codex_encryption_key_production_2025_very_long_and_secure_key_minimum_32_chars
DATABASE_URL=postgresql://a2codex:a2codex_secure_pass_2025@localhost/a2codex_db
ENVIRONMENT=production
DEBUG=false
REDIS_URL=redis://localhost:6379/0

# Saiga Model
SAIGA_MODEL_PATH=/opt/models/saiga_mistral_7b_q4_K.gguf
SAIGA_N_CTX=4096
SAIGA_N_THREADS=4

# CORS
CORS_ORIGINS=https://a2codex.com,https://www.a2codex.com,http://31.130.145.75,http://localhost:3000

# ChromaDB
CHROMA_DB_PATH=/opt/a2codex/backend/data/chroma_db
CHROMA_COLLECTION_NAME=legal_documents

# Project Info
PROJECT_NAME=A2codex.com
VERSION=2.0.0
EOF

echo "✅ .env создан"

# Применяем миграции
echo "📊 Применение миграций БД..."
alembic upgrade head

echo "✅ Миграции применены"

# Инициализируем системы
echo "🏷️ Инициализация систем..."

# RBAC
python init_rbac.py 2>/dev/null || echo "RBAC уже инициализирован"

# Feedback система
python init_feedback_system.py

echo "✅ Системы инициализированы"

# Frontend setup
echo "🎨 Настройка Frontend..."
cd /opt/a2codex/frontend

# Создаем .env
cat > .env << 'EOF'
REACT_APP_API_URL=http://31.130.145.75
REACT_APP_WS_URL=ws://31.130.145.75
EOF

# Устанавливаем зависимости
echo "📥 Установка npm зависимостей..."
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
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;
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

echo "✅ Nginx настроен и запущен"

# Создаем systemd сервис
echo "⚙️ Создание systemd сервиса..."
cat > /etc/systemd/system/a2codex-backend.service << 'SERVICECONF'
[Unit]
Description=A2codex.com Backend API - AI Legal Assistant
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/a2codex/backend
Environment="PATH=/opt/a2codex/backend/venv/bin"
ExecStart=/opt/a2codex/backend/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=append:/opt/a2codex/backend/logs/service.log
StandardError=append:/opt/a2codex/backend/logs/service_error.log

[Install]
WantedBy=multi-user.target
SERVICECONF

# Перезагружаем systemd
systemctl daemon-reload
systemctl enable a2codex-backend
systemctl start a2codex-backend

echo "✅ Backend сервис запущен"

# Ждем запуска
echo "⏳ Ожидание запуска сервисов (30 сек)..."
sleep 30

# Проверка статуса
echo ""
echo "📊 Статус сервисов:"
echo "===================="

echo "Nginx:"
systemctl is-active nginx && echo "✅ Работает" || echo "❌ Не работает"

echo "Backend:"
systemctl is-active a2codex-backend && echo "✅ Работает" || echo "❌ Не работает"

echo "Redis:"
systemctl is-active redis-server && echo "✅ Работает" || echo "❌ Не работает"

echo "PostgreSQL:"
systemctl is-active postgresql && echo "✅ Работает" || echo "❌ Не работает"

# Проверка доступности API
echo ""
echo "🌐 Проверка доступности API..."
curl -s http://localhost:8000/health | grep -q "healthy" && echo "✅ API работает" || echo "⚠️ API не отвечает"

echo ""
echo "📋 Логи backend (последние 20 строк):"
tail -20 /opt/a2codex/backend/logs/service.log 2>/dev/null || echo "Логи пока пусты"

ENDSSH

echo ""
echo "=================================================="
echo -e "${GREEN}🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!${NC}"
echo "=================================================="
echo ""
echo "🌐 Сайт доступен:"
echo "   http://31.130.145.75"
echo ""
echo "📋 Доступные URL:"
echo "   🏠 Главная: http://31.130.145.75/"
echo "   💬 Чат: http://31.130.145.75/chat"
echo "   👮 Модерация: http://31.130.145.75/moderation"
echo "   📊 Аналитика: http://31.130.145.75/moderation-dashboard"
echo "   🔧 API Docs: http://31.130.145.75/docs"
echo "   ❤️ Health: http://31.130.145.75/health"
echo ""
echo "🔐 Следующие шаги:"
echo "   1. Создайте админа:"
echo "      ssh root@31.130.145.75"
echo "      cd /opt/a2codex/backend"
echo "      source venv/bin/activate"
echo "      python create_admin.py"
echo ""
echo "   2. Настройте DNS:"
echo "      a2codex.com → 31.130.145.75"
echo ""
echo "   3. Установите SSL (Let's Encrypt):"
echo "      certbot --nginx -d a2codex.com -d www.a2codex.com"
echo ""
echo "   4. Назначьте модераторов через админ-панель"
echo ""
echo "📊 Проверка логов:"
echo "   ssh root@31.130.145.75"
echo "   tail -f /opt/a2codex/backend/logs/service.log"
echo ""
echo "🔄 Управление сервисом:"
echo "   systemctl status a2codex-backend"
echo "   systemctl restart a2codex-backend"
echo "   systemctl stop a2codex-backend"
echo ""
echo "👨‍💻 Разработчик: Багбеков Азиз"
echo "🏢 Компания: Аврамир"
echo "🌐 A2codex.com"
echo "=================================================="

# Удаляем локальный архив
rm -f ${PROJECT_NAME}.tar.gz

echo ""
echo -e "${GREEN}✅ Готово! Проект развернут на сервере!${NC}"
