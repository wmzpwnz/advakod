#!/bin/bash

# Скрипт быстрого подключения к серверу АДВАКОД
# Автор: Компания "Аврамир"
# Версия: 1.0

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция вывода цветного текста
print_color() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

print_header() {
    echo ""
    print_color "$BLUE" "=================================="
    print_color "$BLUE" "  АДВАКОД - SSH Подключение"
    print_color "$BLUE" "=================================="
    echo ""
}

# Конфигурация серверов
PROD_HOST="31.130.145.75"
PROD_USER="root"
PROD_PASSWORD="pG4Ju#i+i5+UPd"

LEGACY_HOST="89.23.98.167"
DOMAIN_HOST="advacodex.com"

print_header

# Меню выбора сервера
echo "Выберите сервер для подключения:"
echo ""
print_color "$GREEN" "1) Production сервер (31.130.145.75) - ОСНОВНОЙ"
print_color "$YELLOW" "2) Legacy сервер (89.23.98.167)"
print_color "$BLUE" "3) По домену (advacodex.com)"
echo ""
read -p "Введите номер (1-3): " choice

case $choice in
    1)
        HOST=$PROD_HOST
        SERVER_NAME="Production"
        ;;
    2)
        HOST=$LEGACY_HOST
        SERVER_NAME="Legacy"
        ;;
    3)
        HOST=$DOMAIN_HOST
        SERVER_NAME="Domain"
        ;;
    *)
        print_color "$RED" "Неверный выбор!"
        exit 1
        ;;
esac

echo ""
print_color "$YELLOW" "Подключение к серверу $SERVER_NAME ($HOST)..."
echo ""

# Проверка доступности сервера
print_color "$BLUE" "Проверка доступности сервера..."
if ping -c 1 -W 2 $HOST > /dev/null 2>&1; then
    print_color "$GREEN" "✓ Сервер доступен"
else
    print_color "$YELLOW" "⚠ Предупреждение: Сервер не отвечает на ping (может быть заблокирован firewall)"
fi

echo ""
print_color "$BLUE" "Подключение через SSH..."
echo ""

# Проверка наличия sshpass
if command -v sshpass > /dev/null 2>&1; then
    # Подключение с автоматическим вводом пароля
    print_color "$GREEN" "Используется автоматический ввод пароля..."
    sshpass -p "$PROD_PASSWORD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $PROD_USER@$HOST
else
    # Ручной ввод пароля
    print_color "$YELLOW" "Для автоматического ввода пароля установите sshpass:"
    print_color "$YELLOW" "  sudo apt-get install sshpass"
    echo ""
    print_color "$BLUE" "Пароль: $PROD_PASSWORD"
    echo ""
    ssh -o StrictHostKeyChecking=no $PROD_USER@$HOST
fi

echo ""
print_color "$GREEN" "Отключено от сервера."
