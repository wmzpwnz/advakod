#!/bin/bash

echo "🚀 ПОЛНАЯ ИНТЕГРАЦИЯ САЙТА ADVAKOD"
echo "=================================="
echo ""

# Запрос домена у пользователя
read -p "🌐 Введите ваш домен (например, advacodex.com): " DOMAIN

if [ -z "$DOMAIN" ]; then
  echo "❌ Домен не указан!"
  exit 1
fi

echo ""
echo "✅ Домен: $DOMAIN"
echo ""

# 1. Создаем production .env для frontend
echo "📝 Создаю frontend/.env.production..."
cd frontend

cat > .env.production << EOF
# ========================================
# АДВАКОД - Production Environment
# Frontend Configuration
# ========================================

# API Configuration
REACT_APP_API_URL=https://${DOMAIN}
REACT_APP_WS_URL=wss://${DOMAIN}

# App Configuration
REACT_APP_NAME="АДВАКОД"
REACT_APP_VERSION="1.0.0"
REACT_APP_ENV=production

# Build Configuration
GENERATE_SOURCEMAP=false
PORT=3000

# Performance
REACT_APP_OPTIMIZE_CHUNKS=true
REACT_APP_ENABLE_SW=true
EOF

echo "✅ Файл frontend/.env.production создан"
echo ""

# 2. Создаем production .env для backend
echo "📝 Создаю backend/.env.production..."
cd ../backend

cat > .env.production << EOF
# ========================================
# АДВАКОД - Production Environment
# Backend Configuration
# ========================================

# Основные настройки
PROJECT_NAME="АДВАКОД - ИИ-Юрист для РФ"
ENVIRONMENT=production
DEBUG=false

# Безопасность (ЗАМЕНИТЕ НА СЛУЧАЙНЫЕ КЛЮЧИ!)
SECRET_KEY=YOUR_PRODUCTION_SECRET_KEY_MINIMUM_32_CHARACTERS_WITH_UPPERCASE_LOWERCASE_DIGITS
ENCRYPTION_KEY=YOUR_PRODUCTION_ENCRYPTION_KEY_MINIMUM_32_CHARACTERS

# PostgreSQL Database (Production)
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=advakod
POSTGRES_PASSWORD=YOUR_STRONG_POSTGRES_PASSWORD_HERE
POSTGRES_DB=advakod_db
DATABASE_URL=postgresql://advakod:YOUR_STRONG_POSTGRES_PASSWORD_HERE@postgres:5432/advakod_db

# CORS (ваш домен)
CORS_ORIGINS=https://${DOMAIN},https://www.${DOMAIN}

# Redis
REDIS_URL=redis://redis:6379

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=legal_documents

# AI Models
VISTRAL_MODEL_PATH=/opt/advakod/models/vistral-24b-instruct-q4_K_M.gguf
VISTRAL_N_CTX=8192
VISTRAL_N_THREADS=8
VISTRAL_N_GPU_LAYERS=0
VISTRAL_INFERENCE_TIMEOUT=900
VISTRAL_MAX_CONCURRENCY=1

# Таймауты
AI_DOCUMENT_ANALYSIS_TIMEOUT=300
AI_CHAT_RESPONSE_TIMEOUT=120
AI_COMPLEX_ANALYSIS_TIMEOUT=600

# Токены
AI_DOCUMENT_ANALYSIS_TOKENS=30000
AI_CHAT_RESPONSE_TOKENS=4000

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=480
ALGORITHM=HS256

# Директории
UPLOAD_DIR=uploads
LOG_DIR=logs
TEMP_DIR=temp

# Кэширование
CACHE_TTL_DEFAULT=3600
CACHE_TTL_AI_RESPONSE=7200
CACHE_TTL_USER_PROFILE=1800

# Логирование
LOG_PROMPTS=false
EOF

echo "✅ Файл backend/.env.production создан"
echo ""

# 3. Пересобираем frontend
echo "🔨 Пересборка frontend для продакшена..."
cd ../frontend

# Устанавливаем зависимости если нужно
if [ ! -d "node_modules" ]; then
  echo "📦 Устанавливаю зависимости..."
  npm install
fi

# Пересборка
npm run build

if [ $? -eq 0 ]; then
  echo ""
  echo "✅ Frontend успешно пересобран!"
  echo ""
  echo "📦 Build находится в: frontend/build/"
  echo ""
  
  # Проверяем что в build нет localhost
  echo "🔍 Проверяю build на наличие localhost..."
  if grep -r "localhost" build/static/js/*.js > /dev/null 2>&1; then
    echo "⚠️  ВНИМАНИЕ: В build найдены упоминания localhost!"
    echo "   Это может означать что .env.production не применился"
    echo "   Проверьте содержимое .env.production"
  else
    echo "✅ Build чистый - localhost не найден"
  fi
  
  echo ""
  echo "🚀 СЛЕДУЮЩИЕ ШАГИ:"
  echo ""
  echo "1. 📝 ОБЯЗАТЕЛЬНО замените ключи в backend/.env.production:"
  echo "   SECRET_KEY=ваш-случайный-ключ-32-символа"
  echo "   ENCRYPTION_KEY=ваш-случайный-ключ-32-символа"
  echo "   POSTGRES_PASSWORD=ваш-сильный-пароль"
  echo ""
  echo "2. 📤 Загрузите на сервер:"
  echo "   scp -r build/ user@server:/path/to/advakod/frontend/"
  echo ""
  echo "3. 🐳 Или используйте Docker:"
  echo "   docker-compose -f docker-compose.prod.yml build frontend"
  echo "   docker-compose -f docker-compose.prod.yml up -d"
  echo ""
  echo "4. ✅ Проверьте сайт:"
  echo "   https://${DOMAIN}"
  echo "   https://${DOMAIN}/api/v1/health"
  echo ""
  echo "5. 🔧 Если что-то не работает:"
  echo "   - Проверьте логи: docker-compose logs backend frontend"
  echo "   - Проверьте CORS в backend/.env.production"
  echo "   - Убедитесь что домен указан правильно"
  echo ""
  echo "=================================="
  echo "🎉 САЙТ ГОТОВ К ЗАПУСКУ!"
  echo "=================================="
  
else
  echo ""
  echo "❌ Ошибка при сборке фронтенда!"
  echo "Проверьте:"
  echo "1. Установлены ли зависимости: npm install"
  echo "2. Правильно ли указан домен в .env.production"
  echo "3. Нет ли синтаксических ошибок в коде"
  exit 1
fi
