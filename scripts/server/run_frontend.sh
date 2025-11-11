#!/bin/bash

echo "🚀 Запуск frontend ИИ-Юриста..."

cd frontend

# Проверяем наличие node_modules
if [ ! -d "node_modules" ]; then
    echo "❌ node_modules не найдены. Запустите start.sh сначала."
    exit 1
fi

# Запускаем React приложение
echo "🌐 Запуск React приложения на http://localhost:3000"
echo ""

npm start
