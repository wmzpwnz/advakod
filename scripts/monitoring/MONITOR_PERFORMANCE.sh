#!/bin/bash

# 📊 МОНИТОРИНГ ПРОИЗВОДИТЕЛЬНОСТИ АДВАКОД
# Отслеживает ключевые метрики производительности

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_metric() {
    echo -e "${CYAN}📊 $1${NC}"
}

# Функция для получения метрик
get_metrics() {
    local url="http://localhost:8000/metrics/json"
    curl -s "$url" 2>/dev/null || echo "{}"
}

# Функция для проверки статуса
check_status() {
    local url="http://localhost:8000/ready"
    curl -s "$url" 2>/dev/null || echo "{}"
}

# Функция для получения статистики Docker
get_docker_stats() {
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" 2>/dev/null || echo "Docker недоступен"
}

echo "📊 МОНИТОРИНГ ПРОИЗВОДИТЕЛЬНОСТИ АДВАКОД"
echo "========================================"
echo ""

# Проверяем доступность API
log_info "Проверяем доступность API..."
if curl -s http://localhost:8000/ready > /dev/null 2>&1; then
    log_success "API доступен"
else
    log_error "API недоступен!"
    exit 1
fi

echo ""

# Получаем статус системы
log_info "Статус системы:"
status=$(check_status)
echo "$status" | jq -r '
    "  Готовность: " + (.ready | tostring) + 
    " | Статус: " + .system_status + 
    " | Сервисы: " + (.services.healthy | tostring) + "/" + (.services.total | tostring) + 
    " | Uptime: " + (.uptime | floor | tostring) + "s"
'

echo ""

# Получаем метрики производительности
log_info "Метрики производительности:"
metrics=$(get_metrics)

# LLM метрики
if echo "$metrics" | jq -e '.unified_services.unified_llm' > /dev/null 2>&1; then
    llm_metrics=$(echo "$metrics" | jq '.unified_services.unified_llm')
    
    log_metric "LLM Сервис:"
    echo "  • Запросов в минуту: $(echo "$llm_metrics" | jq -r '.requests_per_minute')"
    echo "  • Среднее время ответа: $(echo "$llm_metrics" | jq -r '.average_response_time')s"
    echo "  • P95 время ответа: $(echo "$llm_metrics" | jq -r '.p95_response_time')s"
    echo "  • Ошибок: $(echo "$llm_metrics" | jq -r '.error_rate')%"
    echo "  • Очередь: $(echo "$llm_metrics" | jq -r '.queue_length')"
    echo "  • Активных запросов: $(echo "$llm_metrics" | jq -r '.concurrent_requests')"
    echo "  • Использование памяти: $(echo "$llm_metrics" | jq -r '.memory_usage_mb')MB"
    echo "  • Использование CPU: $(echo "$llm_metrics" | jq -r '.cpu_usage_percent')%"
    echo "  • Всего запросов: $(echo "$llm_metrics" | jq -r '.total_requests')"
    echo "  • Успешных: $(echo "$llm_metrics" | jq -r '.successful_requests')"
    echo "  • Неудачных: $(echo "$llm_metrics" | jq -r '.failed_requests')"
else
    log_warning "LLM метрики недоступны"
fi

echo ""

# Статистика Docker контейнеров
log_info "Статистика Docker контейнеров:"
get_docker_stats

echo ""

# Проверяем логи на ошибки
log_info "Последние ошибки в логах:"
recent_errors=$(docker logs advakod_backend --tail 100 2>/dev/null | grep -i "error\|exception\|timeout" | tail -5)
if [ -n "$recent_errors" ]; then
    echo "$recent_errors"
else
    log_success "Ошибок не найдено"
fi

echo ""

# Рекомендации по производительности
log_info "Рекомендации по производительности:"

# Проверяем использование памяти
memory_usage=$(echo "$metrics" | jq -r '.unified_services.unified_llm.memory_usage_mb // 0')
if [ "$memory_usage" -gt 20000 ]; then
    log_warning "Высокое использование памяти: ${memory_usage}MB"
    echo "  • Рассмотрите уменьшение VISTRAL_N_CTX"
fi

# Проверяем время ответа
avg_response_time=$(echo "$metrics" | jq -r '.unified_services.unified_llm.average_response_time // 0')
if (( $(echo "$avg_response_time > 10" | bc -l) )); then
    log_warning "Медленные ответы: ${avg_response_time}s"
    echo "  • Проверьте настройки VISTRAL_N_THREADS"
    echo "  • Уменьшите VISTRAL_N_CTX для ускорения"
fi

# Проверяем очередь
queue_length=$(echo "$metrics" | jq -r '.unified_services.unified_llm.queue_length // 0')
if [ "$queue_length" -gt 3 ]; then
    log_warning "Большая очередь: $queue_length запросов"
    echo "  • Увеличьте VISTRAL_MAX_CONCURRENCY"
fi

# Проверяем ошибки
error_rate=$(echo "$metrics" | jq -r '.unified_services.unified_llm.error_rate // 0')
if (( $(echo "$error_rate > 5" | bc -l) )); then
    log_warning "Высокий процент ошибок: ${error_rate}%"
    echo "  • Проверьте логи на детали ошибок"
fi

echo ""

# Команды для дальнейшего мониторинга
log_info "Команды для мониторинга:"
echo "  • Логи в реальном времени: docker logs advakod_backend -f"
echo "  • Статистика контейнеров: docker stats"
echo "  • Статус системы: curl -s http://localhost:8000/ready | jq"
echo "  • Метрики: curl -s http://localhost:8000/metrics/json | jq"
echo ""

log_success "Мониторинг завершен!"
