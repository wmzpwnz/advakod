#!/bin/bash

echo "🚀 Запуск backend ИИ-Юриста..."

cd backend

# Активируем виртуальное окружение
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Виртуальное окружение активировано"
else
    echo "❌ Виртуальное окружение не найдено. Запустите start.sh сначала."
    exit 1
fi

# Проверяем наличие .env файла
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден. Скопируйте env.example в .env и настройте."
    exit 1
fi

# Запускаем сервер
echo "🌐 Запуск FastAPI сервера на http://localhost:8000"
echo "📖 Документация API: http://localhost:8000/docs"
echo ""

python main.py
