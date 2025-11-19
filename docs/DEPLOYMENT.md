# 🚀 Руководство по развертыванию АДВАКОД

## Обзор

Это руководство описывает полный процесс развертывания системы АДВАКОД на продакшен сервер с использованием Saiga 13B модели.

## Характеристики сервера

- **IP адрес**: 89.23.98.167
- **CPU**: 8 x 3.3 ГГц
- **RAM**: 16 ГБ
- **Диск**: 160 ГБ NVMe
- **Домен**: advacodex.com

## Быстрый старт

### Автоматическое развертывание

```bash
# Запуск автоматического развертывания
./deploy.sh

# Или с кастомными параметрами
./deploy.sh 89.23.98.167 root "k-^.V1Y-A#KuS6"
```

### Ручное развертывание

Если автоматический скрипт не работает, выполните шаги вручную:

## 1. Подготовка сервера

### Подключение к серверу

```bash
ssh root@89.23.98.167
# Пароль: k-^.V1Y-A#KuS6
```

### Обновление системы

```bash
apt-get update && apt-get upgrade -y
```

### Установка Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh
systemctl enable docker
systemctl start docker
```

### Установка Docker Compose

```bash
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

### Установка дополнительных пакетов

```bash
apt-get install -y curl wget git htop ufw fail2ban sshpass
```

## 2. Настройка проекта

### Создание директорий

```bash
mkdir -p /opt/advakod
mkdir -p /opt/advakod/models
mkdir -p /opt/advakod/backups
mkdir -p /opt/advakod/logs
```

### Копирование файлов

Скопируйте все файлы проекта в `/opt/advakod/`:

- `backend/` - Backend приложение
- `frontend/` - Frontend приложение
- `docker-compose.prod.yml` - Docker Compose конфигурация
- `nginx.conf` - Nginx конфигурация
- `env.production` - Переменные окружения
- `*.sh` - Скрипты развертывания

### Установка прав доступа

```bash
chmod +x /opt/advakod/*.sh
```

## 3. Настройка переменных окружения

### Создание .env файла

```bash
cd /opt/advakod
cp env.production .env
```

### Генерация паролей

```bash
# Генерация SECRET_KEY
SECRET_KEY=$(openssl rand -base64 32)

# Генерация POSTGRES_PASSWORD
POSTGRES_PASSWORD=$(openssl rand -base64 16)

# Генерация ENCRYPTION_KEY
ENCRYPTION_KEY=$(openssl rand -base64 32)
```

### Обновление .env файла

Отредактируйте `.env` файл и замените переменные на сгенерированные значения:

```bash
nano .env
```

## 4. Загрузка модели Saiga 13B

### Автоматическая загрузка

```bash
cd /opt/advakod
./download_saiga_13b.sh
```

### Ручная загрузка

```bash
# Установка huggingface-hub
pip install huggingface-hub

# Создание директории для моделей
mkdir -p /opt/advakod/models

# Загрузка модели
huggingface-cli download IlyaGusev/saiga_mistral_13b_gguf \
  saiga_mistral_13b_q4_K_M.gguf \
  --local-dir /opt/advakod/models
```

## 5. Настройка базы данных

### Запуск PostgreSQL

```bash
cd /opt/advakod
docker-compose -f docker-compose.prod.yml up -d postgres
```

### Ожидание запуска

```bash
# Проверка статуса
docker-compose -f docker-compose.prod.yml ps

# Проверка логов
docker-compose -f docker-compose.prod.yml logs postgres
```

## 6. Запуск всех сервисов

### Полный запуск

```bash
cd /opt/advakod
docker-compose -f docker-compose.prod.yml up -d
```

### Проверка статуса

```bash
docker-compose -f docker-compose.prod.yml ps
```

### Просмотр логов

```bash
# Все сервисы
docker-compose -f docker-compose.prod.yml logs -f

# Конкретный сервис
docker-compose -f docker-compose.prod.yml logs -f backend
```

## 7. Настройка SSL

### Автоматическая настройка

```bash
cd /opt/advakod
./setup_ssl.sh advacodex.com admin@advacodex.com
```

### Ручная настройка

```bash
# Установка Certbot
apt-get install -y certbot python3-certbot-nginx

# Получение сертификата
certbot --nginx -d advacodex.com -d www.advacodex.com \
  --non-interactive --agree-tos --email admin@advacodex.com

# Настройка автообновления
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

## 8. Настройка DNS

### DNS записи

Настройте следующие DNS записи у вашего провайдера:

```
A    advacodex.com           -> 89.23.98.167
A    www.advacodex.com       -> 89.23.98.167
A    api.advacodex.com       -> 89.23.98.167
```

### Проверка DNS

```bash
nslookup advacodex.com
dig advacodex.com
```

## 9. Настройка бэкапов

### Автоматические бэкапы

```bash
cd /opt/advakod
./backup.sh

# Настройка cron для ежедневных бэкапов
echo "0 3 * * * /opt/advakod/backup.sh" | crontab -
```

### Ручные бэкапы

```bash
# Создание бэкапа
docker exec advakod_postgres pg_dump -U advakod advakod_db > backup_$(date +%Y%m%d).sql

# Восстановление из бэкапа
docker exec -i advakod_postgres psql -U advakod advakod_db < backup_20240101.sql
```

## 10. Создание администратора

### Автоматическое создание

```bash
cd /opt/advakod
docker exec advakod_backend python create_admin.py
```

### Ручное создание

```bash
# Подключение к контейнеру
docker exec -it advakod_backend bash

# Создание администратора
python create_admin.py
```

## 11. Проверка развертывания

### Health checks

```bash
# API health check
curl https://advacodex.com/api/v1/health

# SSL проверка
curl -I https://advacodex.com

# Тест модели
curl -X POST https://advacodex.com/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Тест"}'
```

### Мониторинг ресурсов

```bash
# Использование памяти
free -h

# Использование диска
df -h

# Процессы Docker
docker stats

# Логи системы
journalctl -f
```

## 12. Управление сервисами

### Основные команды

```bash
# Остановка всех сервисов
docker-compose -f docker-compose.prod.yml down

# Перезапуск сервисов
docker-compose -f docker-compose.prod.yml restart

# Перезапуск конкретного сервиса
docker-compose -f docker-compose.prod.yml restart backend

# Обновление сервисов
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Логи и отладка

```bash
# Логи всех сервисов
docker-compose -f docker-compose.prod.yml logs -f

# Логи конкретного сервиса
docker-compose -f docker-compose.prod.yml logs -f backend

# Логи Nginx
docker-compose -f docker-compose.prod.yml logs -f nginx

# Логи PostgreSQL
docker-compose -f docker-compose.prod.yml logs -f postgres
```

## 13. Мониторинг и обслуживание

### Мониторинг производительности

```bash
# Использование ресурсов
htop

# Статистика Docker
docker stats

# Использование диска
du -sh /opt/advakod/*
```

### Очистка системы

```bash
# Очистка Docker
docker system prune -a

# Очистка логов
docker-compose -f docker-compose.prod.yml logs --tail=0 -f
```

### Обновление системы

```bash
# Обновление пакетов
apt-get update && apt-get upgrade -y

# Перезапуск сервера
reboot
```

## 14. Безопасность

### Firewall

```bash
# Настройка UFW
ufw enable
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw deny 8000/tcp   # API только через Nginx
```

### Fail2ban

```bash
# Установка и настройка
apt-get install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban
```

### Обновления безопасности

```bash
# Автоматические обновления
apt-get install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
```

## 15. Устранение неполадок

### Проблемы с памятью

```bash
# Проверка использования памяти
free -h
cat /proc/meminfo

# Очистка кэша
sync && echo 3 > /proc/sys/vm/drop_caches
```

### Проблемы с диском

```bash
# Проверка свободного места
df -h

# Очистка логов
docker-compose -f docker-compose.prod.yml logs --tail=0 -f
```

### Проблемы с сетью

```bash
# Проверка портов
netstat -tlnp

# Проверка DNS
nslookup advacodex.com
```

### Проблемы с SSL

```bash
# Проверка сертификата
certbot certificates

# Обновление сертификата
certbot renew --force-renewal
```

## 16. Контакты и поддержка

### Логи и диагностика

```bash
# Сбор диагностической информации
cd /opt/advakod
./collect_diagnostics.sh
```

### Полезные команды

```bash
# Проверка статуса всех сервисов
docker-compose -f docker-compose.prod.yml ps

# Перезапуск с пересборкой
docker-compose -f docker-compose.prod.yml up -d --build

# Просмотр использования ресурсов
docker stats --no-stream
```

---

**АДВАКОД** - Ваш персональный ИИ-правовед 24/7! 🏛️⚖️
