#!/bin/bash

# ADVAKOD Version Management Script
# Автоматическое управление версиями проекта

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка наличия Git
check_git() {
    if ! command -v git &> /dev/null; then
        error "Git не установлен. Установите Git и повторите попытку."
        exit 1
    fi
}

# Получение текущей версии
get_current_version() {
    if [ -f "VERSION" ]; then
        cat VERSION
    else
        echo "0.0.0"
    fi
}

# Обновление версии в файлах
update_version_files() {
    local version=$1
    
    log "Обновление версии до $version..."
    
    # Обновление package.json
    if [ -f "package.json" ]; then
        sed -i "s/\"version\": \".*\"/\"version\": \"$version\"/" package.json
        log "Обновлен package.json"
    fi
    
    # Обновление VERSION файла
    echo "$version" > VERSION
    log "Обновлен VERSION файл"
    
    # Обновление CHANGELOG.md (добавление заголовка новой версии)
    if [ -f "CHANGELOG.md" ]; then
        local today=$(date +%Y-%m-%d)
        sed -i "2i\\n## [$version] - $today" CHANGELOG.md
        log "Обновлен CHANGELOG.md"
    fi
}

# Создание коммита с новой версией
commit_version() {
    local version=$1
    local message=$2
    
    git add package.json VERSION CHANGELOG.md
    git commit -m "chore: Bump version to $version

$message"
    log "Создан коммит для версии $version"
}

# Создание тега
create_tag() {
    local version=$1
    local message=$2
    
    git tag -a "v$version" -m "Release v$version

$message"
    log "Создан тег v$version"
}

# Увеличение версии
bump_version() {
    local current_version=$1
    local bump_type=$2
    
    IFS='.' read -ra VERSION_PARTS <<< "$current_version"
    local major=${VERSION_PARTS[0]}
    local minor=${VERSION_PARTS[1]}
    local patch=${VERSION_PARTS[2]}
    
    case $bump_type in
        "major")
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        "minor")
            minor=$((minor + 1))
            patch=0
            ;;
        "patch")
            patch=$((patch + 1))
            ;;
        *)
            error "Неверный тип версии. Используйте: major, minor, patch"
            exit 1
            ;;
    esac
    
    echo "$major.$minor.$patch"
}

# Основная функция
main() {
    check_git
    
    local current_version=$(get_current_version)
    log "Текущая версия: $current_version"
    
    if [ $# -eq 0 ]; then
        echo "Использование: $0 <bump_type> [message]"
        echo "Типы версий:"
        echo "  major  - Увеличить мажорную версию (1.0.0 -> 2.0.0)"
        echo "  minor  - Увеличить минорную версию (1.0.0 -> 1.1.0)"
        echo "  patch  - Увеличить патч версию (1.0.0 -> 1.0.1)"
        echo "  set     - Установить конкретную версию"
        echo ""
        echo "Примеры:"
        echo "  $0 patch 'Fix critical bug'"
        echo "  $0 minor 'Add new features'"
        echo "  $0 major 'Breaking changes'"
        echo "  $0 set 2.1.0 'Custom version'"
        exit 1
    fi
    
    local bump_type=$1
    local message=${2:-"Version bump"}
    local new_version
    
    if [ "$bump_type" = "set" ]; then
        if [ $# -lt 2 ]; then
            error "Для 'set' необходимо указать версию"
            exit 1
        fi
        new_version=$2
        message=${3:-"Set version to $new_version"}
    else
        new_version=$(bump_version "$current_version" "$bump_type")
    fi
    
    log "Новая версия: $new_version"
    
    # Проверка на незафиксированные изменения
    if ! git diff-index --quiet HEAD --; then
        warn "Обнаружены незафиксированные изменения. Зафиксируйте их перед обновлением версии."
        git status --short
        exit 1
    fi
    
    # Обновление файлов
    update_version_files "$new_version"
    
    # Создание коммита
    commit_version "$new_version" "$message"
    
    # Создание тега
    create_tag "$new_version" "$message"
    
    log "Версия успешно обновлена до $new_version"
    log "Для отправки на удаленный репозиторий выполните:"
    echo "  git push origin master"
    echo "  git push origin v$new_version"
}

# Запуск основной функции
main "$@"
