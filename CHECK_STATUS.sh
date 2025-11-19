#!/bin/bash
# 🔍 ДИАГНОСТИЧЕСКИЙ СКРИПТ ДЛЯ ПРОВЕРКИ СТАТУСА АДВАКОД

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

clear
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║        🔍 ДИАГНОСТИКА АДВАКОД - ПРОВЕРКА СТАТУСА        ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# ============================================
# ПРОВЕРКА 1: СИСТЕМНЫЕ РЕСУРСЫ
# ============================================

log_info "🔍 ПРОВЕРКА 1: Системные ресурсы"
echo ""

TOTAL_RAM=$(free -m | awk 'NR==2{print $2}')
CPU_CORES=$(nproc)
DISK_SPACE=$(df / | awk 'NR==2{print $4}')
LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}')

log_info "  CPU: $CPU_CORES ядер"
log_info "  RAM: $TOTAL_RAM MB"
log_info "  Диск: $(($DISK_SPACE / 1024 / 1024)) GB"
log_info "  Нагрузка: $LOAD_AVG"

if [ "$TOTAL_RAM" -lt 30000 ]; then
    log_error "Недостаточно RAM! Нужно минимум 32 GB"
    log_error "Доступно: $TOTAL_RAM MB"
else
    log_success "Ресурсы: OK"
fi

echo ""

# ============================================
# ПРОВЕРКА 2: DOCKER
# ============================================

log_info "🔍 ПРОВЕРКА 2: Docker"
echo ""

if command -v docker &> /dev/null; then
    log_success "Docker установлен"
    
    if systemctl is-active --quiet docker; then
        log_success "Docker сервис запущен"
    else
        log_error "Docker сервис не запущен!"
        log_info "Запускаю Docker..."
        systemctl start docker
        systemctl enable docker
    fi
else
    log_error "Docker не установлен!"
    log_info "Устанавливаю Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
fi

if command -v docker-compose &> /dev/null; then
    log_success "Docker Compose установлен"
else
    log_error "Docker Compose не установлен!"
    log_info "Устанавливаю Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

echo ""

# ============================================
# ПРОВЕРКА 3: ФАЙЛЫ ПРОЕКТА
# ============================================

log_info "🔍 ПРОВЕРКА 3: Файлы проекта"
echo ""

cd /opt/advakod 2>/dev/null || {
    log_error "Директория /opt/advakod не найдена!"
    log_info "Создаю директорию..."
    mkdir -p /opt/advakod
    log_warning "Нужно скопировать файлы проекта:"
    log_warning "scp -r backend frontend docker-compose.prod.yml nginx.conf root@31.130.145.75:/opt/advakod/"
    exit 1
}

log_success "Директория проекта найдена"

# Проверяем основные файлы
FILES=("backend" "frontend" "docker-compose.prod.yml" "nginx.conf" "DEPLOY_ALL_IN_ONE.sh")
MISSING_FILES=()

for file in "${FILES[@]}"; do
    if [ -e "$file" ]; then
        log_success "  $file - найден"
    else
        log_error "  $file - НЕ НАЙДЕН!"
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    log_error "Отсутствуют файлы: ${MISSING_FILES[*]}"
    log_warning "Скопируйте файлы на сервер:"
    log_warning "scp -r backend frontend docker-compose.prod.yml nginx.conf DEPLOY_ALL_IN_ONE.sh root@31.130.145.75:/opt/advakod/"
    exit 1
fi

echo ""

# ============================================
# ПРОВЕРКА 4: DOCKER КОНТЕЙНЕРЫ
# ============================================

log_info "🔍 ПРОВЕРКА 4: Docker контейнеры"
echo ""

if [ -f "docker-compose.prod.yml" ]; then
    log_info "Статус контейнеров:"
    docker-compose -f docker-compose.prod.yml ps
    
    echo ""
    
    # Проверяем каждый контейнер
    CONTAINERS=("advakod_postgres" "advakod_qdrant" "advakod_redis" "advakod_backend" "advakod_frontend" "advakod_nginx")
    
    for container in "${CONTAINERS[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$container"; then
            STATUS=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$container" | awk '{print $2}')
            if [[ "$STATUS" == *"Up"* ]]; then
                log_success "  $container - запущен"
            else
                log_error "  $container - НЕ ЗАПУЩЕН!"
            fi
        else
            log_error "  $container - НЕ НАЙДЕН!"
        fi
    done
else
    log_error "docker-compose.prod.yml не найден!"
fi

echo ""

# ============================================
# ПРОВЕРКА 5: МОДЕЛИ
# ============================================

log_info "🔍 ПРОВЕРКА 5: Модели"
echo ""

MODELS_DIR="/opt/advakod/models"
if [ -d "$MODELS_DIR" ]; then
    log_success "Директория моделей найдена"
    
    # Проверяем Vistral-24B
    if [ -f "$MODELS_DIR/vistral-24b.gguf" ] || [ -f "$MODELS_DIR/vistral-24b-instruct-q4_K_M.gguf" ]; then
        log_success "  Vistral-24B - найдена"
        VISTRAL_FILE=$(find "$MODELS_DIR" -name "*vistral*" -name "*.gguf" -type f | head -n 1)
        if [ -n "$VISTRAL_FILE" ]; then
            FILE_SIZE=$(stat -c%s "$VISTRAL_FILE" 2>/dev/null || echo "0")
            FILE_SIZE_GB=$((FILE_SIZE / 1024 / 1024 / 1024))
            log_info "    Размер: ${FILE_SIZE_GB} GB"
        fi
    else
        log_error "  Vistral-24B - НЕ НАЙДЕНА!"
        log_warning "Запустите: bash 2_download_models_fixed.sh"
    fi
    
    # Проверяем Borealis
    if [ -d "$MODELS_DIR/borealis" ]; then
        log_success "  Borealis - найдена"
    else
        log_warning "  Borealis - не найдена (опционально)"
    fi
else
    log_error "Директория моделей не найдена!"
    log_warning "Создаю директорию..."
    mkdir -p "$MODELS_DIR"
fi

echo ""

# ============================================
# ПРОВЕРКА 6: API
# ============================================

log_info "🔍 ПРОВЕРКА 6: API"
echo ""

# Проверяем локальный API
if curl -s http://localhost/api/v1/health 2>/dev/null | grep -q "healthy"; then
    log_success "API работает локально"
else
    log_error "API НЕ РАБОТАЕТ локально!"
    log_info "Проверяю логи backend..."
    docker-compose -f docker-compose.prod.yml logs --tail=20 backend
fi

# Проверяем внешний доступ
if curl -s http://31.130.145.75/api/v1/health 2>/dev/null | grep -q "healthy"; then
    log_success "API доступен извне"
else
    log_warning "API недоступен извне"
    log_info "Проверьте firewall и nginx"
fi

echo ""

# ============================================
# ПРОВЕРКА 7: NGINX
# ============================================

log_info "🔍 ПРОВЕРКА 7: Nginx"
echo ""

if docker ps --format "table {{.Names}}" | grep -q "advakod_nginx"; then
    log_success "Nginx контейнер запущен"
    
    # Проверяем конфигурацию
    if docker exec advakod_nginx nginx -t 2>/dev/null; then
        log_success "Nginx конфигурация корректна"
    else
        log_error "Nginx конфигурация содержит ошибки!"
    fi
else
    log_error "Nginx контейнер не запущен!"
fi

echo ""

# ============================================
# ПРОВЕРКА 8: ПОРТЫ
# ============================================

log_info "🔍 ПРОВЕРКА 8: Порты"
echo ""

PORTS=("80" "443" "8000" "5432" "6333" "6379")
for port in "${PORTS[@]}"; do
    if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
        log_success "  Порт $port - открыт"
    else
        log_warning "  Порт $port - закрыт"
    fi
done

echo ""

# ============================================
# ИТОГОВАЯ ДИАГНОСТИКА
# ============================================

log_info "🎯 ИТОГОВАЯ ДИАГНОСТИКА"
echo ""

# Подсчитываем проблемы
PROBLEMS=0

# Проверяем основные компоненты
if ! docker ps --format "table {{.Names}}" | grep -q "advakod_backend"; then
    log_error "Backend не запущен!"
    PROBLEMS=$((PROBLEMS + 1))
fi

if ! docker ps --format "table {{.Names}}" | grep -q "advakod_nginx"; then
    log_error "Nginx не запущен!"
    PROBLEMS=$((PROBLEMS + 1))
fi

if [ ! -f "/opt/advakod/models/vistral-24b.gguf" ] && [ ! -f "/opt/advakod/models/vistral-24b-instruct-q4_K_M.gguf" ]; then
    log_error "Модель Vistral-24B не найдена!"
    PROBLEMS=$((PROBLEMS + 1))
fi

if [ $PROBLEMS -eq 0 ]; then
    log_success "🎉 ВСЕ СИСТЕМЫ РАБОТАЮТ!"
    log_info "Сайт должен быть доступен по адресу: http://31.130.145.75"
else
    log_error "❌ ОБНАРУЖЕНО $PROBLEMS ПРОБЛЕМ!"
    log_info "Запустите скрипт исправления: bash QUICK_FIX.sh"
fi

echo ""
log_info "📝 Полезные команды:"
log_info "  Логи: docker-compose -f docker-compose.prod.yml logs -f backend"
log_info "  Статус: docker-compose -f docker-compose.prod.yml ps"
log_info "  Перезапуск: docker-compose -f docker-compose.prod.yml restart"
log_info "  Исправление: bash QUICK_FIX.sh"