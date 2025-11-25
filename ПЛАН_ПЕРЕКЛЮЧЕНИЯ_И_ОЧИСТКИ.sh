#!/bin/bash
# План безопасного переключения на /opt/advakod и очистки старых папок

set -e

OLD_DIR="/root/advakod_backup_20251029_005854"
NEW_DIR="/opt/advakod"
BACKUP_DIR="/root/backups_before_cleanup_$(date +%Y%m%d_%H%M%S)"

echo "=== ПЛАН ПЕРЕКЛЮЧЕНИЯ И ОЧИСТКИ ==="
echo ""
echo "1. Создать бэкап критичных данных"
echo "2. Переключить production на $NEW_DIR"
echo "3. Протестировать работу"
echo "4. Удалить старые папки (после успешного тестирования)"
echo ""

read -p "Продолжить? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Отменено"
    exit 0
fi

# ШАГ 1: Создать бэкап критичных данных
echo ""
echo "ШАГ 1: Создаю бэкап критичных данных в $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"

# Бэкап только критичных файлов (не всей папки)
echo "Бэкап docker-compose.prod.yml..."
cp "$OLD_DIR/docker-compose.prod.yml" "$BACKUP_DIR/" 2>/dev/null || true

echo "Бэкап env файлов..."
cp "$OLD_DIR/.env" "$BACKUP_DIR/" 2>/dev/null || true
cp "$OLD_DIR/env.production" "$BACKUP_DIR/" 2>/dev/null || true

echo "✅ Бэкап создан в $BACKUP_DIR"

# ШАГ 2: Переключение
echo ""
echo "ШАГ 2: Переключаю production на $NEW_DIR..."

cd "$OLD_DIR"
echo "Останавливаю контейнеры в старой папке..."
docker-compose -f docker-compose.prod.yml down

cd "$NEW_DIR"
echo "Запускаю контейнеры в новой папке..."
docker-compose -f docker-compose.prod.yml up -d

# ШАГ 3: Тестирование
echo ""
echo "ШАГ 3: Тестирую работу..."
sleep 15

echo "Проверяю статус контейнеров..."
docker-compose -f docker-compose.prod.yml ps

echo "Проверяю здоровье backend..."
for i in {1..10}; do
    if docker exec advakod_backend curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo "✅ Backend работает!"
        break
    fi
    echo "Ожидание... ($i/10)"
    sleep 5
done

echo "Проверяю сайт..."
if curl -f https://advacodex.com/api/v1/health > /dev/null 2>&1; then
    echo "✅ Сайт работает!"
else
    echo "❌ Сайт не отвечает! Проверьте логи!"
    exit 1
fi

# ШАГ 4: Очистка (только после успешного тестирования)
echo ""
echo "ШАГ 4: Очистка старых папок..."
echo ""
echo "Будет удалено:"
echo "  - $OLD_DIR (17GB)"
echo "  - /root/advakod.old (13GB)"
echo "  - /root/advakod (471MB)"
echo ""
echo "Бэкап сохранен в: $BACKUP_DIR"
echo ""

read -p "Удалить старые папки? (yes/no): " confirm_delete
if [ "$confirm_delete" = "yes" ]; then
    echo "Удаляю старые папки..."
    rm -rf "$OLD_DIR"
    rm -rf /root/advakod.old
    rm -rf /root/advakod
    echo "✅ Старые папки удалены"
    echo ""
    echo "Освобождено места: ~30GB"
else
    echo "Удаление отменено. Старые папки сохранены."
fi

echo ""
echo "✅ Переключение завершено!"
echo "Production теперь работает из: $NEW_DIR"
