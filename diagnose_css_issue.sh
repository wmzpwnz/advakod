#!/bin/bash

# Диагностика проблемы с CSS
echo "🔍 Диагностика проблемы с CSS на advacodex.com"
echo "=============================================="

echo "📋 1. Проверка статуса контейнеров:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "📋 2. Проверка CSS файла локально:"
if [ -f "frontend/build/static/css/main.0e3cbb1b.css" ]; then
    echo "✅ CSS файл существует в build"
    ls -la frontend/build/static/css/
else
    echo "❌ CSS файл отсутствует в build"
fi

echo ""
echo "📋 3. Проверка доступности через HTTP:"
curl -I http://localhost/static/css/main.0e3cbb1b.css

echo ""
echo "📋 4. Логи nginx (последние 10 строк):"
docker logs advakod_nginx --tail 10

echo ""
echo "📋 5. Логи frontend (последние 10 строк):"
docker logs advakod_frontend --tail 10