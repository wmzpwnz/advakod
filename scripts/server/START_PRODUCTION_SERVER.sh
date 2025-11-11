#!/bin/bash

# Скрипт запуска A2codex.com на production сервере
# Сервер: advacodex.com
# Разработчик: Багбеков Азиз | Компания "Аврамир"

set -e

echo "🚀 Запуск A2codex.com на production сервере"
echo "================================================"
echo "Сервер: advacodex.com"
echo ""

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Проверяем, что мы на сервере
if [ ! -d "/opt/a2codex" ]; then
    echo -e "${RED}❌ Директория /opt/a2codex не найдена!${NC}"
    echo "Этот скрипт должен запускаться на production сервере."
    exit 1
fi

cd /opt/a2codex

echo -e "${BLUE}🔄 Шаг 1: Остановка существующих процессов${NC}"
pkill -f "python.*main.py" || true
pkill -f "npm.*start" || true
pkill -f "node.*" || true
sleep 2
echo -e "${GREEN}✅ Процессы остановлены${NC}"

echo -e "${BLUE}🐍 Шаг 2: Запуск Backend${NC}"
cd backend

# Активируем виртуальное окружение
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo -e "${RED}❌ Виртуальное окружение не найдено!${NC}"
    exit 1
fi

# Создаем директорию для логов
mkdir -p ../logs

# Запускаем backend
nohup python3 main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend.pid
echo -e "${GREEN}✅ Backend запущен (PID: $BACKEND_PID)${NC}"

# Ждем запуска backend
echo "⏳ Ожидание запуска backend..."
sleep 5

# Проверяем, что backend работает
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✅ Backend работает${NC}"
else
    echo -e "${RED}❌ Backend не запустился! Проверьте логи:${NC}"
    echo "tail -f logs/backend.log"
    exit 1
fi

echo -e "${BLUE}🌐 Шаг 3: Сборка Frontend${NC}"
cd ../frontend

# Устанавливаем зависимости если нужно
if [ ! -d "node_modules" ]; then
    echo "📦 Установка зависимостей..."
    npm install
fi

# Собираем production build
echo "🏗️ Сборка production build..."
npm run build

if [ -d "build" ]; then
    echo -e "${GREEN}✅ Frontend собран${NC}"
else
    echo -e "${RED}❌ Ошибка сборки frontend!${NC}"
    exit 1
fi

echo -e "${BLUE}🔧 Шаг 4: Настройка Nginx${NC}"

# Создаем конфигурацию nginx
cat > /tmp/a2codex_nginx.conf << 'EOF'
server {
    listen 80;
    server_name advacodex.com www.advacodex.com;

    # Frontend (React build)
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
        
        # Таймауты для AI запросов
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API Docs
    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
}
EOF

# Копируем конфигурацию
sudo cp /tmp/a2codex_nginx.conf /etc/nginx/sites-available/a2codex
sudo ln -sf /etc/nginx/sites-available/a2codex /etc/nginx/sites-enabled/a2codex

# Удаляем дефолтную конфигурацию
sudo rm -f /etc/nginx/sites-enabled/default

# Проверяем конфигурацию nginx
echo "🔍 Проверка конфигурации nginx..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Конфигурация nginx корректна${NC}"
    
    # Перезагружаем nginx
    echo "🔄 Перезагрузка nginx..."
    sudo systemctl reload nginx
    echo -e "${GREEN}✅ Nginx перезагружен${NC}"
else
    echo -e "${RED}❌ Ошибка в конфигурации nginx!${NC}"
    exit 1
fi

cd /opt/a2codex

echo ""
echo "=================================================="
echo -e "${GREEN}🎉 СЕРВЕР УСПЕШНО ЗАПУЩЕН!${NC}"
echo "=================================================="
echo ""
echo "🌐 Сайт доступен:"
echo "   http://advacodex.com"
echo "   http://www.advacodex.com"
echo ""
echo "📊 API:"
echo "   http://advacodex.com/api/v1/"
echo "   http://advacodex.com/docs"
echo ""
echo "🔍 Проверка:"
echo "   Backend: http://advacodex.com/health"
echo "   Frontend: http://advacodex.com"
echo ""
echo "📋 Логи:"
echo "   Backend: tail -f /opt/a2codex/logs/backend.log"
echo "   Nginx: sudo tail -f /var/log/nginx/error.log"
echo ""
echo "🔄 Управление:"
echo "   Остановить: pkill -f 'python.*main.py'"
echo "   Перезапустить: ./START_PRODUCTION_SERVER.sh"
echo ""
echo "👨‍💻 Разработчик: Багбеков Азиз | Компания \"Аврамир\""
echo "🌐 A2codex.com - Ваш ИИ-юрист готов к работе!"
echo "=================================================="
