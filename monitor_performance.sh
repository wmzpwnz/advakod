#!/bin/bash

# Скрипт мониторинга производительности Vistral 24B
# Автор: АДВАКОД AI Assistant
# Версия: 1.0

echo "🔍 МОНИТОРИНГ ПРОИЗВОДИТЕЛЬНОСТИ VISTRAL 24B"
echo "=============================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция проверки CPU
check_cpu() {
    echo -e "\n${BLUE}📊 CPU ИСПОЛЬЗОВАНИЕ:${NC}"
    echo "Общее количество ядер: $(nproc)"
    echo "Использование CPU:"
    top -bn1 | grep "Cpu(s)" | awk '{print "  " $2 " " $4 " " $6 " " $8 " " $10}'
    
    # Проверка нагрузки на ядра
    echo -e "\n${YELLOW}Нагрузка на ядра:${NC}"
    mpstat 1 1 | tail -1 | awk '{printf "  CPU: %.1f%% idle, %.1f%% iowait\n", $12, $6}'
}

# Функция проверки памяти
check_memory() {
    echo -e "\n${BLUE}💾 ПАМЯТЬ:${NC}"
    free -h | grep -E "Mem|Swap"
    
    # Проверка использования памяти контейнерами
    echo -e "\n${YELLOW}Использование памяти контейнерами:${NC}"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep advakod
}

# Функция проверки контейнеров
check_containers() {
    echo -e "\n${BLUE}🐳 СТАТУС КОНТЕЙНЕРОВ:${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep advakod
}

# Функция проверки логов на ошибки
check_logs() {
    echo -e "\n${BLUE}📋 ПОСЛЕДНИЕ ОШИБКИ В ЛОГАХ:${NC}"
    
    # Проверка логов backend
    echo -e "\n${YELLOW}Backend ошибки:${NC}"
    docker logs advakod_backend --tail 10 2>&1 | grep -i error | tail -5
    
    # Проверка логов nginx
    echo -e "\n${YELLOW}Nginx ошибки:${NC}"
    docker logs advakod_nginx --tail 10 2>&1 | grep -i error | tail -5
}

# Функция проверки производительности API
check_api_performance() {
    echo -e "\n${BLUE}🚀 ПРОИЗВОДИТЕЛЬНОСТЬ API:${NC}"
    
    # Проверка health endpoint
    echo -e "\n${YELLOW}Health check:${NC}"
    curl -s -w "Время ответа: %{time_total}s\nHTTP код: %{http_code}\n" \
         http://localhost:8000/health 2>/dev/null || echo "❌ Backend недоступен"
    
    # Проверка frontend
    echo -e "\n${YELLOW}Frontend доступность:${NC}"
    curl -s -w "Время ответа: %{time_total}s\nHTTP код: %{http_code}\n" \
         http://localhost/ 2>/dev/null || echo "❌ Frontend недоступен"
}

# Функция рекомендаций по оптимизации
show_recommendations() {
    echo -e "\n${GREEN}💡 РЕКОМЕНДАЦИИ ПО ОПТИМИЗАЦИИ:${NC}"
    echo "1. VISTRAL_N_THREADS=8 (оставляет 2 ядра для системы)"
    echo "2. VISTRAL_MAX_CONCURRENCY=2 (максимум 2 параллельных запроса)"
    echo "3. VISTRAL_INFERENCE_TIMEOUT=180 (быстрый отклик)"
    echo "4. Мониторинг CPU каждые 5 минут"
    echo "5. Перезапуск при нагрузке > 90%"
}

# Основная функция
main() {
    check_cpu
    check_memory
    check_containers
    check_logs
    check_api_performance
    show_recommendations
    
    echo -e "\n${GREEN}✅ Мониторинг завершен${NC}"
    echo "Запустите: watch -n 30 ./monitor_performance.sh"
}

# Запуск
main "$@"
