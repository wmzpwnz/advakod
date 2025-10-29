#!/bin/bash

echo "🔧 СОЗДАНИЕ ВСЕХ НЕДОСТАЮЩИХ ТАБЛИЦ"
echo "===================================="

# Создаем все необходимые таблицы
echo "📊 Создание таблицы token_balances..."
docker exec advakod_postgres psql -U advakod -d advakod_db -c "
CREATE TABLE IF NOT EXISTS token_balances (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    balance INTEGER DEFAULT 1000 NOT NULL,
    total_earned INTEGER DEFAULT 0 NOT NULL,
    total_spent INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_token_balances_user_id ON token_balances(user_id);
"

echo "📊 Создание таблицы chat_sessions..."
docker exec advakod_postgres psql -U advakod -d advakod_db -c "
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at);
"

echo "📊 Создание таблицы chat_messages..."
docker exec advakod_postgres psql -U advakod -d advakod_db -c "
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES chat_sessions(id),
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    message_metadata JSONB,
    audio_url VARCHAR(500),
    audio_duration INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);
"

echo "📊 Создание таблицы token_transactions..."
docker exec advakod_postgres psql -U advakod -d advakod_db -c "
CREATE TABLE IF NOT EXISTS token_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    amount INTEGER NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    description TEXT,
    chat_session_id INTEGER REFERENCES chat_sessions(id),
    chat_message_id INTEGER REFERENCES chat_messages(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_token_transactions_user_id ON token_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_token_transactions_created_at ON token_transactions(created_at);
"

echo "📊 Создание таблицы document_analyses..."
docker exec advakod_postgres psql -U advakod -d advakod_db -c "
CREATE TABLE IF NOT EXISTS document_analyses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    analysis_result TEXT NOT NULL,
    risks_found JSONB,
    recommendations TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_document_analyses_user_id ON document_analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_document_analyses_created_at ON document_analyses(created_at);
"

echo "📊 Создание начальных балансов токенов для всех пользователей..."
docker exec advakod_postgres psql -U advakod -d advakod_db -c "
INSERT INTO token_balances (user_id, balance, total_earned, total_spent)
SELECT id, 1000, 0, 0 FROM users
ON CONFLICT (user_id) DO NOTHING;
"

echo "📊 Проверка созданных таблиц..."
docker exec advakod_postgres psql -U advakod -d advakod_db -c "\dt"

echo "📊 Проверка балансов токенов..."
docker exec advakod_postgres psql -U advakod -d advakod_db -c "
SELECT 
    u.email,
    u.username,
    tb.balance,
    tb.total_earned,
    tb.total_spent
FROM users u
LEFT JOIN token_balances tb ON u.id = tb.user_id
ORDER BY u.id;
"

echo "✅ Все таблицы созданы!"
echo "🌐 Проверьте сайт: https://advacodex.com"
