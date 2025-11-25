#!/bin/bash

# 🚀 ФОНОВОЕ СКАЧИВАНИЕ МОДЕЛЕЙ
# Продолжает работу даже после отключения от сессии

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Директории
# Определяем корень проекта (родительская директория scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
MODEL_DIR="/opt/advakod/models"
SETUP_SCRIPTS_DIR="$SCRIPT_DIR/scripts/setup"

# Создаем директории
mkdir -p "$LOG_DIR"
mkdir -p "$MODEL_DIR"

# Функция для запуска в фоне
run_background_download() {
    local script_name=$1
    local log_file=$2
    local description=$3
    
    log_info "🚀 Запускаем фоновое скачивание: $description"
    
    # Проверяем, не запущен ли уже процесс
    if pgrep -f "$script_name" > /dev/null; then
        log_warning "Процесс $script_name уже запущен!"
        return 1
    fi
    
    # Запускаем в фоне с nohup
    # Если скрипт в setup/, используем SETUP_SCRIPTS_DIR, иначе SCRIPT_DIR
    if [[ "$script_name" == "2_download_models_fixed.sh" ]]; then
        nohup bash "$SETUP_SCRIPTS_DIR/$script_name" > "$log_file" 2>&1 &
    else
    nohup bash "$SCRIPT_DIR/$script_name" > "$log_file" 2>&1 &
    fi
    local pid=$!
    
    log_success "Процесс запущен с PID: $pid"
    log_info "Лог файл: $log_file"
    
    # Сохраняем PID для мониторинга
    echo "$pid" > "$LOG_DIR/${script_name%.sh}.pid"
    
    return 0
}

# Функция для мониторинга процесса
monitor_process() {
    local pid_file=$1
    local process_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            log_success "$process_name работает (PID: $pid)"
            return 0
        else
            log_warning "$process_name завершился (PID: $pid)"
            rm -f "$pid_file"
            return 1
        fi
    else
        log_warning "$process_name не запущен"
        return 1
    fi
}

# Главное меню
show_menu() {
    echo ""
    echo "🚀 ФОНОВОЕ СКАЧИВАНИЕ МОДЕЛЕЙ И КОДЕКСОВ"
    echo "========================================"
    echo ""
    echo "1) 📥 Скачать модели AI (Vistral-24B, Borealis)"
    echo "2) 📚 Скачать кодексы РФ (все кодексы)"
    echo "3) 📊 Показать статус процессов"
    echo "4) 🛑 Остановить все процессы"
    echo "5) 📋 Показать логи"
    echo "6) 🔄 Перезапустить прерванные загрузки"
    echo "0) Выход"
    echo ""
}

# Функция скачивания моделей
download_models() {
    log_info "📥 Начинаем фоновое скачивание моделей AI..."
    
    # Проверяем доступность скрипта
    if [ ! -f "$SETUP_SCRIPTS_DIR/2_download_models_fixed.sh" ]; then
        log_error "Скрипт 2_download_models_fixed.sh не найден в $SETUP_SCRIPTS_DIR!"
        return 1
    fi
    
    # Запускаем скачивание моделей
    run_background_download \
        "2_download_models_fixed.sh" \
        "$LOG_DIR/models_download_$(date +%Y%m%d_%H%M%S).log" \
        "Модели AI (Vistral-24B, Borealis)"
    
    if [ $? -eq 0 ]; then
        log_success "Скачивание моделей запущено в фоне!"
        log_info "Можете отключаться - процесс продолжится"
        log_info "Для проверки статуса используйте опцию 3"
    fi
}

# Функция скачивания кодексов
download_codexes() {
    log_info "📚 Начинаем фоновое скачивание кодексов РФ..."
    
    # Проверяем доступность скрипта
    if [ ! -f "$SCRIPT_DIR/smart_codex_downloader.py" ]; then
        log_error "Скрипт smart_codex_downloader.py не найден!"
        return 1
    fi
    
    # Запускаем скачивание кодексов
    nohup python3 "$SCRIPT_DIR/smart_codex_downloader.py" all > "$LOG_DIR/codexes_download_$(date +%Y%m%d_%H%M%S).log" 2>&1 &
    local pid=$!
    
    log_success "Скачивание кодексов запущено с PID: $pid"
    echo "$pid" > "$LOG_DIR/codexes_download.pid"
    
    log_success "Скачивание кодексов запущено в фоне!"
    log_info "Можете отключаться - процесс продолжится"
}

# Функция показа статуса
show_status() {
    echo ""
    log_info "📊 СТАТУС ФОНОВЫХ ПРОЦЕССОВ"
    echo "=============================="
    
    # Проверяем скачивание моделей
    monitor_process "$LOG_DIR/models_download.pid" "Скачивание моделей"
    
    # Проверяем скачивание кодексов
    monitor_process "$LOG_DIR/codexes_download.pid" "Скачивание кодексов"
    
    echo ""
    log_info "📁 Активные лог файлы:"
    ls -la "$LOG_DIR"/*.log 2>/dev/null | tail -5 || log_warning "Лог файлы не найдены"
}

# Функция остановки процессов
stop_processes() {
    log_info "🛑 Останавливаем все фоновые процессы..."
    
    # Останавливаем скачивание моделей
    if [ -f "$LOG_DIR/models_download.pid" ]; then
        local pid=$(cat "$LOG_DIR/models_download.pid")
        if ps -p "$pid" > /dev/null 2>&1; then
            kill "$pid"
            log_success "Остановлен процесс скачивания моделей (PID: $pid)"
        fi
        rm -f "$LOG_DIR/models_download.pid"
    fi
    
    # Останавливаем скачивание кодексов
    if [ -f "$LOG_DIR/codexes_download.pid" ]; then
        local pid=$(cat "$LOG_DIR/codexes_download.pid")
        if ps -p "$pid" > /dev/null 2>&1; then
            kill "$pid"
            log_success "Остановлен процесс скачивания кодексов (PID: $pid)"
        fi
        rm -f "$LOG_DIR/codexes_download.pid"
    fi
    
    # Останавливаем все процессы с нашими скриптами
    pkill -f "2_download_models_fixed.sh" 2>/dev/null && log_success "Остановлены процессы моделей"
    pkill -f "smart_codex_downloader.py" 2>/dev/null && log_success "Остановлены процессы кодексов"
    
    log_success "Все процессы остановлены!"
}

# Функция показа логов
show_logs() {
    echo ""
    log_info "📋 ПОСЛЕДНИЕ ЛОГИ"
    echo "=================="
    
    # Показываем последние логи
    if [ -d "$LOG_DIR" ]; then
        echo ""
        log_info "📁 Доступные лог файлы:"
        ls -la "$LOG_DIR"/*.log 2>/dev/null | tail -10
        
        echo ""
        read -p "Показать содержимое последнего лога? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            local latest_log=$(ls -t "$LOG_DIR"/*.log 2>/dev/null | head -1)
            if [ -n "$latest_log" ]; then
                echo ""
                log_info "📄 Содержимое: $latest_log"
                echo "=========================================="
                tail -50 "$latest_log"
            fi
        fi
    else
        log_warning "Директория логов не найдена"
    fi
}

# Функция перезапуска прерванных загрузок
restart_downloads() {
    log_info "🔄 Проверяем прерванные загрузки..."
    
    # Проверяем, были ли прерваны загрузки
    local interrupted=false
    
    # Проверяем модели
    if [ ! -f "$MODEL_DIR/vistral-24b.gguf" ] && [ ! -d "$MODEL_DIR/vistral" ]; then
        log_warning "Скачивание моделей было прервано"
        interrupted=true
    fi
    
    # Проверяем кодексы
    if [ ! -d "/opt/advakod/unified_codexes/codexes" ] || [ -z "$(ls -A /opt/advakod/unified_codexes/codexes 2>/dev/null)" ]; then
        log_warning "Скачивание кодексов было прервано"
        interrupted=true
    fi
    
    if [ "$interrupted" = true ]; then
        echo ""
        read -p "Перезапустить прерванные загрузки? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "🔄 Перезапускаем загрузки..."
            download_models
            download_codexes
        fi
    else
        log_success "Все загрузки завершены успешно!"
    fi
}

# Основной цикл
main() {
    while true; do
        show_menu
        read -p "Выберите опцию (0-6): " choice
        
        case $choice in
            1)
                download_models
                ;;
            2)
                download_codexes
                ;;
            3)
                show_status
                ;;
            4)
                stop_processes
                ;;
            5)
                show_logs
                ;;
            6)
                restart_downloads
                ;;
            0)
                log_info "Выход..."
                exit 0
                ;;
            *)
                log_error "Неверный выбор. Попробуйте снова."
                ;;
        esac
        
        echo ""
        read -p "Нажмите Enter для продолжения..."
    done
}

# Проверяем аргументы командной строки
if [ $# -gt 0 ]; then
    case $1 in
        "models")
            download_models
            ;;
        "codexes")
            download_codexes
            ;;
        "status")
            show_status
            ;;
        "stop")
            stop_processes
            ;;
        "logs")
            show_logs
            ;;
        "restart")
            restart_downloads
            ;;
        *)
            echo "Использование: $0 [models|codexes|status|stop|logs|restart]"
            echo "Или запустите без аргументов для интерактивного меню"
            exit 1
            ;;
    esac
else
    main
fi

