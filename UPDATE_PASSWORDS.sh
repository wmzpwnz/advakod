#!/bin/bash

# Генерация безопасных паролей для продакшена
echo "🔐 ГЕНЕРАЦИЯ БЕЗОПАСНЫХ ПАРОЛЕЙ ДЛЯ ПРОДАКШЕНА"
echo "=============================================="

# Генерируем случайные пароли
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
SECRET_KEY=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-64)
ENCRYPTION_KEY=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-64)

echo "📋 НОВЫЕ БЕЗОПАСНЫЕ ПАРОЛИ:"
echo "POSTGRES_PASSWORD: $POSTGRES_PASSWORD"
echo "SECRET_KEY: $SECRET_KEY"
echo "ENCRYPTION_KEY: $ENCRYPTION_KEY"
echo ""

# Обновляем env.production
echo "🔄 Обновление env.production..."
sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=\"$POSTGRES_PASSWORD\"/" /root/advakod/env.production
sed -i "s/SECRET_KEY=.*/SECRET_KEY=\"$SECRET_KEY\"/" /root/advakod/env.production
sed -i "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=\"$ENCRYPTION_KEY\"/" /root/advakod/env.production

# Обновляем docker-compose.yml
echo "🔄 Обновление docker-compose.yml..."
sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" /root/advakod/docker-compose.yml
sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" /root/advakod/docker-compose.yml
sed -i "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=$ENCRYPTION_KEY/" /root/advakod/docker-compose.yml

echo "✅ Пароли обновлены!"
echo "⚠️  ВАЖНО: Сохраните эти пароли в безопасном месте!"
echo "🔄 Перезапуск системы с новыми паролями..."

# Перезапуск системы
cd /root/advakod
docker-compose down
docker-compose up -d

echo "✅ Система перезапущена с новыми паролями!"
