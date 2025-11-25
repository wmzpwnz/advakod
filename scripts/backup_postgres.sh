#!/bin/bash

# Скрипт резервного копирования PostgreSQL для АДВАКОД
# Автор: АДВАКОД AI Assistant
# Версия: 1.0

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Конфигурация
BACKUP_DIR="/backups"
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-advakod_db}"
POSTGRES_USER="${POSTGRES_USER:-advakod}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD}"
MAX_BACKUPS="${MAX_BACKUPS:-30}"
BACKUP_PREFIX="advakod_postgres"

# Функция логирования
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Функция создания бэкапа PostgreSQL
backup_postgres() {
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="${BACKUP_DIR}/${BACKUP_PREFIX}_${timestamp}.sql"
    local backup_file_gz="${backup_file}.gz"
    
    log "🔄 Начинаем резервное копирование PostgreSQL..."
    log "📊 База данных: ${POSTGRES_DB}"
    log "📁 Файл бэкапа: ${backup_file_gz}"
    
    # Установка переменной окружения для пароля
    export PGPASSWORD="${POSTGRES_PASSWORD}"
    
    # Создание бэкапа
    if pg_dump -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
        --verbose --no-password --format=plain --no-owner --no-privileges \
        --exclude-table-data=pg_stat_statements \
        --exclude-table-data=pg_stat_user_tables \
        --exclude-table-data=pg_stat_user_indexes \
        > "${backup_file}"; then
        
        # Сжатие бэкапа
        if gzip "${backup_file}"; then
            success "✅ PostgreSQL бэкап создан: ${backup_file_gz}"
            
            # Получение размера файла
            local file_size=$(du -h "${backup_file_gz}" | cut -f1)
            log "📏 Размер бэкапа: ${file_size}"
            
            # Проверка целостности
            if gzip -t "${backup_file_gz}"; then
                success "✅ Целостность бэкапа проверена"
            else
                error "❌ Бэкап поврежден!"
                return 1
            fi
            
        else
            error "❌ Ошибка сжатия бэкапа"
            return 1
        fi
        
    else
        error "❌ Ошибка создания бэкапа PostgreSQL"
        return 1
    fi
    
    # Очистка старых бэкапов
    cleanup_old_backups
    
    return 0
}

# Функция очистки старых бэкапов
cleanup_old_backups() {
    log "🧹 Очистка старых бэкапов (максимум ${MAX_BACKUPS} файлов)..."
    
    local backup_count=$(find "${BACKUP_DIR}" -name "${BACKUP_PREFIX}_*.sql.gz" | wc -l)
    
    if [ "${backup_count}" -gt "${MAX_BACKUPS}" ]; then
        local files_to_delete=$((backup_count - MAX_BACKUPS))
        log "🗑️ Удаляем ${files_to_delete} старых бэкапов..."
        
        find "${BACKUP_DIR}" -name "${BACKUP_PREFIX}_*.sql.gz" -type f -exec stat -c '%Y %n' {} \; | \
        sort -n | head -n "${files_to_delete}" | cut -d' ' -f2- | \
        while read -r file; do
            if rm -f "${file}"; then
                log "🗑️ Удален: $(basename "${file}")"
            else
                warning "⚠️ Не удалось удалить: $(basename "${file}")"
            fi
        done
        
        success "✅ Очистка завершена"
    else
        log "ℹ️ Количество бэкапов в норме (${backup_count}/${MAX_BACKUPS})"
    fi
}

# Функция проверки подключения к PostgreSQL
check_postgres_connection() {
    log "🔍 Проверка подключения к PostgreSQL..."
    
    export PGPASSWORD="${POSTGRES_PASSWORD}"
    
    if pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" >/dev/null 2>&1; then
        success "✅ PostgreSQL доступен"
        return 0
    else
        error "❌ PostgreSQL недоступен"
        return 1
    fi
}

# Функция создания отчета о бэкапе
create_backup_report() {
    local report_file="${BACKUP_DIR}/backup_report_$(date '+%Y%m%d').txt"
    
    log "📊 Создание отчета о бэкапах..."
    
    {
        echo "=== ОТЧЕТ О РЕЗЕРВНОМ КОПИРОВАНИИ АДВАКОД ==="
        echo "Дата: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "Система: PostgreSQL"
        echo ""
        echo "=== СТАТИСТИКА БЭКАПОВ ==="
        echo "Общее количество бэкапов: $(find "${BACKUP_DIR}" -name "${BACKUP_PREFIX}_*.sql.gz" | wc -l)"
        echo "Общий размер: $(du -sh "${BACKUP_DIR}" | cut -f1)"
        echo ""
        echo "=== ПОСЛЕДНИЕ 5 БЭКАПОВ ==="
        find "${BACKUP_DIR}" -name "${BACKUP_PREFIX}_*.sql.gz" -type f -exec stat -c '%Y %n %s' {} \; | \
        sort -n | tail -5 | while read -r timestamp file size; do
            echo "$(date -d "@${timestamp}" '+%Y-%m-%d %H:%M:%S') - $(basename "${file}") - $(numfmt --to=iec "${size}")"
        done
        echo ""
        echo "=== СТАТУС БАЗЫ ДАННЫХ ==="
        export PGPASSWORD="${POSTGRES_PASSWORD}"
        psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables 
            WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 10;
        " 2>/dev/null || echo "Не удалось получить статистику БД"
    } > "${report_file}"
    
    success "✅ Отчет создан: ${report_file}"
}

# Основная функция
main() {
    log "🚀 Запуск резервного копирования АДВАКОД PostgreSQL"
    log "=================================================="
    
    # Проверка подключения
    if ! check_postgres_connection; then
        error "❌ Не удалось подключиться к PostgreSQL. Выход."
        exit 1
    fi
    
    # Создание бэкапа
    if backup_postgres; then
        success "✅ Резервное копирование PostgreSQL завершено успешно"
        
        # Создание отчета
        create_backup_report
        
        log "🎉 Все задачи выполнены!"
    else
        error "❌ Ошибка при создании бэкапа"
        exit 1
    fi
}

# Обработка сигналов
trap 'error "❌ Скрипт прерван пользователем"; exit 130' INT TERM

# Запуск
main "$@"
