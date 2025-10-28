# Настройка аутентификации для GitHub репозитория

## Текущий статус

✅ **Репозиторий настроен**: `https://github.com/wmzpwnz/advakod.git`  
✅ **Код готов к загрузке**: 5 коммитов, тег v2.0.0  
✅ **Конфигурация обновлена**: package.json содержит правильный URL репозитория  

## Необходимые действия для загрузки кода

### Вариант 1: Personal Access Token (Рекомендуется)

1. **Создайте Personal Access Token**:
   - Перейдите в GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Нажмите "Generate new token (classic)"
   - Выберите scopes: `repo` (полный доступ к репозиториям)
   - Скопируйте созданный токен

2. **Загрузите код с токеном**:
   ```bash
   cd /root/advakod
   git push -u origin master
   # При запросе username: wmzpwnz
   # При запросе password: вставьте Personal Access Token
   ```

3. **Загрузите теги**:
   ```bash
   git push origin --tags
   ```

### Вариант 2: SSH ключи

1. **Создайте SSH ключ**:
   ```bash
   ssh-keygen -t ed25519 -C "wmzpwnz@users.noreply.github.com"
   # Нажмите Enter для всех вопросов
   ```

2. **Добавьте ключ в SSH агент**:
   ```bash
   eval "$(ssh-agent -s)"
   ssh-add ~/.ssh/id_ed25519
   ```

3. **Добавьте публичный ключ в GitHub**:
   ```bash
   cat ~/.ssh/id_ed25519.pub
   # Скопируйте вывод и добавьте в GitHub → Settings → SSH and GPG keys
   ```

4. **Измените URL репозитория на SSH**:
   ```bash
   git remote set-url origin git@github.com:wmzpwnz/advakod.git
   git push -u origin master
   git push origin --tags
   ```

### Вариант 3: GitHub CLI

1. **Установите GitHub CLI**:
   ```bash
   # Ubuntu/Debian
   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
   sudo apt update
   sudo apt install gh
   ```

2. **Авторизуйтесь**:
   ```bash
   gh auth login
   # Выберите GitHub.com → HTTPS → Yes → Login with a web browser
   ```

3. **Загрузите код**:
   ```bash
   git push -u origin master
   git push origin --tags
   ```

## Проверка после загрузки

После успешной загрузки проверьте:

1. **Репозиторий на GitHub**: https://github.com/wmzpwnz/advakod
2. **Теги**: Должен быть тег v2.0.0
3. **Файлы**: README.md, package.json, CHANGELOG.md должны быть видны

## Настройка приватного репозитория

После загрузки кода:

1. Перейдите в Settings репозитория
2. Scroll down до "Danger Zone"
3. Нажмите "Change repository visibility"
4. Выберите "Make private"
5. Подтвердите действие

## Команды для ежедневной работы

```bash
# Получение обновлений
git pull origin master

# Создание новой ветки
git checkout -b feature/new-feature

# Коммит и отправка
git add .
git commit -m "feat: Add new feature"
git push origin feature/new-feature

# Управление версиями
./scripts/version_manager.sh patch "Fix bug"
git push origin master
git push origin --tags
```

## Troubleshooting

### Ошибка аутентификации
- Убедитесь, что используете правильный username (wmzpwnz)
- Для HTTPS используйте Personal Access Token вместо пароля
- Для SSH проверьте, что ключ добавлен в GitHub

### Ошибка доступа к репозиторию
- Убедитесь, что репозиторий существует на GitHub
- Проверьте права доступа к приватному репозиторию
- Убедитесь, что токен имеет права `repo`

### Ошибка push
- Убедитесь, что нет конфликтов: `git status`
- Если нужно, сделайте pull: `git pull origin master`
- Попробуйте force push (осторожно!): `git push -f origin master`
