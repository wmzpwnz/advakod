#!/bin/bash

# Скрипт для исправления проблемы с CSS и деплоя
# Исправляет конфигурацию Nginx и пересобирает frontend

set -e

echo "🔧 Исправление проблемы с CSS на advacodex.com"
echo "================================================"

# Проверяем что мы в правильной директории
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ Ошибка: docker-compose.prod.yml не найден. Запустите скрипт из корневой директории проекта."
    exit 1
fi

echo "📋 Шаг 1: Остановка текущих контейнеров..."
docker-compose -f docker-compose.prod.yml down

echo "🧹 Шаг 2: Очистка старых образов frontend..."
docker rmi advakod_frontend:latest || true
docker rmi advakod-frontend:latest || true

echo "🏗️ Шаг 3: Пересборка frontend с исправленной конфигурацией..."
docker-compose -f docker-compose.prod.yml build --no-cache frontend

echo "🏗️ Шаг 4: Пересборка nginx с обновленной конфигурацией..."
docker-compose -f docker-compose.prod.yml build --no-cache nginx || true

echo "🚀 Шаг 5: Запуск обновленных сервисов..."
docker-compose -f docker-compose.prod.yml up -d

echo "⏳ Шаг 6: Ожидание запуска сервисов..."
sleep 30

echo "🔍 Шаг 7: Проверка статуса сервисов..."
docker-compose -f docker-compose.prod.yml ps

echo "🧪 Шаг 8: Тестирование CSS файлов..."
echo "Проверяем доступность CSS файла..."

# Ждем пока сервисы полностью запустятся
sleep 10

# Проверяем CSS файл
CSS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/static/css/main.0e3cbb1b.css || echo "000")
if [ "$CSS_STATUS" = "200" ]; then
    echo "✅ CSS файл доступен (HTTP $CSS_STATUS)"
else
    echo "❌ CSS файл недоступен (HTTP $CSS_STATUS)"
    echo "Проверяем логи nginx..."
    docker logs advakod_nginx --tail 20
    echo "Проверяем логи frontend..."
    docker logs advakod_frontend --tail 20
fi

# Проверяем главную страницу
MAIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ || echo "000")
if [ "$MAIN_STATUS" = "200" ]; then
    echo "✅ Главная страница доступна (HTTP $MAIN_STATUS)"
else
    echo "❌ Главная страница недоступна (HTTP $MAIN_STATUS)"
fi

echo ""
echo "🎯 Исправление завершено!"
echo "================================================"
echo "📊 Результаты:"
echo "   - CSS файл: HTTP $CSS_STATUS"
echo "   - Главная страница: HTTP $MAIN_STATUS"
echo ""
echo "🌐 Проверьте сайт: https://advacodex.com"
echo "🔧 Если проблемы остались, проверьте логи:"
echo "   docker logs advakod_nginx"
echo "   docker logs advakod_frontend"
echo ""