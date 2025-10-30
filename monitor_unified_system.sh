#!/bin/bash

# Скрипт мониторинга унифицированной системы кодексов
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
SYSTEM_NAME="unified_codex_system"
LOG_DIR="/root/advakod/unified_codexes/logs"
STATUS_FILE="/root/advakod/unified_codexes/status.json"

# Функция проверки статуса сервиса
check_service_status() {
    log_info "🔍 Проверка статуса сервиса $SYSTEM_NAME..."
    
    if systemctl is-active --quiet $SYSTEM_NAME; then
        log_success "✅ Сервис $SYSTEM_NAME активен"
        
        # Получаем PID
        PID=$(systemctl show -p MainPID --value $SYSTEM_NAME)
        log_info "📊 PID процесса: $PID"
        
        # Получаем использование памяти
        MEMORY=$(ps -o rss= -p $PID 2>/dev/null | awk '{print $1/1024 " MB"}' || echo "N/A")
        log_info "💾 Использование памяти: $MEMORY"
        
        return 0
    else
        log_error "❌ Сервис $SYSTEM_NAME неактивен"
        return 1
    fi
}

# Функция проверки скачанных файлов
check_downloaded_files() {
    log_info "📁 Проверка скачанных файлов..."
    
    CODEXES_DIR="/root/advakod/unified_codexes/codexes"
    
    if [ -d "$CODEXES_DIR" ]; then
        FILE_COUNT=$(find "$CODEXES_DIR" -name "*.pdf" | wc -l)
        TOTAL_SIZE=$(du -sh "$CODEXES_DIR" 2>/dev/null | cut -f1 || echo "0")
        
        log_info "📄 Количество PDF файлов: $FILE_COUNT"
        log_info "💾 Общий размер: $TOTAL_SIZE"
        
        if [ $FILE_COUNT -gt 0 ]; then
            log_success "✅ Файлы кодексов найдены"
            
            # Показываем последние файлы
            log_info "📋 Последние файлы:"
            find "$CODEXES_DIR" -name "*.pdf" -printf "%T@ %p\n" | sort -nr | head -5 | while read timestamp filepath; do
                filename=$(basename "$filepath")
                filedate=$(date -d "@$timestamp" "+%Y-%m-%d %H:%M:%S")
                log_info "  - $filename ($filedate)"
            done
        else
            log_warning "⚠️ PDF файлы не найдены"
        fi
    else
        log_error "❌ Директория кодексов не найдена: $CODEXES_DIR"
    fi
}

# Функция проверки логов
check_logs() {
    log_info "📝 Проверка логов..."
    
    if [ -d "$LOG_DIR" ]; then
        LOG_FILES=$(find "$LOG_DIR" -name "*.log" | wc -l)
        log_info "📄 Количество лог-файлов: $LOG_FILES"
        
        # Показываем последние записи
        LATEST_LOG=$(find "$LOG_DIR" -name "*.log" -printf "%T@ %p\n" | sort -nr | head -1 | cut -d' ' -f2-)
        
        if [ -n "$LATEST_LOG" ] && [ -f "$LATEST_LOG" ]; then
            log_info "📋 Последние записи из $(basename "$LATEST_LOG"):"
            tail -5 "$LATEST_LOG" | while read line; do
                log_info "  $line"
            done
        fi
    else
        log_warning "⚠️ Директория логов не найдена: $LOG_DIR"
    fi
}

# Функция проверки статуса системы
check_system_status() {
    log_info "🔧 Проверка статуса системы..."
    
    if [ -f "$STATUS_FILE" ]; then
        log_info "📊 Статус системы:"
        
        # Показываем основные метрики
        if command -v jq >/dev/null 2>&1; then
            jq -r '.download.total_files, .integration.integrated_files, .integration.total_chunks' "$STATUS_FILE" 2>/dev/null | while read total_files; do
                read integrated_files
                read total_chunks
                log_info "  📄 Всего файлов: $total_files"
                log_info "  🔗 Интегрировано: $integrated_files"
                log_info "  📝 Всего чанков: $total_chunks"
            done
        else
            log_info "  📄 Статус файл найден: $STATUS_FILE"
        fi
    else
        log_warning "⚠️ Файл статуса не найден: $STATUS_FILE"
    fi
}

# Функция проверки производительности
check_performance() {
    log_info "⚡ Проверка производительности..."
    
    # Проверяем использование CPU
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    log_info "🖥️ Использование CPU: ${CPU_USAGE}%"
    
    # Проверяем использование памяти
    MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    log_info "💾 Использование памяти: ${MEMORY_USAGE}%"
    
    # Проверяем место на диске
    DISK_USAGE=$(df -h /root/advakod | tail -1 | awk '{print $5}')
    log_info "💽 Использование диска: $DISK_USAGE"
}

# Функция проверки сетевого подключения
check_network() {
    log_info "🌐 Проверка сетевого подключения..."
    
    if ping -c 1 pravo.gov.ru >/dev/null 2>&1; then
        log_success "✅ Подключение к pravo.gov.ru доступно"
    else
        log_error "❌ Подключение к pravo.gov.ru недоступно"
    fi
}

# Основная функция
main() {
    log_info "🚀 Мониторинг системы кодексов АДВАКОД"
    log_info "========================================"
    
    # Проверяем все компоненты
    check_service_status
    echo ""
    
    check_downloaded_files
    echo ""
    
    check_logs
    echo ""
    
    check_system_status
    echo ""
    
    check_performance
    echo ""
    
    check_network
    echo ""
    
    log_success "🎉 Мониторинг завершен"
}

# Обработка аргументов командной строки
case "${1:-}" in
    "service")
        check_service_status
        ;;
    "files")
        check_downloaded_files
        ;;
    "logs")
        check_logs
        ;;
    "status")
        check_system_status
        ;;
    "performance")
        check_performance
        ;;
    "network")
        check_network
        ;;
    *)
        main
        ;;
esac



