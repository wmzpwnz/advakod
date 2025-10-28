# 🔧 САЙТ НЕ ДОСТУПЕН - РЕШЕНИЕ ПРОБЛЕМ

## 🚨 ПРОБЛЕМА
Сайт https://a2codex.com/ не доступен или не работает корректно.

## 🎯 БЫСТРОЕ РЕШЕНИЕ

### Вариант 1: Автоматическое исправление (РЕКОМЕНДУЮ)

```bash
# Подключитесь к серверу
ssh root@31.130.145.75

# Перейдите в директорию проекта
cd /opt/advakod

# Запустите скрипт исправления
bash QUICK_FIX.sh
```

**Скрипт автоматически:**
- ✅ Остановит старые контейнеры
- ✅ Проверит и загрузит модели
- ✅ Создаст .env файл
- ✅ Запустит все сервисы
- ✅ Проверит работоспособность

### Вариант 2: Диагностика проблемы

```bash
# Подключитесь к серверу
ssh root@31.130.145.75

# Перейдите в директорию проекта
cd /opt/advakod

# Запустите диагностику
bash CHECK_STATUS.sh
```

**Диагностика покажет:**
- 🔍 Статус системных ресурсов
- 🔍 Состояние Docker
- 🔍 Наличие файлов проекта
- 🔍 Статус контейнеров
- 🔍 Наличие моделей
- 🔍 Работоспособность API

### Вариант 3: Ручное исправление

```bash
# 1. Остановите все контейнеры
cd /opt/advakod
docker-compose -f docker-compose.prod.yml down

# 2. Запустите заново
docker-compose -f docker-compose.prod.yml up -d

# 3. Проверьте логи
docker-compose -f docker-compose.prod.yml logs -f backend
```

## 🔍 ВОЗМОЖНЫЕ ПРИЧИНЫ

### 1. Проект не скопирован на сервер
**Решение:**
```bash
# Скопируйте файлы с локальной машины
scp -r backend frontend docker-compose.prod.yml nginx.conf root@31.130.145.75:/opt/advakod/
```

### 2. Docker не запущен
**Решение:**
```bash
# Запустите Docker
systemctl start docker
systemctl enable docker

# Запустите проект
cd /opt/advakod
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Модели не загружены
**Решение:**
```bash
# Загрузите модели
cd /opt/advakod
bash 2_download_models_fixed.sh
```

### 4. Проблемы с конфигурацией
**Решение:**
```bash
# Создайте .env файл
cd /opt/advakod
cat > .env << 'EOF'
# Основные настройки
PROJECT_NAME="АДВАКОД - ИИ-Юрист для РФ"
ENVIRONMENT=production
DEBUG=false

# База данных
DATABASE_URL=postgresql://advakod:AdvakodSecurePass2024!@postgres:5432/advakod_db
POSTGRES_PASSWORD=AdvakodSecurePass2024!

# Vistral-24B модель
VISTRAL_MODEL_PATH=/opt/advakod/models/vistral-24b.gguf
VISTRAL_N_CTX=8192
VISTRAL_N_THREADS=8
VISTRAL_MAX_CONCURRENCY=1

# Безопасность
SECRET_KEY=AdvakodSecretKey2024WithNumbers123AndLettersABC456DEF789GHI
EOF
```

### 5. Проблемы с портами
**Решение:**
```bash
# Проверьте открытые порты
netstat -tlnp | grep -E ":(80|443|8000)"

# Откройте порты в firewall
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp
```

## 📋 ПОШАГОВАЯ ИНСТРУКЦИЯ

### Шаг 1: Подключение к серверу
```bash
ssh root@31.130.145.75
```

### Шаг 2: Проверка директории
```bash
cd /opt/advakod
ls -la
```

**Должны быть файлы:**
- `backend/`
- `frontend/`
- `docker-compose.prod.yml`
- `nginx.conf`
- `DEPLOY_ALL_IN_ONE.sh`

### Шаг 3: Запуск исправления
```bash
# Сделайте скрипт исполняемым
chmod +x QUICK_FIX.sh

# Запустите исправление
bash QUICK_FIX.sh
```

### Шаг 4: Проверка результата
```bash
# Проверьте статус контейнеров
docker-compose -f docker-compose.prod.yml ps

# Проверьте API
curl http://localhost/api/v1/health

# Проверьте внешний доступ
curl http://31.130.145.75/api/v1/health
```

## 🔧 ПОЛЕЗНЫЕ КОМАНДЫ

### Проверка статуса
```bash
# Статус контейнеров
docker-compose -f docker-compose.prod.yml ps

# Логи backend
docker-compose -f docker-compose.prod.yml logs -f backend

# Логи nginx
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### Перезапуск сервисов
```bash
# Перезапуск всех сервисов
docker-compose -f docker-compose.prod.yml restart

# Перезапуск только backend
docker-compose -f docker-compose.prod.yml restart backend

# Перезапуск только nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### Проверка ресурсов
```bash
# Использование памяти
free -h

# Использование диска
df -h

# Нагрузка системы
htop
```

## 🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

После исправления сайт должен быть доступен по адресам:
- **Основной сайт:** http://31.130.145.75
- **API:** http://31.130.145.75/api/v1
- **Health check:** http://31.130.145.75/api/v1/health
- **Документация:** http://31.130.145.75/docs

## 🆘 ЕСЛИ НИЧЕГО НЕ ПОМОГАЕТ

1. **Проверьте логи:**
   ```bash
   docker-compose -f docker-compose.prod.yml logs -f
   ```

2. **Перезапустите сервер:**
   ```bash
   reboot
   ```

3. **Обратитесь за помощью:**
   - Проверьте логи на наличие ошибок
   - Убедитесь, что на сервере достаточно ресурсов (32+ GB RAM)
   - Проверьте, что все файлы скопированы корректно

## 📞 ПОДДЕРЖКА

Если проблема не решается:
1. Запустите диагностику: `bash CHECK_STATUS.sh`
2. Сохраните вывод команд
3. Обратитесь за помощью с приложением логов