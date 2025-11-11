# 📋 Система резервного копирования АДВАКОД

## 🎯 Обзор

Комплексная система автоматического резервного копирования для юридической ИИ-системы АДВАКОД, включающая:

- **PostgreSQL** - пользовательские данные, чат-история, токены
- **Qdrant** - векторные эмбеддинги юридических документов  
- **Конфигурация** - настройки системы, скрипты, конфиги

## 🚀 Быстрый старт

### Ручной запуск бэкапа
```bash
# Все бэкапы
./backup.sh

# Только PostgreSQL
./backup.sh --postgres

# Только Qdrant
./backup.sh --qdrant

# Только конфигурация
./backup.sh --config

# Тестовый режим
./backup.sh --test
```

### Автоматический бэкап
```bash
# Запуск сервиса автоматического бэкапа
docker-compose -f docker-compose.prod.yml up -d backup
```

## 📁 Структура бэкапов

```
backups/
├── advakod_postgres_YYYYMMDD_HHMMSS.sql.gz    # PostgreSQL бэкапы
├── advakod_qdrant_full_YYYYMMDD_HHMMSS.json.gz # Qdrant бэкапы
├── advakod_config_YYYYMMDD_HHMMSS.tar.gz       # Конфигурация
├── backup_report_YYYYMMDD.txt                  # Отчеты PostgreSQL
├── qdrant_backup_report_YYYYMMDD.txt          # Отчеты Qdrant
└── backup_summary_YYYYMMDD_HHMMSS.txt         # Сводные отчеты
```

## ⚙️ Конфигурация

### Переменные окружения
```bash
# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=advakod_db
POSTGRES_USER=advakod
POSTGRES_PASSWORD=your_password

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Общие настройки
MAX_BACKUPS=30                    # Максимум бэкапов каждого типа
BACKUP_SCHEDULE="0 2 * * *"       # Cron расписание (ежедневно в 2:00)
```

### Docker Compose сервис
```yaml
backup:
  image: alpine:latest
  container_name: advakod_backup
  volumes:
    - ./backups:/backups
    - ./scripts:/scripts:ro
    - /var/run/docker.sock:/var/run/docker.sock:ro
  environment:
    - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    - BACKUP_SCHEDULE=0 2 * * *
  restart: unless-stopped
  networks:
    - advakod_network
```

## 🔧 Скрипты

### Основные скрипты
- `backup.sh` - главный скрипт ручного запуска
- `scripts/backup_postgres.sh` - бэкап PostgreSQL
- `scripts/backup_qdrant.sh` - бэкап Qdrant
- `scripts/backup_all.sh` - полный автоматический бэкап

### Параметры backup.sh
```bash
-h, --help          Показать справку
-p, --postgres      Только PostgreSQL
-q, --qdrant        Только Qdrant  
-c, --config        Только конфигурация
-a, --all           Все бэкапы (по умолчанию)
-t, --test          Тестовый режим
-f, --force         Принудительный запуск
```

## 📊 Мониторинг

### Проверка статуса
```bash
# Статистика бэкапов
./backup.sh --test

# Логи сервиса бэкапа
docker logs advakod_backup

# Размер бэкапов
du -sh backups/
```

### Отчеты
- **backup_report_YYYYMMDD.txt** - детальный отчет PostgreSQL
- **qdrant_backup_report_YYYYMMDD.txt** - отчет Qdrant
- **backup_summary_YYYYMMDD_HHMMSS.txt** - сводный отчет

## 🔄 Восстановление

### PostgreSQL
```bash
# Остановка сервиса
docker-compose -f docker-compose.prod.yml stop backend

# Восстановление из бэкапа
gunzip -c backups/advakod_postgres_YYYYMMDD_HHMMSS.sql.gz | \
docker exec -i advakod_postgres psql -U advakod -d advakod_db

# Перезапуск сервиса
docker-compose -f docker-compose.prod.yml start backend
```

### Qdrant
```bash
# Остановка Qdrant
docker-compose -f docker-compose.prod.yml stop qdrant

# Очистка данных
docker volume rm advakod_qdrant_data

# Восстановление из бэкапа
gunzip -c backups/advakod_qdrant_full_YYYYMMDD_HHMMSS.json.gz | \
python3 restore_qdrant.py

# Перезапуск Qdrant
docker-compose -f docker-compose.prod.yml start qdrant
```

### Конфигурация
```bash
# Извлечение конфигурации
tar -xzf backups/advakod_config_YYYYMMDD_HHMMSS.tar.gz

# Применение изменений
docker-compose -f docker-compose.prod.yml restart
```

## 🛡️ Безопасность

### Рекомендации
1. **Шифрование** - зашифруйте папку backups
2. **Внешнее хранилище** - синхронизируйте с облаком
3. **Тестирование** - регулярно тестируйте восстановление
4. **Мониторинг** - настройте уведомления об ошибках

### Пример шифрования
```bash
# Создание зашифрованного архива
tar -czf - backups/ | gpg --symmetric --cipher-algo AES256 > backups_encrypted.tar.gz.gpg

# Расшифровка
gpg --decrypt backups_encrypted.tar.gz.gpg | tar -xzf -
```

## 🚨 Устранение неполадок

### Частые проблемы

**Ошибка подключения к PostgreSQL**
```bash
# Проверка статуса
docker ps | grep postgres

# Проверка логов
docker logs advakod_postgres

# Перезапуск
docker-compose -f docker-compose.prod.yml restart postgres
```

**Ошибка подключения к Qdrant**
```bash
# Проверка доступности
curl http://localhost:6333/health

# Проверка логов
docker logs advakod_qdrant
```

**Нехватка места на диске**
```bash
# Очистка старых бэкапов
find backups/ -name "*.gz" -mtime +30 -delete

# Проверка места
df -h backups/
```

## 📈 Оптимизация

### Производительность
- **Параллельные бэкапы** - PostgreSQL и Qdrant одновременно
- **Сжатие** - gzip для экономии места
- **Инкрементальные бэкапы** - только изменения (в разработке)

### Мониторинг производительности
```bash
# Время выполнения бэкапа
time ./backup.sh

# Размер бэкапов по времени
ls -lah backups/ | grep -E "\.(sql|json|tar)\.gz$"
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `docker logs advakod_backup`
2. Запустите тестовый режим: `./backup.sh --test`
3. Проверьте статус сервисов: `docker ps`
4. Обратитесь к документации PostgreSQL/Qdrant

---

**Версия:** 1.0  
**Автор:** АДВАКОД AI Assistant  
**Дата:** 2025-10-29
