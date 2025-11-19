# 🚀 Инструкция по развертыванию АДВАКОД с Vistral-24B + Borealis

## 📋 Конфигурация сервера
- **CPU:** 10 ядер × 3.3 ГГц (Dedicated)
- **RAM:** 40 ГБ
- **NVMe:** 200 ГБ
- **IP:** 31.130.145.75
- **Пароль:** pG4Ju#i+i5+UPd

---

## 🎯 Что будет установлено

### Модели:
1. **Vistral-24B-Instruct-GGUF** (~15 GB)
   - Основная модель AI-юриста
   - 24B параметров
   - Русский язык

2. **Borealis** (~1-2 GB)
   - Распознавание речи (Speech-to-Text)
   - Голосовое управление

### Функции:
- ✅ Текстовый чат с AI-юристом
- ✅ Голосовой ввод вопросов
- ✅ RAG система (поиск по юридическим документам)
- ✅ Векторная база данных (Qdrant)
- ✅ Кэширование (Redis)
- ✅ База данных (PostgreSQL)

---

## 📝 Пошаговая инструкция

### Шаг 1: Подключитесь к серверу

```bash
ssh root@31.130.145.75
# Введите пароль: pG4Ju#i+i5+UPd
```

### Шаг 2: Скопируйте скрипты на сервер

**Вариант A: С вашей локальной машины**
```bash
# На вашем компьютере (в папке проекта):
scp 1_setup_server.sh root@31.130.145.75:/root/
scp 2_download_models.sh root@31.130.145.75:/root/
```

**Вариант B: Создайте файлы прямо на сервере**
```bash
# На сервере:
cd /root

# Создайте файл 1_setup_server.sh
nano 1_setup_server.sh
# Вставьте содержимое из файла 1_setup_server.sh
# Ctrl+X, Y, Enter для сохранения

# Создайте файл 2_download_models.sh
nano 2_download_models.sh
# Вставьте содержимое из файла 2_download_models.sh
# Ctrl+X, Y, Enter для сохранения
```

### Шаг 3: Настройте сервер

```bash
cd /root
chmod +x 1_setup_server.sh
bash 1_setup_server.sh
```

**Что делает этот скрипт:**
- ✅ Обновляет систему
- ✅ Устанавливает Docker и Docker Compose
- ✅ Настраивает firewall (порты 22, 80, 443)
- ✅ Настраивает fail2ban (защита SSH)
- ✅ Создает swap (8 GB)
- ✅ Оптимизирует параметры системы
- ✅ Создает директории проекта

**Время выполнения:** 5-10 минут

### Шаг 4: Загрузите модели

```bash
chmod +x 2_download_models.sh
bash 2_download_models.sh
```

**Что делает этот скрипт:**
- ✅ Загружает Vistral-24B-GGUF (~15 GB)
- ✅ Загружает Borealis (~1-2 GB)
- ✅ Проверяет целостность файлов
- ✅ Создает символические ссылки

**Время выполнения:** 15-35 минут (зависит от скорости интернета)

⏱️ **Можете пойти попить кофе** ☕

### Шаг 5: Скопируйте проект на сервер

**На вашей локальной машине:**
```bash
# Упакуйте проект (исключая ненужные файлы)
tar -czf advakod-project.tar.gz \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.pyc' \
    backend/ frontend/ docker-compose.prod.yml nginx.conf

# Скопируйте на сервер
scp advakod-project.tar.gz root@31.130.145.75:/opt/advakod/

# Подключитесь к серверу
ssh root@31.130.145.75
```

**На сервере:**
```bash
cd /opt/advakod
tar -xzf advakod-project.tar.gz
rm advakod-project.tar.gz
```

### Шаг 6: Настройте окружение

```bash
cd /opt/advakod

# Создайте .env файл
cat > .env << 'EOF'
# Основные настройки
PROJECT_NAME="АДВАКОД - ИИ-Юрист для РФ"
VERSION="2.0.0"
ENVIRONMENT=production
DEBUG=false

# База данных PostgreSQL
DATABASE_URL=postgresql://advakod:CHANGE_THIS_PASSWORD@postgres:5432/advakod_db
POSTGRES_USER=advakod
POSTGRES_PASSWORD=CHANGE_THIS_PASSWORD
POSTGRES_DB=advakod_db

# Vistral-24B модель
VISTRAL_MODEL_PATH=/opt/advakod/models/vistral-24b.gguf
VISTRAL_N_CTX=8192
VISTRAL_N_THREADS=10
VISTRAL_MAX_CONCURRENCY=2
VISTRAL_INFERENCE_TIMEOUT=900

# Borealis (Speech-to-Text)
BOREALIS_MODEL_PATH=/opt/advakod/models/borealis/
BOREALIS_ENABLED=true

# Qdrant векторная база
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=legal_documents

# Redis кэширование
REDIS_URL=redis://redis:6379
CACHE_TTL_DEFAULT=3600
CACHE_TTL_AI_RESPONSE=7200

# JWT безопасность
SECRET_KEY=CHANGE_THIS_TO_RANDOM_64_CHARS_STRING_WITH_NUMBERS_AND_LETTERS
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# CORS (замените на ваш домен)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
EOF

# ВАЖНО: Измените пароли и секретные ключи!
nano .env
```

**Обязательно измените:**
1. `POSTGRES_PASSWORD` - сильный пароль для БД
2. `SECRET_KEY` - случайная строка 64+ символов
3. `CORS_ORIGINS` - ваш домен

### Шаг 7: Запустите проект

```bash
cd /opt/advakod

# Запустите все сервисы
docker-compose -f docker-compose.prod.yml up -d

# Следите за логами
docker-compose -f docker-compose.prod.yml logs -f backend
```

**Дождитесь сообщения:**
```
✅ Модель Vistral успешно загружена
✅ Borealis инициализирована
🚀 Server started
```

**Это займет 5-10 минут** (загрузка моделей в память)

### Шаг 8: Проверьте работу

```bash
# Проверьте статус контейнеров
docker-compose -f docker-compose.prod.yml ps

# Проверьте health endpoint
curl http://localhost/api/v1/health

# Проверьте ready endpoint
curl http://localhost/ready

# Тестовый запрос к AI
curl -X POST http://localhost/api/v1/chat/legal \
  -H "Content-Type: application/json" \
  -d '{"question": "Что такое договор?"}'
```

Если все работает - вы увидите ответ от AI! 🎉

---

## 🔧 Полезные команды

### Управление Docker

```bash
# Просмотр логов
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f postgres
docker-compose -f docker-compose.prod.yml logs -f qdrant

# Перезапуск сервисов
docker-compose -f docker-compose.prod.yml restart backend
docker-compose -f docker-compose.prod.yml restart

# Остановка
docker-compose -f docker-compose.prod.yml stop
docker-compose -f docker-compose.prod.yml down

# Обновление
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --build
```

### Мониторинг

```bash
# Использование ресурсов
docker stats

# Память
free -h

# Диск
df -h

# CPU
htop
```

### Резервное копирование

```bash
# Бэкап базы данных
docker exec advakod_postgres pg_dump -U advakod advakod_db > /opt/advakod/backups/db_$(date +%Y%m%d_%H%M%S).sql

# Бэкап конфигурации
tar -czf /opt/advakod/backups/config_$(date +%Y%m%d_%H%M%S).tar.gz /opt/advakod/.env
```

---

## 🐛 Troubleshooting

### Проблема: Модель не загружается

```bash
# Проверьте логи
docker-compose -f docker-compose.prod.yml logs backend | grep -i error

# Проверьте память
free -h

# Проверьте что модель на месте
ls -lh /opt/advakod/models/vistral-24b.gguf
```

### Проблема: Контейнер постоянно перезапускается

```bash
# Увеличьте timeout в docker-compose.prod.yml
# start_period: 600s  # 10 минут

# Перезапустите
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### Проблема: Out of Memory

```bash
# Проверьте swap
swapon --show

# Увеличьте swap до 16 GB
swapoff /swapfile
rm /swapfile
fallocate -l 16G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

---

## 📊 Ожидаемая производительность

### Использование ресурсов:
- **RAM:** 28-35 GB из 40 GB (резерв 5-12 GB)
- **CPU:** 60-80% при генерации
- **Диск:** ~20 GB (модели + данные)

### Скорость:
- **Загрузка моделей:** 5-10 минут
- **Время ответа (текст):** 8-20 секунд
- **Распознавание речи:** 1-3 секунды
- **Параллельность:** 2-3 запроса одновременно

---

## ✅ Чек-лист развертывания

- [ ] Подключились к серверу
- [ ] Запустили 1_setup_server.sh
- [ ] Запустили 2_download_models.sh
- [ ] Скопировали проект на сервер
- [ ] Настроили .env файл
- [ ] Изменили пароли и секретные ключи
- [ ] Запустили docker-compose
- [ ] Дождались загрузки моделей
- [ ] Проверили /api/v1/health
- [ ] Протестировали запрос к AI
- [ ] Настроили SSL (опционально)
- [ ] Настроили домен (опционально)

---

## 🎉 Готово!

Если все шаги выполнены - ваш AI-юрист с голосовым управлением работает!

**Следующие шаги:**
1. Настройте SSL сертификат (Let's Encrypt)
2. Настройте домен
3. Протестируйте с реальными пользователями
4. Настройте мониторинг и алерты

**Нужна помощь?** Проверьте логи: `docker-compose logs -f backend`

---

**Версия:** 1.0.0  
**Дата:** 2024-01-22  
**Сервер:** 10 CPU, 40 GB RAM, 200 GB NVMe