# 🚀 Быстрый гайд: Работа с Git в Cursor

## 📋 Через интерфейс Cursor (Source Control)

### 1. Открыть панель Source Control
- Нажмите `Ctrl+Shift+G` (или `Cmd+Shift+G` на Mac)
- Или кликните на иконку ветки в левой панели (🔄)

### 2. Закоммитить изменения
1. В панели Source Control увидите список изменённых файлов
2. Нажмите `+` рядом с файлом, чтобы добавить в staging (или `+` в заголовке "Changes" для всех файлов)
3. Введите сообщение коммита в поле вверху (например: `feat: add new feature`)
4. Нажмите `✓ Commit` (или `Ctrl+Enter`)

### 3. Запушить в GitHub
- Нажмите на кнопку `...` (три точки) в панели Source Control
- Выберите `Push` (или используйте иконку синхронизации внизу)
- Или используйте горячую клавишу: `Ctrl+Shift+P` → введите `Git: Push`

### 4. Создать тег релиза
Через терминал в Cursor (Terminal → New Terminal):
```bash
# Создать тег
git tag -a v1.0.1 -m "Release v1.0.1"

# Запушить тег
git push origin v1.0.1
```

## 🔧 Через терминал Cursor

### Основные команды:

```bash
# Проверить статус
git status

# Добавить все изменения
git add .

# Закоммитить
git commit -m "feat: описание изменений"

# Запушить в GitHub
git push origin main

# Создать и запушить тег
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin v1.0.1
```

### Полезные команды:

```bash
# Посмотреть историю коммитов
git log --oneline -10

# Посмотреть различия
git diff

# Отменить изменения в файле (до staging)
git checkout -- filename

# Посмотреть текущую ветку
git branch
```

## 🏷️ Создание релиза (тег)

### Вариант 1: Через терминал
```bash
# Создать аннотированный тег
git tag -a v1.0.1 -m "Release v1.0.1: описание"

# Запушить тег (запустит CI для сборки образов)
git push origin v1.0.1
```

### Вариант 2: Через GitHub веб-интерфейс
1. Перейдите на https://github.com/wmzpwnz/advakod
2. Releases → Create a new release
3. Выберите тег (например `v1.0.1`) или создайте новый
4. Заполните описание и нажмите "Publish release"

## 📦 Деплой после релиза

После создания тега CI автоматически соберёт Docker образы в GHCR.

Затем на сервере:
```bash
/root/advakod/scripts/deploy_tag.sh v1.0.1 ghcr.io/wmzpwnz/advakod-backend /root/advakod ghcr.io/wmzpwnz/advakod-frontend
```

## ⚠️ Что НЕ коммитить

Следующие файлы автоматически исключены через `.gitignore`:
- `.env` (секреты)
- `logs/`, `*.log`
- `node_modules/`
- `backups/`, `uploads/`, `media/`
- `*.tar.gz`, `*.zip`
- Модели (`models/`, `*.bin`)

## 🆘 Быстрая помощь

- **Отменить последний коммит (до push):** `git reset --soft HEAD~1`
- **Отменить изменения в файле:** `git checkout -- filename`
- **Посмотреть удалённые ветки:** `git branch -r`
- **Переключиться на ветку:** `git checkout branch-name`

---

**Важно:** Всегда проверяйте `git status` перед коммитом!

