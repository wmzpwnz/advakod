#!/bin/bash

# Скрипт для копирования обновленного фронтенда на сервер
# Замените YOUR_SERVER_IP на реальный IP вашего сервера

echo "🚀 Копируем обновленный фронтенд на сервер..."

# Замените на ваш реальный IP сервера
SERVER_IP="YOUR_SERVER_IP"
SERVER_USER="root"  # или ваш пользователь
SERVER_PATH="/root/advakod"  # путь на сервере

# Проверяем что build существует
if [ ! -d "frontend/build" ]; then
    echo "❌ Ошибка: frontend/build не найден!"
    echo "Сначала выполните: cd frontend && npm run build"
    exit 1
fi

echo "📦 Копируем build на сервер..."

# Копируем build на сервер
rsync -avz --delete frontend/build/ ${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/frontend/build/

if [ $? -eq 0 ]; then
    echo "✅ Фронтенд успешно скопирован на сервер!"
    echo ""
    echo "🔄 Теперь нужно перезапустить Docker контейнеры на сервере:"
    echo "ssh ${SERVER_USER}@${SERVER_IP}"
    echo "cd ${SERVER_PATH}"
    echo "docker-compose -f docker-compose.prod.yml restart frontend"
    echo ""
    echo "🌐 После этого сайт должен работать на https://advacodex.com"
else
    echo "❌ Ошибка при копировании на сервер"
    exit 1
fi
