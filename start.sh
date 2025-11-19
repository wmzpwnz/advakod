#!/bin/bash

echo "🚀 Запуск ИИ-Юриста для РФ..."

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker для запуска баз данных."
    exit 1
fi

# Проверяем наличие Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose."
    exit 1
fi

# Запускаем базы данных
echo "📦 Запуск баз данных (PostgreSQL, Qdrant, Redis)..."
docker-compose up -d

# Ждем запуска баз данных
echo "⏳ Ожидание запуска баз данных..."
sleep 10

# Проверяем Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не установлен."
    exit 1
fi

# Создаем виртуальное окружение если не существует
if [ ! -d "backend/venv" ]; then
    echo "🐍 Создание виртуального окружения..."
    cd backend
    python3 -m venv venv
    cd ..
fi

# Активируем виртуальное окружение
echo "🔧 Активация виртуального окружения..."
source backend/venv/bin/activate

# Устанавливаем зависимости backend
echo "📦 Установка зависимостей backend..."
cd backend
pip install -r requirements.txt

# Создаем .env файл если не существует
if [ ! -f ".env" ]; then
    echo "⚙️ Создание .env файла..."
    cp env.example .env
    echo "📝 Отредактируйте backend/.env файл с вашими настройками"
fi

# Создаем миграции базы данных
echo "🗄️ Создание миграций базы данных..."
alembic revision --autogenerate -m "Initial migration"

# Применяем миграции
echo "🔄 Применение миграций..."
alembic upgrade head

cd ..

# Проверяем Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js не установлен."
    exit 1
fi

# Устанавливаем зависимости frontend
echo "📦 Установка зависимостей frontend..."
cd frontend
npm install
cd ..

echo "✅ Установка завершена!"
echo ""
echo "🚀 Для запуска приложения:"
echo "1. Backend: cd backend && source venv/bin/activate && python main.py"
echo "2. Frontend: cd frontend && npm start"
echo ""
echo "📖 Документация API: http://localhost:8000/docs"
echo "🌐 Frontend: http://localhost:3000"
echo ""
echo "⚠️  Убедитесь, что модель Qwen находится по пути:"
echo "   /Users/macbook/llama.cpp/models/qwen2.5-1.5b-instruct-q4_k_m.gguf"
