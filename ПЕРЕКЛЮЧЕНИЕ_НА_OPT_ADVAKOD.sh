#!/bin/bash
# Скрипт для безопасного переключения production на /opt/advakod

set -e

OLD_DIR="/root/advakod_backup_20251029_005854"
NEW_DIR="/opt/advakod"

echo "🔄 Переключение production на $NEW_DIR..."

# 1. Остановить контейнеры в старой папке
echo "1. Останавливаю контейнеры в $OLD_DIR..."
cd "$OLD_DIR"
docker-compose -f docker-compose.prod.yml down

# 2. Переключиться на новую папку
echo "2. Запускаю контейнеры в $NEW_DIR..."
cd "$NEW_DIR"
docker-compose -f docker-compose.prod.yml up -d

# 3. Проверить статус
echo "3. Проверяю статус контейнеров..."
sleep 10
docker-compose -f docker-compose.prod.yml ps

# 4. Проверить здоровье сервисов
echo "4. Проверяю здоровье сервисов..."
sleep 20
docker exec advakod_backend curl -f http://localhost:8000/api/v1/health || {
    echo "❌ Backend не отвечает!"
    exit 1
}

echo "✅ Переключение завершено успешно!"

