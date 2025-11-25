#!/bin/bash

# Скрипт для загрузки ADVAKOD на GitHub
# Автор: ADVAKOD Team

set -e

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Проверка SSH ключа
check_ssh_key() {
    if [ ! -f ~/.ssh/id_ed25519.pub ]; then
        error "SSH ключ не найден. Создайте ключ сначала."
        exit 1
    fi
    
    log "SSH ключ найден: ~/.ssh/id_ed25519.pub"
    
    echo ""
    info "=== SSH ПУБЛИЧНЫЙ КЛЮЧ ==="
    cat ~/.ssh/id_ed25519.pub
    echo ""
    info "=== ИНСТРУКЦИИ ==="
    echo "1. Скопируйте ключ выше"
    echo "2. Перейдите в GitHub → Settings → SSH and GPG keys"
    echo "3. Нажмите 'New SSH key'"
    echo "4. Вставьте ключ и сохраните"
    echo "5. Нажмите Enter для продолжения..."
    echo ""
    read -p "Нажмите Enter после добавления ключа в GitHub..."
}

# Проверка подключения к GitHub
test_github_connection() {
    log "Проверка подключения к GitHub..."
    
    if ssh -o ConnectTimeout=10 -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
        log "✅ Подключение к GitHub успешно!"
        return 0
    else
        warn "❌ Не удалось подключиться к GitHub"
        return 1
    fi
}

# Загрузка кода
push_to_github() {
    log "Загрузка кода на GitHub..."
    
    # Проверка статуса
    if ! git diff-index --quiet HEAD --; then
        warn "Обнаружены незафиксированные изменения"
        git status --short
        read -p "Зафиксировать изменения? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git add .
            git commit -m "chore: Auto-commit before push"
        fi
    fi
    
    # Загрузка основной ветки
    log "Загрузка master ветки..."
    if git push -u origin master; then
        log "✅ Master ветка загружена успешно!"
    else
        error "❌ Ошибка загрузки master ветки"
        return 1
    fi
    
    # Загрузка тегов
    log "Загрузка тегов..."
    if git push origin --tags; then
        log "✅ Теги загружены успешно!"
    else
        warn "⚠️ Ошибка загрузки тегов (возможно, теги уже существуют)"
    fi
}

# Основная функция
main() {
    echo ""
    info "🚀 ADVAKOD GitHub Upload Script"
    echo "================================"
    echo ""
    
    # Проверка директории
    if [ ! -f "package.json" ]; then
        error "Запустите скрипт из корневой директории проекта ADVAKOD"
        exit 1
    fi
    
    # Проверка Git репозитория
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        error "Это не Git репозиторий"
        exit 1
    fi
    
    # Проверка удаленного репозитория
    if ! git remote get-url origin > /dev/null 2>&1; then
        error "Удаленный репозиторий не настроен"
        exit 1
    fi
    
    log "Удаленный репозиторий: $(git remote get-url origin)"
    
    # Проверка SSH ключа
    check_ssh_key
    
    # Проверка подключения
    if ! test_github_connection; then
        error "Не удалось подключиться к GitHub. Проверьте SSH ключ."
        exit 1
    fi
    
    # Загрузка кода
    push_to_github
    
    echo ""
    log "🎉 Код успешно загружен на GitHub!"
    echo ""
    info "Репозиторий: https://github.com/wmzpwnz/advakod"
    info "Тег: v2.0.0"
    echo ""
    info "Следующие шаги:"
    echo "1. Перейдите в Settings репозитория"
    echo "2. Сделайте репозиторий приватным"
    echo "3. Настройте защиту веток"
    echo "4. Создайте первый release"
    echo ""
}

# Запуск
main "$@"
