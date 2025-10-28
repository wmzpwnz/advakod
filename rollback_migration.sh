#!/bin/bash
# Скрипт для отката миграции Saiga -> Vistral
# Создан автоматически validate_migration.py

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
