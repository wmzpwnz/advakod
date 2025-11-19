#!/bin/bash
# Генерация секретных ключей для env.production
# Использование: ./scripts/generate_secrets.sh

echo "🔐 Генерация секретных ключей для ADVAKOD"
echo "=========================================="
echo ""

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен"
    exit 1
fi

echo "📝 Генерирую SECRET_KEY..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
echo "SECRET_KEY=\"$SECRET_KEY\""
echo ""

echo "📝 Генерирую ENCRYPTION_KEY..."
ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "ENCRYPTION_KEY=\"$ENCRYPTION_KEY\""
echo ""

echo "📝 Генерирую POSTGRES_PASSWORD..."
POSTGRES_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "POSTGRES_PASSWORD=\"$POSTGRES_PASSWORD\""
echo ""

echo "=========================================="
echo "✅ Скопируйте эти значения в env.production"
echo ""
echo "Или автоматически обновить env.production? (y/n)"
read -p "> " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "env.production" ]; then
        # Обновляем SECRET_KEY
        if grep -q "^SECRET_KEY=" env.production; then
            sed -i "s|^SECRET_KEY=.*|SECRET_KEY=\"$SECRET_KEY\"|" env.production
        else
            echo "SECRET_KEY=\"$SECRET_KEY\"" >> env.production
        fi
        
        # Обновляем ENCRYPTION_KEY
        if grep -q "^ENCRYPTION_KEY=" env.production; then
            sed -i "s|^ENCRYPTION_KEY=.*|ENCRYPTION_KEY=\"$ENCRYPTION_KEY\"|" env.production
        else
            echo "ENCRYPTION_KEY=\"$ENCRYPTION_KEY\"" >> env.production
        fi
        
        # Обновляем POSTGRES_PASSWORD
        if grep -q "^POSTGRES_PASSWORD=" env.production; then
            sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=\"$POSTGRES_PASSWORD\"|" env.production
            # Также обновляем в DATABASE_URL
            sed -i "s|postgresql://advakod:[^@]*@|postgresql://advakod:$POSTGRES_PASSWORD@|" env.production
        else
            echo "POSTGRES_PASSWORD=\"$POSTGRES_PASSWORD\"" >> env.production
        fi
        
        echo "✅ env.production обновлен"
    else
        echo "❌ Файл env.production не найден"
        echo "   Создайте его из шаблона: cp env.production.template env.production"
    fi
fi

