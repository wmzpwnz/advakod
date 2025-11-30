#!/bin/bash

# Скрипт для анализа проекта на сервере
# Собирает информацию о проекте и сохраняет локально

SERVER="31.130.145.75"
USER="root"
PASSWORD="pG4Ju#i+i5+UPd"
OUTPUT_DIR="./server_analysis"

echo "Сбор информации о проекте на сервере..."

mkdir -p "$OUTPUT_DIR"

# Функция для выполнения команды на сервере
run_remote() {
    local cmd="$1"
    local output_file="$2"

    if command -v sshpass &> /dev/null; then
        sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no "$USER@$SERVER" "$cmd" > "$OUTPUT_DIR/$output_file" 2>&1
    else
        echo "Выполните на сервере: $cmd" >> "$OUTPUT_DIR/$output_file"
        echo "Скопируйте результат в этот файл" >> "$OUTPUT_DIR/$output_file"
    fi
}

echo "1. Проверка структуры проекта..."
run_remote "ls -la /opt/" "01_opt_structure.txt"
run_remote "ls -la /opt/advakod/ 2>/dev/null || ls -la /opt/a2codex/ 2>/dev/null" "02_project_structure.txt"

echo "2. Проверка Docker контейнеров..."
run_remote "docker ps -a" "03_docker_containers.txt"

echo "3. Проверка Docker Compose..."
run_remote "cd /opt/advakod && docker-compose ps 2>/dev/null || cd /opt/a2codex && docker-compose ps 2>/dev/null" "04_docker_compose.txt"

echo "4. Проверка конфигураций..."
run_remote "cd /opt/advakod && ls -la *.yml *.yaml 2>/dev/null || cd /opt/a2codex && ls -la *.yml *.yaml 2>/dev/null" "05_configs.txt"

echo "5. Проверка Nginx..."
run_remote "nginx -t 2>&1" "06_nginx_test.txt"
run_remote "systemctl status nginx" "07_nginx_status.txt"

echo "6. Проверка процессов..."
run_remote "ps aux | grep -E 'python|node|nginx|docker'" "08_processes.txt"

echo "7. Проверка портов..."
run_remote "netstat -tlnp 2>/dev/null || ss -tlnp" "09_ports.txt"

echo "8. Проверка логов..."
run_remote "cd /opt/advakod && tail -100 logs/*.log 2>/dev/null || cd /opt/a2codex && tail -100 logs/*.log 2>/dev/null" "10_logs.txt"

echo "9. Проверка Git..."
run_remote "cd /opt/advakod && git status && git log --oneline -10 2>/dev/null || cd /opt/a2codex && git status && git log --oneline -10 2>/dev/null" "11_git_status.txt"

echo "10. Проверка системных ресурсов..."
run_remote "free -h && df -h && uptime" "12_system_resources.txt"

echo "11. Проверка backend..."
run_remote "cd /opt/advakod/backend && ls -la 2>/dev/null || cd /opt/a2codex/backend && ls -la 2>/dev/null" "13_backend_structure.txt"

echo "12. Проверка frontend..."
run_remote "cd /opt/advakod/frontend && ls -la 2>/dev/null || cd /opt/a2codex/frontend && ls -la 2>/dev/null" "14_frontend_structure.txt"

echo "13. Проверка переменных окружения..."
run_remote "cd /opt/advakod && ls -la .env* 2>/dev/null || cd /opt/a2codex && ls -la .env* 2>/dev/null" "15_env_files.txt"

echo ""
echo "Информация собрана в директории: $OUTPUT_DIR"
echo ""
echo "Если sshpass не установлен, выполните команды вручную:"
echo "ssh root@$SERVER"
echo "Пароль: $PASSWORD"
