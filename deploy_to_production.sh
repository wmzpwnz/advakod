#!/bin/bash
# Скрипт развертывания A2codex.com на production сервер
# Сервер: 31.130.145.75
# Разработчик: Багбеков Азиз | Компания "Аврамир"

set -e

SERVER="31.130.145.75"
USER="root"
PASSWORD="pG4Ju#i+i5+UPd"
PROJECT_DIR="/opt/a2codex"
DOMAIN="a2codex.com"

echo "🚀 Развертывание A2codex.com на production"
echo "Сервер: $SERVER"
echo "=================================================="

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}📦 Шаг 1: Подготовка локального проекта${NC}"

# Создаем архив проекта (исключая ненужное)
echo "Создание архива проекта..."
tar -czf a2codex_deploy.tar.gz \
  --exclude='node_modules' \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='*.pyc' \
  --exclude='*.log' \
  --exclude='backend/data/chroma_db' \
  --exclude='backend/uploads' \
  --exclude='frontend/build' \
  backend/ frontend/ *.sh *.md docker-compose.prod.yml nginx.conf Makefile

echo -e "${GREEN}✅ Архив создан: a2codex_deploy.tar.gz${NC}"

echo -e "${BLUE}📤 Шаг 2: Загрузка на сервер${NC}"

# Загружаем архив на сервер
sshpass -p "$PASSWORD" scp a2codex_deploy.tar.gz $USER@$SERVER:/tmp/

echo -e "${GREEN}✅ Файлы загружены на сервер${NC}"

echo -e "${BLUE}🔧 Шаг 3: Настройка сервера${NC}"

# Подключаемся к серверу и выполняем команды
sshpass -p "$PASSWORD" ssh $USER@$SERVER << 'ENDSSH'

set -e

echo "🔧 Настройка production сервера для A2codex.com"

# Обновляем систему
apt-get update
apt-get install -y python3 python3-pip python3-venv nodejs npm nginx redis-server postgresql

# Создаем директорию проекта
mkdir -p /opt/a2codex
cd /opt/a2codex

# Распаковываем архив
tar -xzf /tmp/a2codex_deploy.tar.gz -C /opt/a2codex
rm /tmp/a2codex_deploy.tar.gz

echo "✅ Проект распакован"

# Настройка backend
cd /opt/a2codex/backend

# Создаем виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
pip install --upgrade pip
pip install -r requirements.txt

# Создаем .env если не существует
if [ ! -f .env ]; then
    cat > .env << 'EOF'
SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)
DATABASE_URL=postgresql://a2codex:a2codex_pass@localhost/a2codex_db
ENVIRONMENT=production
DEBUG=false
REDIS_URL=redis://localhost:6379
ALLOWED_ORIGINS=https://a2codex.com,https://www.a2codex.com
EOF
fi

echo "✅ Backend настроен"

# Настройка PostgreSQL
sudo -u postgres psql << 'EOSQL'
CREATE DATABASE a2codex_db;
CREATE USER a2codex WITH PASSWORD 'a2codex_pass';
GRANT ALL PRIVILEGES ON DATABASE a2codex_db TO a2codex;
EOSQL

echo "✅ База данных создана"

# Применяем миграции
source venv/bin/activate
alembic upgrade head
python init_feedback_system.py

echo "✅ Миграции применены"

ENDSSH

echo -e "${GREEN}✅ Сервер настроен${NC}"


echo -e "${BLUE}🎨 Шаг 4: Настройка frontend${NC}"

sshpass -p "$PASSWORD" ssh $USER@$SERVER << 'ENDSSH'

cd /opt/a2codex/frontend

# Устанавливаем зависимости
npm install

# Создаем .env для production
cat > .env << 'EOF'
REACT_APP_API_URL=https://a2codex.com
REACT_APP_WS_URL=wss://a2codex.com
EOF

# Собираем production build
npm run build

echo "✅ Frontend собран"

ENDSSH

echo -e "${GREEN}✅ Frontend готов${NC}"

echo -e "${BLUE}🌐 Шаг 5: Настройка Nginx${NC}"

sshpass -p "$PASSWORD" ssh $USER@$SERVER << 'ENDSSH'

# Создаем конфигурацию Nginx
cat > /etc/nginx/sites-available/a2codex << 'EOF'
server {
    listen 80;
    server_name a2codex.com www.a2codex.com;

    # Frontend
    location / {
        root /opt/a2codex/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
EOF

# Активируем конфигурацию
ln -sf /etc/nginx/sites-available/a2codex /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo "✅ Nginx настроен"

ENDSSH

echo -e "${GREEN}✅ Nginx готов${NC}"


echo -e "${BLUE}🚀 Шаг 6: Создание systemd сервисов${NC}"

sshpass -p "$PASSWORD" ssh $USER@$SERVER << 'ENDSSH'

# Backend service
cat > /etc/systemd/system/a2codex-backend.service << 'EOF'
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
EOF

# Перезагружаем systemd и запускаем сервисы
systemctl daemon-reload
systemctl enable a2codex-backend
systemctl start a2codex-backend

echo "✅ Systemd сервисы созданы и запущены"

ENDSSH

echo -e "${GREEN}✅ Сервисы запущены${NC}"

echo ""
echo "=================================================="
echo -e "${GREEN}🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО УСПЕШНО!${NC}"
echo "=================================================="
echo ""
echo "📋 Что было сделано:"
echo "  ✅ Проект загружен на сервер"
echo "  ✅ Backend настроен и запущен"
echo "  ✅ Frontend собран"
echo "  ✅ База данных создана"
echo "  ✅ Миграции применены"
echo "  ✅ Nginx настроен"
echo "  ✅ Systemd сервисы запущены"
echo ""
echo "🌐 Сайт доступен по адресу:"
echo "  http://a2codex.com"
echo ""
echo "🔧 Полезные команды:"
echo "  Статус backend: ssh root@$SERVER 'systemctl status a2codex-backend'"
echo "  Логи backend: ssh root@$SERVER 'journalctl -u a2codex-backend -f'"
echo "  Перезапуск: ssh root@$SERVER 'systemctl restart a2codex-backend'"
echo ""
echo "👨‍💻 Разработчик: Багбеков Азиз | Компания Аврамир"
echo "=================================================="

# Очистка
rm -f a2codex_deploy.tar.gz

echo -e "${GREEN}✅ Готово!${NC}"
