#!/bin/bash

echo "🔧 СОЗДАНИЕ ТАБЛИЦ В БАЗЕ ДАННЫХ"
echo "================================"

# Подключаемся к PostgreSQL и создаем таблицы
echo "📊 Создание таблицы users..."
docker exec advakod_postgres psql -U postgres -d advakod_db -c "
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_premium BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    subscription_type VARCHAR(50) DEFAULT 'free',
    subscription_expires TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    company_name VARCHAR(255),
    legal_form VARCHAR(100),
    inn VARCHAR(12),
    ogrn VARCHAR(15),
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(32),
    backup_codes TEXT
);

-- Создаем индексы
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_is_premium ON users(is_premium);
CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin);

-- Создаем тестового пользователя
INSERT INTO users (email, username, hashed_password, full_name, is_active, is_admin) 
VALUES ('admin@advacodex.com', 'admin', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4/LewdBPj4', 'Администратор', TRUE, TRUE)
ON CONFLICT (email) DO NOTHING;

-- Создаем обычного пользователя для тестирования
INSERT INTO users (email, username, hashed_password, full_name, is_active) 
VALUES ('test@test.com', 'testuser', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4/LewdBPj4', 'Тестовый пользователь', TRUE)
ON CONFLICT (email) DO NOTHING;

-- Проверяем созданные таблицы
\dt
"

echo "✅ Таблицы созданы!"
echo "🔍 Проверка подключения backend к базе данных..."

# Тестируем подключение через backend
docker exec advakod_backend python -c "
import os
import psycopg2
try:
    conn = psycopg2.connect(
        host='advakod_postgres',
        port=5432,
        database='advakod_db',
        user='advakod',
        password='StrongPassword123'
    )
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users;')
    count = cursor.fetchone()[0]
    print(f'✅ Подключение успешно! Пользователей в базе: {count}')
    conn.close()
except Exception as e:
    print(f'❌ Ошибка подключения: {e}')
"

echo "🌐 Тестирование API login..."
curl -X POST https://advacodex.com/api/v1/auth/login-email \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test"}' \
  -s | head -3

echo ""
echo "✅ База данных настроена!"
