#!/bin/bash
# Скрипт автоматического восстановления проекта ADVAKOD
# Использование: ./scripts/restore.sh

set -e  # Остановка при ошибке

echo "🚀 Начало восстановления проекта ADVAKOD"
echo "=========================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для проверки команды
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1 не установлен${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ $1 установлен${NC}"
}

# Проверка предварительных требований
echo ""
echo "📋 Проверка предварительных требований..."
check_command docker
check_command docker-compose
check_command git

# Проверка наличия env.production
if [ ! -f "env.production" ]; then
    echo -e "${YELLOW}⚠️  Файл env.production не найден${NC}"
    if [ -f "env.production.template" ]; then
        echo "📝 Создание env.production из шаблона..."
        cp env.production.template env.production
        echo -e "${YELLOW}⚠️  ВАЖНО: Отредактируйте env.production и заполните все значения!${NC}"
        echo "   Особенно: SECRET_KEY, ENCRYPTION_KEY, POSTGRES_PASSWORD"
        read -p "Нажмите Enter после заполнения env.production..."
    else
        echo -e "${RED}❌ Шаблон env.production.template не найден${NC}"
        exit 1
    fi
fi

# Проверка наличия модели
echo ""
echo "🤖 Проверка AI модели..."
if [ ! -f "/opt/advakod/models/vistral/Vistral-24B-Instruct-Q5_0.gguf" ]; then
    echo -e "${YELLOW}⚠️  Модель Vistral не найдена${NC}"
    echo "   Путь: /opt/advakod/models/vistral/Vistral-24B-Instruct-Q5_0.gguf"
    read -p "Загрузить модель сейчас? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f "2_download_models.sh" ]; then
            bash 2_download_models.sh
        else
            echo -e "${RED}❌ Скрипт загрузки моделей не найден${NC}"
            echo "   Загрузите модель вручную в /opt/advakod/models/vistral/"
        fi
    fi
else
    echo -e "${GREEN}✅ Модель найдена${NC}"
fi

# Проверка SSL сертификатов
echo ""
echo "🔒 Проверка SSL сертификатов..."
if [ ! -f "/etc/letsencrypt/live/advacodex.com/fullchain.pem" ]; then
    echo -e "${YELLOW}⚠️  SSL сертификаты не найдены${NC}"
    echo "   Получите сертификаты командой:"
    echo "   sudo certbot certonly --standalone -d advacodex.com -d www.advacodex.com"
    read -p "Продолжить без SSL? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ SSL сертификаты найдены${NC}"
fi

# Загрузка переменных окружения
echo ""
echo "📦 Загрузка переменных окружения..."
set -a
source env.production
set +a

# Остановка существующих контейнеров
echo ""
echo "🛑 Остановка существующих контейнеров..."
docker-compose -f docker-compose.prod.yml down || true

# Запуск PostgreSQL
echo ""
echo "🗄️  Запуск PostgreSQL..."
docker-compose -f docker-compose.prod.yml up -d postgres

# Ожидание готовности PostgreSQL
echo "⏳ Ожидание готовности PostgreSQL..."
for i in {1..30}; do
    if docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U advakod -d advakod_db &>/dev/null; then
        echo -e "${GREEN}✅ PostgreSQL готов${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ PostgreSQL не запустился за 30 секунд${NC}"
        exit 1
    fi
    sleep 1
done

# Применение миграций
echo ""
echo "🔄 Применение миграций базы данных..."
if docker-compose -f docker-compose.prod.yml exec -T backend alembic upgrade head 2>/dev/null; then
    echo -e "${GREEN}✅ Миграции применены${NC}"
else
    echo -e "${YELLOW}⚠️  Не удалось применить миграции через backend (возможно еще не запущен)${NC}"
    echo "   Миграции будут применены при первом запуске backend"
fi

# Запуск всех сервисов
echo ""
echo "🚀 Запуск всех сервисов..."
docker-compose -f docker-compose.prod.yml up -d

# Ожидание готовности сервисов
echo "⏳ Ожидание готовности сервисов..."
sleep 10

# Проверка статуса
echo ""
echo "📊 Статус сервисов:"
docker-compose -f docker-compose.prod.yml ps

# Проверка здоровья
echo ""
echo "🏥 Проверка здоровья сервисов..."
sleep 5

if curl -f http://localhost/health &>/dev/null || curl -f https://advacodex.com/health &>/dev/null; then
    echo -e "${GREEN}✅ Сервисы работают${NC}"
else
    echo -e "${YELLOW}⚠️  Не удалось проверить здоровье сервисов${NC}"
    echo "   Проверьте логи: docker-compose -f docker-compose.prod.yml logs"
fi

# Создание администратора
echo ""
echo "👤 Создание администратора..."
read -p "Создать администратора сейчас? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose -f docker-compose.prod.yml exec -T backend python create_admin.py || echo -e "${YELLOW}⚠️  Не удалось создать администратора (возможно уже существует)${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Восстановление завершено!${NC}"
echo ""
echo "📝 Следующие шаги:"
echo "   1. Проверьте логи: docker-compose -f docker-compose.prod.yml logs -f"
echo "   2. Откройте сайт: https://advacodex.com"
echo "   3. Войдите как администратор"
echo ""
echo "📚 Документация: см. RESTORE.md"

