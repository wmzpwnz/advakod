#!/bin/bash

# Главный скрипт автоматического резервного копирования АДВАКОД
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
SCRIPT_DIR="/scripts"
BACKUP_DIR="/backups"
LOG_FILE="${BACKUP_DIR}/backup.log"
MAX_LOG_SIZE="10M"

# Функция логирования
log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "${BLUE}${message}${NC}"
    echo "${message}" >> "${LOG_FILE}"
}

error() {
    local message="[ERROR] $1"
    echo -e "${RED}${message}${NC}" >&2
    echo "${message}" >> "${LOG_FILE}"
}

success() {
    local message="[SUCCESS] $1"
    echo -e "${GREEN}${message}${NC}"
    echo "${message}" >> "${LOG_FILE}"
}

warning() {
    local message="[WARNING] $1"
    echo -e "${YELLOW}${message}${NC}"
    echo "${message}" >> "${LOG_FILE}"
}

# Функция очистки логов
cleanup_logs() {
    if [ -f "${LOG_FILE}" ]; then
        local log_size=$(stat -c%s "${LOG_FILE}" 2>/dev/null || echo "0")
        local max_size_bytes=$(echo "${MAX_LOG_SIZE}" | sed 's/M/*1024*1024/' | bc 2>/dev/null || echo "10485760")
        
        if [ "${log_size}" -gt "${max_size_bytes}" ]; then
            log "🧹 Очистка логов (размер: $(numfmt --to=iec "${log_size}"))"
            tail -n 1000 "${LOG_FILE}" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "${LOG_FILE}"
            success "✅ Логи очищены"
        fi
    fi
}

# Функция проверки доступности сервисов
check_services() {
    log "🔍 Проверка доступности сервисов..."
    
    local services_ok=true
    
    # Проверка PostgreSQL
    if docker exec advakod_postgres pg_isready -U advakod -d advakod_db >/dev/null 2>&1; then
        success "✅ PostgreSQL доступен"
    else
        error "❌ PostgreSQL недоступен"
        services_ok=false
    fi
    
    # Проверка Qdrant
    if curl -s http://localhost:6333/health >/dev/null 2>&1; then
        success "✅ Qdrant доступен"
    else
        error "❌ Qdrant недоступен"
        services_ok=false
    fi
    
    # Проверка Redis
    if docker exec advakod_redis redis-cli ping >/dev/null 2>&1; then
        success "✅ Redis доступен"
    else
        warning "⚠️ Redis недоступен (не критично)"
    fi
    
    if [ "${services_ok}" = false ]; then
        error "❌ Не все сервисы доступны. Пропускаем бэкап."
        return 1
    fi
    
    return 0
}

# Функция создания бэкапа PostgreSQL
backup_postgres() {
    log "🔄 Начинаем резервное копирование PostgreSQL..."
    
    if docker run --rm \
        --network advakod_advakod_network \
        -v "${BACKUP_DIR}:/backups" \
        -e POSTGRES_HOST=postgres \
        -e POSTGRES_PORT=5432 \
        -e POSTGRES_DB=advakod_db \
        -e POSTGRES_USER=advakod \
        -e POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
        -e MAX_BACKUPS=30 \
        postgres:15-alpine \
        bash -c "
            apk add --no-cache curl jq bc
            chmod +x /scripts/backup_postgres.sh
            /scripts/backup_postgres.sh
        "; then
        success "✅ PostgreSQL бэкап завершен"
        return 0
    else
        error "❌ Ошибка при создании бэкапа PostgreSQL"
        return 1
    fi
}

# Функция создания бэкапа Qdrant
backup_qdrant() {
    log "🔄 Начинаем резервное копирование Qdrant..."
    
    if docker run --rm \
        --network advakod_advakod_network \
        -v "${BACKUP_DIR}:/backups" \
        -e QDRANT_HOST=qdrant \
        -e QDRANT_PORT=6333 \
        -e MAX_BACKUPS=30 \
        alpine:latest \
        sh -c "
            apk add --no-cache curl jq bc bash
            chmod +x /scripts/backup_qdrant.sh
            /scripts/backup_qdrant.sh
        "; then
        success "✅ Qdrant бэкап завершен"
        return 0
    else
        error "❌ Ошибка при создании бэкапа Qdrant"
        return 1
    fi
}

# Функция создания бэкапа конфигурации
backup_config() {
    log "🔄 Создание бэкапа конфигурации..."
    
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local config_backup="${BACKUP_DIR}/advakod_config_${timestamp}.tar.gz"
    
    if tar -czf "${config_backup}" \
        -C /opt/advakod\
        docker-compose.prod.yml \
        nginx.conf \
        env.production \
        scripts/ \
        2>/dev/null; then
        
        success "✅ Бэкап конфигурации создан: $(basename "${config_backup}")"
        
        # Получение размера файла
        local file_size=$(du -h "${config_backup}" | cut -f1)
        log "📏 Размер бэкапа конфигурации: ${file_size}"
        
        return 0
    else
        error "❌ Ошибка при создании бэкапа конфигурации"
        return 1
    fi
}

# Функция создания сводного отчета
create_summary_report() {
    local report_file="${BACKUP_DIR}/backup_summary_$(date '+%Y%m%d_%H%M%S').txt"
    
    log "📊 Создание сводного отчета..."
    
    {
        echo "=========================================="
        echo "СВОДНЫЙ ОТЧЕТ О РЕЗЕРВНОМ КОПИРОВАНИИ"
        echo "=========================================="
        echo "Дата: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "Система: АДВАКОД - ИИ-Юрист для РФ"
        echo ""
        echo "=== ОБЩАЯ СТАТИСТИКА ==="
        echo "Общий размер бэкапов: $(du -sh "${BACKUP_DIR}" | cut -f1)"
        echo "Количество файлов: $(find "${BACKUP_DIR}" -type f | wc -l)"
        echo ""
        echo "=== POSTGRES БЭКАПЫ ==="
        echo "Количество: $(find "${BACKUP_DIR}" -name "advakod_postgres_*.sql.gz" | wc -l)"
        echo "Размер: $(du -sh "${BACKUP_DIR}"/advakod_postgres_*.sql.gz 2>/dev/null | cut -f1 || echo "0")"
        echo ""
        echo "=== QDRANT БЭКАПЫ ==="
        echo "Количество: $(find "${BACKUP_DIR}" -name "advakod_qdrant_*.json.gz" | wc -l)"
        echo "Размер: $(du -sh "${BACKUP_DIR}"/advakod_qdrant_*.json.gz 2>/dev/null | cut -f1 || echo "0")"
        echo ""
        echo "=== КОНФИГУРАЦИЯ ==="
        echo "Количество: $(find "${BACKUP_DIR}" -name "advakod_config_*.tar.gz" | wc -l)"
        echo "Размер: $(du -sh "${BACKUP_DIR}"/advakod_config_*.tar.gz 2>/dev/null | cut -f1 || echo "0")"
        echo ""
        echo "=== ПОСЛЕДНИЕ БЭКАПЫ ==="
        find "${BACKUP_DIR}" -type f -name "*.gz" -printf '%T@ %p %s\n' | \
        sort -n | tail -10 | while read -r timestamp file size; do
            echo "$(date -d "@${timestamp}" '+%Y-%m-%d %H:%M:%S') - $(basename "${file}") - $(numfmt --to=iec "${size}")"
        done
        echo ""
        echo "=== СТАТУС СИСТЕМЫ ==="
        echo "Диск: $(df -h "${BACKUP_DIR}" | tail -1 | awk '{print $4 " свободно из " $2}')"
        echo "Память: $(free -h | grep Mem | awk '{print $7 " свободно из " $2}')"
        echo ""
        echo "=========================================="
    } > "${report_file}"
    
    success "✅ Сводный отчет создан: $(basename "${report_file}")"
}

# Функция отправки уведомления (заглушка)
send_notification() {
    local status="$1"
    local message="$2"
    
    log "📧 Уведомление: ${status} - ${message}"
    
    # Здесь можно добавить отправку email, Slack, Telegram и т.д.
    # Например:
    # curl -X POST "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK" \
    #      -H "Content-Type: application/json" \
    #      -d "{\"text\":\"АДВАКОД Backup: ${status} - ${message}\"}"
}

# Основная функция
main() {
    local start_time=$(date +%s)
    
    log "🚀 Запуск автоматического резервного копирования АДВАКОД"
    log "====================================================="
    
    # Очистка логов
    cleanup_logs
    
    # Проверка доступности сервисов
    if ! check_services; then
        send_notification "FAILED" "Сервисы недоступны"
        exit 1
    fi
    
    local backup_success=true
    local failed_services=""
    
    # Бэкап PostgreSQL
    if ! backup_postgres; then
        backup_success=false
        failed_services="${failed_services} PostgreSQL"
    fi
    
    # Бэкап Qdrant
    if ! backup_qdrant; then
        backup_success=false
        failed_services="${failed_services} Qdrant"
    fi
    
    # Бэкап конфигурации
    if ! backup_config; then
        backup_success=false
        failed_services="${failed_services} Config"
    fi
    
    # Создание сводного отчета
    create_summary_report
    
    # Подсчет времени выполнения
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local duration_formatted=$(printf '%02d:%02d:%02d' $((duration/3600)) $((duration%3600/60)) $((duration%60)))
    
    if [ "${backup_success}" = true ]; then
        success "🎉 Все бэкапы созданы успешно за ${duration_formatted}"
        send_notification "SUCCESS" "Все бэкапы созданы за ${duration_formatted}"
    else
        error "❌ Ошибки при создании бэкапов:${failed_services}"
        send_notification "PARTIAL" "Ошибки в сервисах:${failed_services}"
        exit 1
    fi
}

# Обработка сигналов
trap 'error "❌ Скрипт прерван пользователем"; exit 130' INT TERM

# Запуск
main "$@"
