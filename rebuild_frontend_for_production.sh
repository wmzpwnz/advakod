#!/bin/bash

echo "🔄 Пересборка фронтенда для продакшена"
echo "======================================="
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

# Создаем .env.production
cd frontend

echo "📝 Создаю .env.production..."
cat > .env.production << EOF
REACT_APP_API_URL=https://${DOMAIN}
REACT_APP_WS_URL=wss://${DOMAIN}
REACT_APP_ENV=production
EOF

echo "✅ Файл .env.production создан"
echo ""

# Показываем содержимое
echo "📄 Содержимое .env.production:"
cat .env.production
echo ""

# Пересборка
echo "🔨 Пересборка фронтенда..."
npm run build

if [ $? -eq 0 ]; then
  echo ""
  echo "✅ Фронтенд успешно пересобран!"
  echo ""
  echo "📦 Build находится в: frontend/build/"
  echo ""
  echo "🚀 Следующие шаги:"
  echo "   1. Скопируйте build на сервер:"
  echo "      scp -r build/ user@server:/path/to/advakod/frontend/"
  echo ""
  echo "   2. На сервере перезапустите:"
  echo "      docker-compose -f docker-compose.prod.yml restart frontend nginx"
  echo ""
  echo "   3. Проверьте сайт: https://${DOMAIN}"
else
  echo ""
  echo "❌ Ошибка при сборке фронтенда!"
  exit 1
fi

