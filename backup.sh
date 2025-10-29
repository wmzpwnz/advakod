#!/bin/bash

# Скрипт ручного запуска резервного копирования АДВАКОД
# Автор: АДВАКОД AI Assistant
# Версия: 1.0

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Функция показа справки
show_help() {
    echo "Использование: $0 [ОПЦИИ]"
    echo ""
    echo "ОПЦИИ:"
    echo "  -h, --help          Показать эту справку"
    echo "  -p, --postgres      Создать только бэкап PostgreSQL"
    echo "  -q, --qdrant        Создать только бэкап Qdrant"
    echo "  -c, --config        Создать только бэкап конфигурации"
    echo "  -a, --all           Создать все бэкапы (по умолчанию)"
    echo "  -t, --test          Тестовый режим (без создания файлов)"
    echo "  -f, --force         Принудительный запуск (игнорировать проверки)"
    echo ""
    echo "ПРИМЕРЫ:"
    echo "  $0                  # Создать все бэкапы"
    echo "  $0 --postgres       # Только PostgreSQL"
    echo "  $0 --test           # Тестовый режим"
    echo "  $0 --force          # Принудительный запуск"
}

# Функция проверки зависимостей
check_dependencies() {
    log "🔍 Проверка зависимостей..."
    
    local missing_deps=()
    
    # Проверка Docker
    if ! command -v docker >/dev/null 2>&1; then
        missing_deps+=("docker")
    fi
    
    # Проверка Docker Compose
    if ! command -v docker-compose >/dev/null 2>&1; then
        missing_deps+=("docker-compose")
    fi
    
    # Проверка curl
    if ! command -v curl >/dev/null 2>&1; then
        missing_deps+=("curl")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        error "❌ Отсутствуют зависимости: ${missing_deps[*]}"
        error "Установите их и повторите попытку"
    exit 1
fi

    success "✅ Все зависимости установлены"
}

# Функция проверки статуса контейнеров
check_containers() {
    log "🔍 Проверка статуса контейнеров..."
    
    local containers=("advakod_postgres" "advakod_qdrant" "advakod_redis")
    local all_running=true
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "^${container}$"; then
            success "✅ ${container} запущен"
        else
            error "❌ ${container} не запущен"
            all_running=false
        fi
    done
    
    if [ "${all_running}" = false ]; then
        error "❌ Не все контейнеры запущены"
        warning "💡 Запустите: docker-compose -f docker-compose.prod.yml up -d"
    exit 1
fi
}

# Функция создания бэкапа PostgreSQL
backup_postgres() {
    log "🔄 Создание бэкапа PostgreSQL..."
    
    if [ "${TEST_MODE}" = true ]; then
        log "🧪 Тестовый режим: PostgreSQL бэкап пропущен"
        return 0
    fi
    
    if docker run --rm \
        --network advakod_advakod_network \
        -v "$(pwd)/backups:/backups" \
        -v "$(pwd)/scripts:/scripts:ro" \
        -e POSTGRES_HOST=postgres \
        -e POSTGRES_PORT=5432 \
        -e POSTGRES_DB=advakod_db \
        -e POSTGRES_USER=advakod \
        -e POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
        -e MAX_BACKUPS=30 \
        postgres:15-alpine \
        bash -c "
            apk add --no-cache curl jq bc
            /scripts/backup_postgres.sh
        "; then
        success "✅ PostgreSQL бэкап создан"
        return 0
    else
        error "❌ Ошибка при создании бэкапа PostgreSQL"
        return 1
    fi
}

# Функция создания бэкапа Qdrant
backup_qdrant() {
    log "🔄 Создание бэкапа Qdrant..."
    
    if [ "${TEST_MODE}" = true ]; then
        log "🧪 Тестовый режим: Qdrant бэкап пропущен"
        return 0
    fi
    
    if docker run --rm \
        --network advakod_advakod_network \
        -v "$(pwd)/backups:/backups" \
        -v "$(pwd)/scripts:/scripts:ro" \
        -e QDRANT_HOST=qdrant \
        -e QDRANT_PORT=6333 \
        -e MAX_BACKUPS=30 \
        alpine:latest \
        sh -c "
            apk add --no-cache curl jq bc bash
            /scripts/backup_qdrant.sh
        "; then
        success "✅ Qdrant бэкап создан"
        return 0
    else
        error "❌ Ошибка при создании бэкапа Qdrant"
        return 1
    fi
}

# Функция создания бэкапа конфигурации
backup_config() {
    log "🔄 Создание бэкапа конфигурации..."
    
    if [ "${TEST_MODE}" = true ]; then
        log "🧪 Тестовый режим: Конфигурация бэкап пропущен"
        return 0
    fi
    
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local config_backup="backups/advakod_config_${timestamp}.tar.gz"
    
    if tar -czf "${config_backup}" \
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

# Функция показа статистики
show_statistics() {
    log "📊 Статистика бэкапов:"
    
    local backup_dir="backups"
    if [ -d "${backup_dir}" ]; then
        echo "  📁 Общий размер: $(du -sh "${backup_dir}" | cut -f1)"
        echo "  📄 Количество файлов: $(find "${backup_dir}" -type f | wc -l)"
        echo "  🗄️ PostgreSQL бэкапов: $(find "${backup_dir}" -name "advakod_postgres_*.sql.gz" | wc -l)"
        echo "  🔍 Qdrant бэкапов: $(find "${backup_dir}" -name "advakod_qdrant_*.json.gz" | wc -l)"
        echo "  ⚙️ Конфигураций: $(find "${backup_dir}" -name "advakod_config_*.tar.gz" | wc -l)"
    else
        warning "⚠️ Папка бэкапов не найдена"
    fi
}

# Основная функция
main() {
    local start_time=$(date +%s)
    
    # Параметры по умолчанию
    local backup_postgres_flag=false
    local backup_qdrant_flag=false
    local backup_config_flag=false
    local backup_all_flag=true
    TEST_MODE=false
    FORCE_MODE=false
    
    # Парсинг аргументов
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -p|--postgres)
                backup_postgres_flag=true
                backup_all_flag=false
                shift
                ;;
            -q|--qdrant)
                backup_qdrant_flag=true
                backup_all_flag=false
                shift
                ;;
            -c|--config)
                backup_config_flag=true
                backup_all_flag=false
                shift
                ;;
            -a|--all)
                backup_all_flag=true
                shift
                ;;
            -t|--test)
                TEST_MODE=true
                shift
                ;;
            -f|--force)
                FORCE_MODE=true
                shift
                ;;
            *)
                error "❌ Неизвестный параметр: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    log "🚀 Запуск ручного резервного копирования АДВАКОД"
    log "=============================================="
    
    if [ "${TEST_MODE}" = true ]; then
        warning "🧪 ТЕСТОВЫЙ РЕЖИМ - файлы не будут созданы"
    fi
    
    # Проверки (если не принудительный режим)
    if [ "${FORCE_MODE}" = false ]; then
        check_dependencies
        check_containers
    fi
    
    # Загрузка переменных окружения
    if [ -f "env.production" ]; then
        source env.production
    else
        error "❌ Файл env.production не найден"
        exit 1
    fi
    
    local backup_success=true
    local failed_services=""
    
    # Выполнение бэкапов
    if [ "${backup_all_flag}" = true ] || [ "${backup_postgres_flag}" = true ]; then
        if ! backup_postgres; then
            backup_success=false
            failed_services="${failed_services} PostgreSQL"
        fi
    fi
    
    if [ "${backup_all_flag}" = true ] || [ "${backup_qdrant_flag}" = true ]; then
        if ! backup_qdrant; then
            backup_success=false
            failed_services="${failed_services} Qdrant"
        fi
    fi
    
    if [ "${backup_all_flag}" = true ] || [ "${backup_config_flag}" = true ]; then
        if ! backup_config; then
            backup_success=false
            failed_services="${failed_services} Config"
        fi
    fi
    
    # Подсчет времени выполнения
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local duration_formatted=$(printf '%02d:%02d:%02d' $((duration/3600)) $((duration%3600/60)) $((duration%60)))
    
    # Показ статистики
    show_statistics
    
    if [ "${backup_success}" = true ]; then
        success "🎉 Резервное копирование завершено успешно за ${duration_formatted}"
        if [ "${TEST_MODE}" = true ]; then
            warning "🧪 Тестовый режим - файлы не созданы"
        fi
    else
        error "❌ Ошибки при создании бэкапов:${failed_services}"
        exit 1
    fi
}

# Обработка сигналов
trap 'error "❌ Скрипт прерван пользователем"; exit 130' INT TERM

# Запуск
main "$@"