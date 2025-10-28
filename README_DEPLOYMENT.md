# 🚀 АДВАКОД - Развертывание с Vistral-24B + Borealis

## 📊 Конфигурация

**Сервер:**
- IP: 31.130.145.75
- CPU: 10 ядер × 3.3 ГГц
- RAM: 40 ГБ
- NVMe: 200 ГБ

**Модели:**
- Vistral-24B-Instruct-GGUF (~15 GB) - AI-юрист
- Borealis (~1-2 GB) - Распознавание речи

---

## 📁 Созданные файлы

### Скрипты развертывания:
1. **1_setup_server.sh** - Настройка сервера (Docker, firewall, swap)
2. **2_download_models.sh** - Загрузка моделей Vistral + Borealis
3. **download_vistral_and_borealis.sh** - Альтернативный скрипт загрузки

### Документация:
1. **DEPLOY_INSTRUCTIONS.md** - Полная пошаговая инструкция
2. **QUICK_START.md** - Быстрый старт (5 команд)
3. **VISTRAL_MIGRATION_COMPLETE_GUIDE.md** - Детальное руководство по миграции

### Спецификации:
1. **.kiro/specs/vistral-24b-migration/requirements.md** - Требования
2. **.kiro/specs/vistral-24b-migration/design.md** - Проектирование
3. **.kiro/specs/vistral-24b-migration/tasks.md** - План задач

---

## ⚡ Быстрый старт

### Вариант 1: Автоматический (рекомендуется)

```bash
# 1. Подключитесь к серверу
ssh root@31.130.145.75

# 2. Скопируйте скрипты на сервер (с вашей машины)
scp 1_setup_server.sh 2_download_models.sh root@31.130.145.75:/root/

# 3. На сервере выполните:
cd /root
chmod +x *.sh
bash 1_setup_server.sh  # 5-10 минут
bash 2_download_models.sh  # 20-40 минут

# 4. Скопируйте проект
scp -r backend frontend docker-compose.prod.yml nginx.conf root@31.130.145.75:/opt/advakod/

# 5. Запустите
cd /opt/advakod
docker-compose -f docker-compose.prod.yml up -d
```

### Вариант 2: Ручной

Следуйте инструкциям в **DEPLOY_INSTRUCTIONS.md**

---

## 🎯 Что будет работать

### Функции:
✅ Текстовый чат с AI-юристом (Vistral-24B)
✅ Голосовой ввод вопросов (Borealis)
✅ RAG система (поиск по юридическим документам)
✅ Векторная база данных (Qdrant)
✅ Кэширование ответов (Redis)
✅ База данных пользователей (PostgreSQL)
✅ WebSocket для real-time чата
✅ REST API

### Производительность:
- Время ответа: 8-20 секунд
- Распознавание речи: 1-3 секунды
- Параллельность: 2-3 запроса
- Использование RAM: 28-35 GB из 40 GB

---

## 📝 Следующие шаги

После развертывания:

1. **Настройте SSL:**
   ```bash
   apt install certbot python3-certbot-nginx
   certbot --nginx -d yourdomain.com
   ```

2. **Настройте домен:**
   - Добавьте A-запись на IP 31.130.145.75
   - Обновите CORS_ORIGINS в .env

3. **Настройте мониторинг:**
   - Prometheus + Grafana
   - Алерты на использование памяти
   - Логирование ошибок

4. **Протестируйте:**
   - Текстовые запросы
   - Голосовые запросы
   - Нагрузочное тестирование

5. **Соберите обратную связь:**
   - От пользователей
   - Качество ответов
   - Скорость работы

---

## 🔧 Управление

### Просмотр логов:
```bash
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Перезапуск:
```bash
docker-compose -f docker-compose.prod.yml restart backend
```

### Остановка:
```bash
docker-compose -f docker-compose.prod.yml down
```

### Обновление:
```bash
git pull
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 📊 Мониторинг

### Проверка здоровья:
```bash
curl http://localhost/api/v1/health
curl http://localhost/ready
```

### Использование ресурсов:
```bash
free -h          # Память
docker stats     # Docker контейнеры
htop             # CPU
df -h            # Диск
```

---

## 🐛 Troubleshooting

### Модель не загружается:
```bash
# Проверьте логи
docker-compose logs backend | grep -i error

# Проверьте память
free -h

# Проверьте модель
ls -lh /opt/advakod/models/vistral-24b.gguf
```

### Out of Memory:
```bash
# Увеличьте swap
swapoff /swapfile
rm /swapfile
fallocate -l 16G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

### Медленная генерация:
```bash
# Увеличьте VISTRAL_N_THREADS в .env
VISTRAL_N_THREADS=10

# Перезапустите
docker-compose restart backend
```

---

## 📞 Поддержка

**Документация:**
- DEPLOY_INSTRUCTIONS.md - Полная инструкция
- QUICK_START.md - Быстрый старт
- VISTRAL_MIGRATION_COMPLETE_GUIDE.md - Детальное руководство

**Логи:**
```bash
docker-compose logs -f backend
```

**Проверка:**
```bash
curl http://localhost/api/v1/health
```

---

## ✅ Чек-лист

- [ ] Сервер настроен (1_setup_server.sh)
- [ ] Модели загружены (2_download_models.sh)
- [ ] Проект скопирован на сервер
- [ ] .env файл настроен
- [ ] Пароли изменены
- [ ] Docker контейнеры запущены
- [ ] Модели загружены в память
- [ ] /api/v1/health возвращает OK
- [ ] Тестовый запрос работает
- [ ] SSL настроен (опционально)
- [ ] Домен настроен (опционально)

---

## 🎉 Готово!

Ваш AI-юрист с голосовым управлением готов к работе!

**Модели:**
- ✅ Vistral-24B-GGUF - Основная модель
- ✅ Borealis - Распознавание речи

**Сервер:**
- ✅ 10 CPU, 40 GB RAM, 200 GB NVMe
- ✅ Docker + Docker Compose
- ✅ Firewall + Fail2ban
- ✅ Swap 8 GB

**Производительность:**
- ✅ Ответ за 8-20 секунд
- ✅ Распознавание речи за 1-3 секунды
- ✅ 2-3 параллельных запроса

---

**Версия:** 2.0.0  
**Дата:** 2024-01-22  
**Автор:** АДВАКОД Team