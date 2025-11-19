#!/bin/bash

set -e  # Выход при любой ошибке

echo "🔧 ИСПРАВЛЕНИЕ БАЗЫ ДАННЫХ POSTGRESQL"
echo "====================================="

# Конфигурация
POSTGRES_USER="${POSTGRES_USER:-advakod}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-StrongPassword123}"  # Используем пароль из docker-compose.yml
POSTGRES_DB="${POSTGRES_DB:-advakod_db}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-advakod}"
DOCKER_COMPOSE_CMD="${DOCKER_COMPOSE_CMD:-docker-compose}"

# Проверка переменных
if [[ -z "$POSTGRES_PASSWORD" ]]; then
    echo "❌ ERROR: POSTGRES_PASSWORD не установлен!"
    exit 1
fi

# Останавливаем сервисы
echo "🛑 Остановка сервисов..."
$DOCKER_COMPOSE_CMD stop backend postgres || true

# Подтверждение удаления данных
read -p "⚠️  Вы уверены, что хотите УДАЛИТЬ ВСЕ ДАННЫЕ базы? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Отменено пользователем"
    exit 1
fi

# Удаляем том (с проверкой существования)
echo "🗑️ Удаление тома PostgreSQL..."
if docker volume ls | grep -q "${COMPOSE_PROJECT_NAME}_postgres_data"; then
    docker volume rm "${COMPOSE_PROJECT_NAME}_postgres_data"
else
    echo "ℹ️  Том не найден, пропускаем удаление"
fi

# Запускаем postgres
echo "🚀 Запуск PostgreSQL..."
$DOCKER_COMPOSE_CMD up -d postgres

# Ожидание с проверкой готовности
echo "⏳ Ожидание инициализации PostgreSQL..."
for i in {1..30}; do
    if docker exec "${COMPOSE_PROJECT_NAME}_postgres" pg_isready -U postgres >/dev/null 2>&1; then
        echo "✅ PostgreSQL готов"
        break
    fi
    echo "⏱️  Попытка $i/30..."
    sleep 2
done

# Создание БД и пользователя
echo "👤 Настройка базы данных..."
docker exec "${COMPOSE_PROJECT_NAME}_postgres" psql -U postgres -c "
    CREATE USER ${POSTGRES_USER} WITH PASSWORD '${POSTGRES_PASSWORD}';
    CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER};
    GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB} TO ${POSTGRES_USER};
    \c ${POSTGRES_DB};
    GRANT ALL ON SCHEMA public TO ${POSTGRES_USER};
" || {
    echo "❌ Ошибка создания БД"
    exit 1
}

# Запуск backend
echo "🚀 Запуск backend..."
$DOCKER_COMPOSE_CMD up -d backend

# Ожидание готовности backend
echo "⏳ Ожидание запуска backend..."
for i in {1..20}; do
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ Backend готов"
        break
    fi
    echo "⏱️  Попытка $i/20..."
    sleep 3
done

# Проверка подключения и миграций
echo "🔍 Проверка системы..."
docker exec "${COMPOSE_PROJECT_NAME}_backend" python -c "
import os
import psycopg2
import requests
try:
    # Проверка БД
    conn = psycopg2.connect(
        host='${COMPOSE_PROJECT_NAME}_postgres',
        database='${POSTGRES_DB}',
        user='${POSTGRES_USER}',
        password='${POSTGRES_PASSWORD}'
    )
    print('✅ База данных: OK')
    
    # Проверка health endpoint
    resp = requests.get('http://localhost:8000/health', timeout=10)
    if resp.status_code == 200:
        print('✅ Health endpoint: OK')
    else:
        print(f'❌ Health endpoint: {resp.status_code}')
        
    # Проверка ready endpoint  
    resp = requests.get('http://localhost:8000/ready', timeout=10)
    if resp.status_code == 200:
        print('✅ Ready endpoint: OK')
    else:
        print(f'⚠️ Ready endpoint: {resp.status_code}')
        
except Exception as e:
    print(f'❌ Ошибка проверки: {e}')
    exit(1)
"

echo "✅ Восстановление завершено!"
echo "🌐 Сайт: https://advacodex.com"
echo "📊 Проверьте логи: docker-compose logs -f"