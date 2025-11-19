#!/usr/bin/env python3
"""
Скрипт для валидации миграции от Saiga к Vistral
Проверяет корректность переименования и отсутствие broken imports
"""

import os
import re
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple

# Цвета для вывода
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_success(message: str):
    print(f"{Colors.GREEN}✅ {message}{Colors.ENDC}")

def print_error(message: str):
    print(f"{Colors.RED}❌ {message}{Colors.ENDC}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.ENDC}")

def print_info(message: str):
    print(f"{Colors.BLUE}ℹ️ {message}{Colors.ENDC}")

def find_saiga_references(root_dir: str) -> List[Tuple[str, int, str]]:
    """Находит все упоминания 'saiga' в Python файлах"""
    references = []
    
    for root, dirs, files in os.walk(root_dir):
        # Пропускаем определенные директории
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache', 'node_modules']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            if 'saiga' in line.lower():
                                references.append((file_path, line_num, line.strip()))
                except Exception as e:
                    print_warning(f"Не удалось прочитать файл {file_path}: {e}")
    
    return references

def check_import_errors(root_dir: str) -> List[str]:
    """Проверяет наличие ошибок импорта"""
    errors = []
    
    # Находим все Python файлы
    python_files = []
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache']]
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    # Проверяем каждый файл на синтаксические ошибки
    for file_path in python_files:
        try:
            result = subprocess.run([
                sys.executable, '-m', 'py_compile', file_path
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                errors.append(f"{file_path}: {result.stderr.strip()}")
        except Exception as e:
            errors.append(f"{file_path}: Ошибка проверки - {e}")
    
    return errors

def check_configuration_consistency(config_path: str) -> List[str]:
    """Проверяет консистентность конфигурации"""
    issues = []
    
    if not os.path.exists(config_path):
        issues.append(f"Файл конфигурации не найден: {config_path}")
        return issues
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем наличие VISTRAL параметров
        vistral_params = [
            'VISTRAL_MODEL_PATH',
            'VISTRAL_N_CTX',
            'VISTRAL_N_THREADS',
            'VISTRAL_N_GPU_LAYERS',
            'VISTRAL_INFERENCE_TIMEOUT',
            'VISTRAL_MAX_CONCURRENCY'
        ]
        
        for param in vistral_params:
            if param not in content:
                issues.append(f"Отсутствует параметр конфигурации: {param}")
        
        # Проверяем отсутствие SAIGA параметров (кроме legacy комментариев)
        saiga_params = [
            'SAIGA_MODEL_PATH',
            'SAIGA_N_CTX',
            'SAIGA_N_THREADS'
        ]
        
        for param in saiga_params:
            if f"{param}:" in content and "Legacy" not in content:
                issues.append(f"Найден устаревший параметр конфигурации: {param}")
    
    except Exception as e:
        issues.append(f"Ошибка чтения конфигурации: {e}")
    
    return issues

def check_service_files(services_dir: str) -> Dict[str, List[str]]:
    """Проверяет состояние файлов сервисов"""
    results = {
        "legacy_files": [],
        "new_files": [],
        "missing_files": []
    }
    
    if not os.path.exists(services_dir):
        results["missing_files"].append("Директория services не найдена")
        return results
    
    # Ожидаемые новые файлы
    expected_new_files = [
        "unified_llm_service.py",
        "unified_rag_service.py",
        "service_manager.py",
        "unified_monitoring_service.py"
    ]
    
    # Legacy файлы, которые должны быть помечены как устаревшие
    legacy_files = [
        "saiga_service.py",
        "saiga_service_improved.py",
        "optimized_saiga_service.py",
        "mock_saiga_service.py"
    ]
    
    for file in os.listdir(services_dir):
        if file.endswith('.py'):
            file_path = os.path.join(services_dir, file)
            
            if file in legacy_files:
                results["legacy_files"].append(file)
            elif file in expected_new_files:
                results["new_files"].append(file)
    
    # Проверяем отсутствующие новые файлы
    for expected_file in expected_new_files:
        if expected_file not in results["new_files"]:
            results["missing_files"].append(expected_file)
    
    return results

def validate_api_endpoints(api_dir: str) -> List[str]:
    """Проверяет обновление API endpoints"""
    issues = []
    
    if not os.path.exists(api_dir):
        issues.append("Директория API не найдена")
        return issues
    
    # Файлы, которые должны быть обновлены
    critical_files = [
        "enhanced_chat.py",
        "admin_dashboard.py",
        "monitoring.py",
        "chat.py"
    ]
    
    for file in critical_files:
        file_path = os.path.join(api_dir, file)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Проверяем наличие legacy комментариев
                if 'saiga_service' in content and 'Legacy' not in content:
                    issues.append(f"{file}: Найдены не помеченные legacy импорты")
                
                # Проверяем обновление переменных
                if 'saiga_ready' in content and 'vistral_ready' not in content:
                    issues.append(f"{file}: Переменные не переименованы с saiga на vistral")
                    
            except Exception as e:
                issues.append(f"Ошибка чтения {file}: {e}")
        else:
            issues.append(f"Критический файл не найден: {file}")
    
    return issues

def create_rollback_script(root_dir: str):
    """Создает скрипт для отката изменений"""
    rollback_script = f"""#!/bin/bash
# Скрипт для отката миграции Saiga -> Vistral
# Создан автоматически {os.path.basename(__file__)}

echo "🔄 Начинаем откат миграции..."

# Восстанавливаем git состояние до миграции
if git rev-parse --verify HEAD~1 >/dev/null 2>&1; then
    echo "📦 Восстанавливаем состояние из git..."
    git checkout HEAD~1 -- backend/app/
    echo "✅ Состояние восстановлено"
else
    echo "❌ Не удалось найти предыдущий commit для отката"
    echo "Выполните откат вручную или восстановите из резервной копии"
fi

echo "🎯 Откат завершен"
"""
    
    rollback_path = os.path.join(root_dir, "rollback_migration.sh")
    with open(rollback_path, 'w', encoding='utf-8') as f:
        f.write(rollback_script)
    
    # Делаем скрипт исполняемым
    os.chmod(rollback_path, 0o755)
    print_info(f"Создан скрипт отката: {rollback_path}")

def main():
    """Основная функция валидации"""
    print(f"{Colors.BOLD}🔍 Валидация миграции Saiga -> Vistral{Colors.ENDC}")
    print("=" * 50)
    
    # Определяем корневую директорию проекта
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)  # advakod/
    backend_dir = os.path.join(root_dir, "backend")
    
    if not os.path.exists(backend_dir):
        print_error("Директория backend не найдена")
        sys.exit(1)
    
    total_issues = 0
    
    # 1. Проверяем упоминания 'saiga' в коде
    print_info("1. Проверка упоминаний 'saiga' в коде...")
    saiga_refs = find_saiga_references(backend_dir)
    
    if saiga_refs:
        print_warning(f"Найдено {len(saiga_refs)} упоминаний 'saiga':")
        for file_path, line_num, line in saiga_refs[:10]:  # Показываем первые 10
            rel_path = os.path.relpath(file_path, root_dir)
            print(f"  {rel_path}:{line_num} - {line}")
        
        if len(saiga_refs) > 10:
            print(f"  ... и еще {len(saiga_refs) - 10} упоминаний")
        
        # Проверяем, помечены ли они как legacy
        legacy_marked = sum(1 for _, _, line in saiga_refs if 'Legacy' in line or 'legacy' in line)
        if legacy_marked < len(saiga_refs):
            total_issues += len(saiga_refs) - legacy_marked
            print_warning(f"Не все упоминания помечены как legacy: {legacy_marked}/{len(saiga_refs)}")
    else:
        print_success("Упоминания 'saiga' не найдены")
    
    # 2. Проверяем ошибки импорта
    print_info("2. Проверка синтаксических ошибок...")
    import_errors = check_import_errors(backend_dir)
    
    if import_errors:
        print_error(f"Найдено {len(import_errors)} ошибок импорта:")
        for error in import_errors[:5]:  # Показываем первые 5
            print(f"  {error}")
        if len(import_errors) > 5:
            print(f"  ... и еще {len(import_errors) - 5} ошибок")
        total_issues += len(import_errors)
    else:
        print_success("Синтаксические ошибки не найдены")
    
    # 3. Проверяем конфигурацию
    print_info("3. Проверка конфигурации...")
    config_path = os.path.join(backend_dir, "app", "core", "config.py")
    config_issues = check_configuration_consistency(config_path)
    
    if config_issues:
        print_warning(f"Найдено {len(config_issues)} проблем в конфигурации:")
        for issue in config_issues:
            print(f"  {issue}")
        total_issues += len(config_issues)
    else:
        print_success("Конфигурация корректна")
    
    # 4. Проверяем файлы сервисов
    print_info("4. Проверка файлов сервисов...")
    services_dir = os.path.join(backend_dir, "app", "services")
    service_results = check_service_files(services_dir)
    
    if service_results["missing_files"]:
        print_error(f"Отсутствуют новые файлы сервисов:")
        for file in service_results["missing_files"]:
            print(f"  {file}")
        total_issues += len(service_results["missing_files"])
    
    if service_results["new_files"]:
        print_success(f"Найдены новые файлы сервисов: {', '.join(service_results['new_files'])}")
    
    if service_results["legacy_files"]:
        print_info(f"Legacy файлы: {', '.join(service_results['legacy_files'])}")
    
    # 5. Проверяем API endpoints
    print_info("5. Проверка API endpoints...")
    api_dir = os.path.join(backend_dir, "app", "api")
    api_issues = validate_api_endpoints(api_dir)
    
    if api_issues:
        print_warning(f"Найдено {len(api_issues)} проблем в API:")
        for issue in api_issues:
            print(f"  {issue}")
        total_issues += len(api_issues)
    else:
        print_success("API endpoints обновлены корректно")
    
    # 6. Создаем скрипт отката
    print_info("6. Создание скрипта отката...")
    create_rollback_script(root_dir)
    
    # Итоговый результат
    print("\n" + "=" * 50)
    if total_issues == 0:
        print_success("🎉 Валидация прошла успешно! Миграция выполнена корректно.")
        return 0
    else:
        print_error(f"🚨 Найдено {total_issues} проблем. Требуется исправление.")
        print_info("Используйте rollback_migration.sh для отката при необходимости")
        return 1

if __name__ == "__main__":
    sys.exit(main())