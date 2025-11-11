#!/bin/bash

# Скрипт автоматических бэкапов для АДВАКОД
# Создает бэкапы PostgreSQL и очищает старые
# Автор: АДВАКОД Team
# Версия: 1.0

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Функции логирования
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Настройки
BACKUP_DIR="/opt/advakod/backups"
MAX_BACKUPS=30
DB_NAME="advakod_db"
DB_USER="advakod"
DB_HOST="localhost"
DB_PORT="5432"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="advakod_backup_${DATE}.sql"
LOG_FILE="/var/log/advakod_backup.log"

# Проверка аргументов
if [ $# -ge 1 ]; then
    BACKUP_DIR=$1
fi

if [ $# -ge 2 ]; then
    MAX_BACKUPS=$2
fi

log_info "💾 Создание бэкапа АДВАКОД"
log_info "Директория: $BACKUP_DIR"
log_info "Максимум бэкапов: $MAX_BACKUPS"
log_info "Файл: $BACKUP_FILE"

# Создание директории для бэкапов
mkdir -p "$BACKUP_DIR"
chmod 755 "$BACKUP_DIR"

# Проверка доступности PostgreSQL
log_info "Проверка доступности PostgreSQL..."
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"; then
    log_error "❌ PostgreSQL недоступен"
    log_info "Проверьте:"
    log_info "1. PostgreSQL запущен"
    log_info "2. Параметры подключения корректны"
    log_info "3. Пользователь $DB_USER существует"
    exit 1
fi

log_success "✅ PostgreSQL доступен"

# Создание бэкапа
log_info "Создание бэкапа базы данных..."
if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --verbose --no-password --format=custom --compress=9 \
    --file="$BACKUP_DIR/$BACKUP_FILE"; then
    log_success "✅ Бэкап создан успешно"
else
    log_error "❌ Ошибка создания бэкапа"
    exit 1
fi

# Проверка размера файла
FILE_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
log_info "Размер бэкапа: $FILE_SIZE"

# Проверка целостности бэкапа
log_info "Проверка целостности бэкапа..."
if pg_restore --list "$BACKUP_DIR/$BACKUP_FILE" > /dev/null 2>&1; then
    log_success "✅ Бэкап корректен"
else
    log_error "❌ Бэкап поврежден"
    rm -f "$BACKUP_DIR/$BACKUP_FILE"
    exit 1
fi

# Создание архива
log_info "Создание архива..."
cd "$BACKUP_DIR"
if tar -czf "${BACKUP_FILE}.tar.gz" "$BACKUP_FILE"; then
    log_success "✅ Архив создан"
    rm -f "$BACKUP_FILE"  # Удаляем исходный файл
    BACKUP_FILE="${BACKUP_FILE}.tar.gz"
else
    log_warning "⚠️ Не удалось создать архив"
fi

# Очистка старых бэкапов
log_info "Очистка старых бэкапов..."
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/advakod_backup_*.tar.gz 2>/dev/null | wc -l)

if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
    OLD_BACKUPS=$((BACKUP_COUNT - MAX_BACKUPS))
    log_info "Удаление $OLD_BACKUPS старых бэкапов..."
    
    ls -1t "$BACKUP_DIR"/advakod_backup_*.tar.gz | tail -n "$OLD_BACKUPS" | while read -r file; do
        rm -f "$file"
        log_info "Удален: $(basename "$file")"
    done
    
    log_success "✅ Старые бэкапы удалены"
else
    log_info "Количество бэкапов в пределах лимита ($BACKUP_COUNT/$MAX_BACKUPS)"
fi

# Создание отчета
REPORT_FILE="$BACKUP_DIR/backup_report_${DATE}.txt"
cat > "$REPORT_FILE" << EOF
АДВАКОД - Отчет о бэкапе
========================
Дата: $(date)
Файл: $BACKUP_FILE
Размер: $FILE_SIZE
Количество бэкапов: $(ls -1 "$BACKUP_DIR"/advakod_backup_*.tar.gz 2>/dev/null | wc -l)
Статус: Успешно
EOF

log_success "✅ Отчет создан: $REPORT_FILE"

# Логирование
echo "$(date): Бэкап создан успешно - $BACKUP_FILE ($FILE_SIZE)" >> "$LOG_FILE"

log_success "🎉 Бэкап завершен успешно!"
log_info "Файл: $BACKUP_DIR/$BACKUP_FILE"
log_info "Размер: $FILE_SIZE"
log_info "Всего бэкапов: $(ls -1 "$BACKUP_DIR"/advakod_backup_*.tar.gz 2>/dev/null | wc -l)"

# Информация о восстановлении
echo ""
log_info "Для восстановления используйте:"
log_info "pg_restore -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME $BACKUP_DIR/$BACKUP_FILE"
