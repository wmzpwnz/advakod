#!/bin/bash

echo "🔐 НАСТРОЙКА БЕЗОПАСНОСТИ ДЛЯ ПРОДАКШЕНА"
echo "======================================="

# Создаем .env файл с реальными паролями (НЕ КОММИТИТЬ В GIT!)
echo "📝 Создание .env файла с безопасными паролями..."

# Генерируем криптографически стойкие пароли
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d '\n' | tr -dc 'a-zA-Z0-9!@#$%^&*()_+-=' | head -c 32)
SECRET_KEY=$(openssl rand -base64 64 | tr -d '\n' | tr -dc 'a-zA-Z0-9!@#$%^&*()_+-=' | head -c 64)
ENCRYPTION_KEY=$(openssl rand -base64 32 | tr -d '\n' | tr -dc 'a-zA-Z0-9!@#$%^&*()_+-=' | head -c 32)

# Создаем .env файл
cat > .env << EOF
# ПРОДАКШЕН ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ - НЕ КОММИТИТЬ В GIT!
POSTGRES_PASSWORD="$POSTGRES_PASSWORD"
SECRET_KEY="$SECRET_KEY"
ENCRYPTION_KEY="$ENCRYPTION_KEY"
EOF

echo "✅ Создан .env файл с безопасными паролями"
echo "⚠️  ВАЖНО: Добавьте .env в .gitignore!"

# Создаем .gitignore если его нет
if [ ! -f .gitignore ]; then
    cat > .gitignore << EOF
# Переменные окружения
.env
.env.local
.env.production.local

# Логи
*.log
logs/

# Временные файлы
*.tmp
*.temp

# SSL сертификаты (кроме Let's Encrypt)
ssl/
*.pem
*.key
*.crt

# Бэкапы БД
backups/
*.sql.gz
*.dump
EOF
    echo "✅ Создан .gitignore"
fi

echo ""
echo "🔐 РЕКОМЕНДАЦИИ ДЛЯ ПРОДАКШЕНА:"
echo "1. Используйте Docker Secrets для критичных данных"
echo "2. Настройте CI/CD для автоматического деплоя"
echo "3. Используйте внешние системы управления секретами (HashiCorp Vault, AWS Secrets Manager)"
echo "4. Регулярно ротируйте пароли"
echo "5. Мониторьте доступ к секретам"
echo ""
echo "📋 Для использования Docker Secrets:"
echo "echo '$POSTGRES_PASSWORD' | docker secret create postgres_password -"
echo "echo '$SECRET_KEY' | docker secret create secret_key -"
