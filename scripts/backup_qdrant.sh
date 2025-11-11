#!/bin/bash

# Скрипт резервного копирования Qdrant для АДВАКОД
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
QDRANT_HOST="${QDRANT_HOST:-qdrant}"
QDRANT_PORT="${QDRANT_PORT:-6333}"
MAX_BACKUPS="${MAX_BACKUPS:-30}"
BACKUP_PREFIX="advakod_qdrant"

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

# Функция проверки подключения к Qdrant
check_qdrant_connection() {
    log "🔍 Проверка подключения к Qdrant..."
    
    if curl -s "http://${QDRANT_HOST}:${QDRANT_PORT}/health" >/dev/null 2>&1; then
        success "✅ Qdrant доступен"
        return 0
    else
        error "❌ Qdrant недоступен"
        return 1
    fi
}

# Функция получения списка коллекций
get_collections() {
    log "📋 Получение списка коллекций..."
    
    local collections_response
    if collections_response=$(curl -s "http://${QDRANT_HOST}:${QDRANT_PORT}/collections"); then
        # Извлекаем имена коллекций из JSON ответа
        echo "${collections_response}" | jq -r '.result.collections[].name' 2>/dev/null || {
            warning "⚠️ Не удалось распарсить список коллекций"
            return 1
        }
    else
        error "❌ Не удалось получить список коллекций"
        return 1
    fi
}

# Функция создания бэкапа коллекции
backup_collection() {
    local collection_name="$1"
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="${BACKUP_DIR}/${BACKUP_PREFIX}_${collection_name}_${timestamp}.json"
    local backup_file_gz="${backup_file}.gz"
    
    log "🔄 Создание бэкапа коллекции: ${collection_name}"
    
    # Получение информации о коллекции
    local collection_info
    if collection_info=$(curl -s "http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${collection_name}"); then
        
        # Получение всех точек коллекции
        local points_response
        if points_response=$(curl -s "http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${collection_name}/points/scroll" \
            -H "Content-Type: application/json" \
            -d '{"limit": 10000, "with_payload": true, "with_vector": true}'); then
            
            # Создание JSON файла с полной информацией
            {
                echo "{"
                echo "  \"collection_name\": \"${collection_name}\","
                echo "  \"backup_timestamp\": \"$(date -Iseconds)\","
                echo "  \"collection_info\": ${collection_info},"
                echo "  \"points\": ${points_response}"
                echo "}"
            } > "${backup_file}"
            
            # Сжатие бэкапа
            if gzip "${backup_file}"; then
                success "✅ Бэкап коллекции ${collection_name} создан: ${backup_file_gz}"
                
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
            error "❌ Не удалось получить точки коллекции ${collection_name}"
            return 1
        fi
        
    else
        error "❌ Не удалось получить информацию о коллекции ${collection_name}"
        return 1
    fi
    
    return 0
}

# Функция создания полного бэкапа Qdrant
backup_qdrant() {
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="${BACKUP_DIR}/${BACKUP_PREFIX}_full_${timestamp}.json"
    local backup_file_gz="${backup_file}.gz"
    
    log "🔄 Начинаем полное резервное копирование Qdrant..."
    log "📁 Файл бэкапа: ${backup_file_gz}"
    
    # Получение списка коллекций
    local collections
    if ! collections=$(get_collections); then
        error "❌ Не удалось получить список коллекций"
        return 1
    fi
    
    if [ -z "${collections}" ]; then
        warning "⚠️ Коллекции не найдены"
        return 0
    fi
    
    # Создание JSON файла с полной информацией
    {
        echo "{"
        echo "  \"backup_timestamp\": \"$(date -Iseconds)\","
        echo "  \"qdrant_host\": \"${QDRANT_HOST}\","
        echo "  \"qdrant_port\": ${QDRANT_PORT},"
        echo "  \"collections\": ["
        
        local first=true
        while IFS= read -r collection; do
            if [ -n "${collection}" ]; then
                if [ "${first}" = true ]; then
                    first=false
                else
                    echo ","
                fi
                
                log "📦 Обработка коллекции: ${collection}"
                
                # Получение информации о коллекции
                local collection_info
                collection_info=$(curl -s "http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${collection}")
                
                # Получение точек коллекции
                local points_response
                points_response=$(curl -s "http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${collection}/points/scroll" \
                    -H "Content-Type: application/json" \
                    -d '{"limit": 10000, "with_payload": true, "with_vector": true}')
                
                echo "    {"
                echo "      \"name\": \"${collection}\","
                echo "      \"info\": ${collection_info},"
                echo "      \"points\": ${points_response}"
                echo "    }"
            fi
        done <<< "${collections}"
        
        echo ""
        echo "  ]"
        echo "}"
    } > "${backup_file}"
    
    # Сжатие бэкапа
    if gzip "${backup_file}"; then
        success "✅ Полный бэкап Qdrant создан: ${backup_file_gz}"
        
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
    
    # Очистка старых бэкапов
    cleanup_old_backups
    
    return 0
}

# Функция очистки старых бэкапов
cleanup_old_backups() {
    log "🧹 Очистка старых бэкапов Qdrant (максимум ${MAX_BACKUPS} файлов)..."
    
    local backup_count=$(find "${BACKUP_DIR}" -name "${BACKUP_PREFIX}_*.json.gz" | wc -l)
    
    if [ "${backup_count}" -gt "${MAX_BACKUPS}" ]; then
        local files_to_delete=$((backup_count - MAX_BACKUPS))
        log "🗑️ Удаляем ${files_to_delete} старых бэкапов..."
        
        find "${BACKUP_DIR}" -name "${BACKUP_PREFIX}_*.json.gz" -type f -exec stat -c '%Y %n' {} \; | \
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

# Функция создания отчета о бэкапе
create_backup_report() {
    local report_file="${BACKUP_DIR}/qdrant_backup_report_$(date '+%Y%m%d').txt"
    
    log "📊 Создание отчета о бэкапах Qdrant..."
    
    {
        echo "=== ОТЧЕТ О РЕЗЕРВНОМ КОПИРОВАНИИ QDRANT ==="
        echo "Дата: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "Система: Qdrant Vector Database"
        echo ""
        echo "=== СТАТИСТИКА БЭКАПОВ ==="
        echo "Общее количество бэкапов: $(find "${BACKUP_DIR}" -name "${BACKUP_PREFIX}_*.json.gz" | wc -l)"
        echo "Общий размер: $(du -sh "${BACKUP_DIR}" | cut -f1)"
        echo ""
        echo "=== ПОСЛЕДНИЕ 5 БЭКАПОВ ==="
        find "${BACKUP_DIR}" -name "${BACKUP_PREFIX}_*.json.gz" -type f -exec stat -c '%Y %n %s' {} \; | \
        sort -n | tail -5 | while read -r timestamp file size; do
            echo "$(date -d "@${timestamp}" '+%Y-%m-%d %H:%M:%S') - $(basename "${file}") - $(numfmt --to=iec "${size}")"
        done
        echo ""
        echo "=== СТАТУС КОЛЛЕКЦИЙ ==="
        if collections=$(get_collections); then
            while IFS= read -r collection; do
                if [ -n "${collection}" ]; then
                    local collection_info
                    collection_info=$(curl -s "http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${collection}" 2>/dev/null || echo '{"error": "unavailable"}')
                    local points_count=$(echo "${collection_info}" | jq -r '.result.points_count // "unknown"' 2>/dev/null || echo "unknown")
                    echo "Коллекция: ${collection} - Точек: ${points_count}"
                fi
            done <<< "${collections}"
        else
            echo "Не удалось получить информацию о коллекциях"
        fi
    } > "${report_file}"
    
    success "✅ Отчет создан: ${report_file}"
}

# Основная функция
main() {
    log "🚀 Запуск резервного копирования АДВАКОД Qdrant"
    log "==============================================="
    
    # Проверка подключения
    if ! check_qdrant_connection; then
        error "❌ Не удалось подключиться к Qdrant. Выход."
        exit 1
    fi
    
    # Создание бэкапа
    if backup_qdrant; then
        success "✅ Резервное копирование Qdrant завершено успешно"
        
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
