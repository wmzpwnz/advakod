# Настройка удаленного Git репозитория для ADVAKOD

## Шаги для загрузки проекта на GitHub/GitLab

### 1. Создание репозитория на GitHub

1. Перейдите на [GitHub](https://github.com) и войдите в аккаунт
2. Нажмите кнопку "New repository" или "+" → "New repository"
3. Заполните форму:
   - **Repository name**: `advakod`
   - **Description**: `ADVAKOD - ИИ-Юрист для РФ с RAG интеграцией`
   - **Visibility**: Public (рекомендуется для open source)
   - **Initialize**: НЕ ставьте галочки (у нас уже есть код)

### 2. Настройка удаленного репозитория

Выполните следующие команды в терминале:

```bash
cd /root/advakod

# Добавление удаленного репозитория (замените YOUR_USERNAME на ваш GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/advakod.git

# Проверка настроек
git remote -v

# Отправка кода на GitHub
git push -u origin master

# Отправка тегов
git push origin --tags
```

### 3. Альтернатива: Использование SSH

Если у вас настроен SSH ключ:

```bash
# Добавление SSH репозитория
git remote add origin git@github.com:YOUR_USERNAME/advakod.git

# Отправка кода
git push -u origin master
git push origin --tags
```

### 4. Настройка GitHub Actions (опционально)

Создайте файл `.github/workflows/ci.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ master, develop ]
  pull_request:
    branches: [ master ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install dependencies
      run: |
        cd backend && pip install -r requirements.txt
        cd ../frontend && npm install
    
    - name: Run tests
      run: |
        cd backend && python -m pytest
        cd ../frontend && npm test
```

### 5. Настройка защиты веток

1. Перейдите в Settings → Branches
2. Добавьте правило для ветки `master`:
   - Require pull request reviews before merging
   - Require status checks to pass before merging
   - Require branches to be up to date before merging

### 6. Настройка Issues и Projects

1. Включите Issues в настройках репозитория
2. Создайте шаблоны для Issues:
   - Bug Report
   - Feature Request
   - Documentation

### 7. Настройка Releases

1. Перейдите в раздел Releases
2. Создайте новый release для версии v2.0.0:
   - Tag: `v2.0.0`
   - Title: `ADVAKOD v2.0.0 - RAG Integration Release`
   - Description: Скопируйте содержимое из CHANGELOG.md

### 8. Настройка GitHub Pages (опционально)

Для документации:

1. Перейдите в Settings → Pages
2. Source: Deploy from a branch
3. Branch: `gh-pages` (создайте отдельную ветку для документации)

### 9. Команды для ежедневной работы

```bash
# Получение обновлений
git pull origin master

# Создание новой ветки для функции
git checkout -b feature/new-feature

# Коммит изменений
git add .
git commit -m "feat: Add new feature"

# Отправка ветки
git push origin feature/new-feature

# Создание Pull Request через GitHub UI

# После мержа - удаление локальной ветки
git checkout master
git pull origin master
git branch -d feature/new-feature
```

### 10. Управление версиями

Используйте созданный скрипт для управления версиями:

```bash
# Увеличение патч версии (1.0.0 -> 1.0.1)
./scripts/version_manager.sh patch "Fix critical bug"

# Увеличение минор версии (1.0.0 -> 1.1.0)
./scripts/version_manager.sh minor "Add new features"

# Увеличение мажор версии (1.0.0 -> 2.0.0)
./scripts/version_manager.sh major "Breaking changes"

# Установка конкретной версии
./scripts/version_manager.sh set 2.1.0 "Custom version"
```

### 11. Настройка Git Hooks (опционально)

Создайте файл `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Проверка кода перед коммитом

echo "Running pre-commit checks..."

# Проверка Python кода
cd backend
python -m flake8 . --max-line-length=100
if [ $? -ne 0 ]; then
    echo "Python linting failed"
    exit 1
fi

# Проверка JavaScript кода
cd ../frontend
npm run lint
if [ $? -ne 0 ]; then
    echo "JavaScript linting failed"
    exit 1
fi

echo "All checks passed!"
```

### 12. Настройка .gitignore

Убедитесь, что файл `.gitignore` содержит все необходимые исключения (уже настроен).

### 13. Проверка статуса

После настройки проверьте:

```bash
# Статус репозитория
git status

# Информация о удаленном репозитории
git remote -v

# История коммитов
git log --oneline -5

# Список тегов
git tag -l
```

## Полезные ссылки

- [GitHub Documentation](https://docs.github.com/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)

## Поддержка

Если у вас возникли проблемы с настройкой, создайте Issue в репозитории или обратитесь к команде разработки.
