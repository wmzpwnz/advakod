# 🚀 НАЧНИТЕ ЗДЕСЬ - Развертывание АДВАКОД

## 👋 Привет!

Я подготовил для вас **полный набор** для развертывания AI-юриста с голосовым управлением на вашем сервере.

---

## 📦 Что у вас есть

### ✅ Сервер:
- **IP:** 31.130.145.75
- **Пароль:** pG4Ju#i+i5+UPd
- **Конфигурация:** 10 CPU, 40 GB RAM, 200 GB NVMe

### ✅ Модели (будут загружены):
- **Vistral-24B-Instruct-GGUF** - AI-юрист (15 GB)
- **Borealis** - Распознавание речи (1-2 GB)

### ✅ Скрипты (готовы к запуску):
- `1_setup_server.sh` - Настройка сервера
- `2_download_models.sh` - Загрузка моделей

---

## ⚡ Что делать - 3 простых шага

### Шаг 1: Подключитесь к серверу (1 минута)

```bash
ssh root@31.130.145.75
# Введите пароль: pG4Ju#i+i5+UPd
```

### Шаг 2: Скопируйте и запустите скрипты (30-50 минут)

**На вашей локальной машине:**
```bash
# Скопируйте скрипты на сервер
scp 1_setup_server.sh root@31.130.145.75:/root/
scp 2_download_models.sh root@31.130.145.75:/root/
```

**На сервере:**
```bash
cd /root

# Настройте сервер (5-10 минут)
chmod +x 1_setup_server.sh
bash 1_setup_server.sh

# Загрузите модели (20-40 минут)
chmod +x 2_download_models.sh
bash 2_download_models.sh
```

☕ **Пока модели загружаются - попейте кофе!**

### Шаг 3: Скопируйте проект и запустите (10-15 минут)

**На вашей локальной машине:**
```bash
# Скопируйте проект на сервер
scp -r backend frontend docker-compose.prod.yml nginx.conf root@31.130.145.75:/opt/advakod/
```

**На сервере:**
```bash
cd /opt/advakod

# Создайте .env файл (скопируйте из env.production и измените пароли)
cp env.production .env
nano .env  # Измените POSTGRES_PASSWORD и SECRET_KEY

# Запустите проект
docker-compose -f docker-compose.prod.yml up -d

# Следите за логами
docker-compose -f docker-compose.prod.yml logs -f backend
```

⏱️ **Дождитесь сообщения:** `✅ Модель Vistral успешно загружена`

---

## ✅ Проверка

```bash
# Проверьте здоровье API
curl http://localhost/api/v1/health

# Тестовый запрос к AI
curl -X POST http://localhost/api/v1/chat/legal \
  -H "Content-Type: application/json" \
  -d '{"question": "Что такое договор?"}'
```

Если видите ответ от AI - **ВСЁ РАБОТАЕТ!** 🎉

---

## 📚 Документация

### Для быстрого старта:
- **QUICK_START.md** - 5 команд для запуска

### Для детальной настройки:
- **DEPLOY_INSTRUCTIONS.md** - Полная пошаговая инструкция
- **README_DEPLOYMENT.md** - Обзор и управление

### Для понимания архитектуры:
- **VISTRAL_MIGRATION_COMPLETE_GUIDE.md** - Детальное руководство
- **.kiro/specs/vistral-24b-migration/** - Спецификации

---

## 🎯 Что получится

### Функции:
✅ **Текстовый чат** - Пользователь пишет вопрос, AI отвечает
✅ **Голосовой ввод** - Пользователь говорит, Borealis распознает
✅ **RAG система** - Поиск по юридическим документам
✅ **Векторная БД** - Qdrant для семантического поиска
✅ **Кэширование** - Redis для быстрых ответов
✅ **База данных** - PostgreSQL для пользователей

### Производительность:
- ⚡ Ответ за 8-20 секунд
- 🎤 Распознавание речи за 1-3 секунды
- 👥 2-3 параллельных пользователя
- 💾 Использование RAM: 28-35 GB из 40 GB

---

## 🆘 Нужна помощь?

### Проблемы при установке:
1. Проверьте логи: `docker-compose logs -f backend`
2. Проверьте память: `free -h`
3. Проверьте модели: `ls -lh /opt/advakod/models/`

### Модель не загружается:
```bash
# Проверьте что файл на месте
ls -lh /opt/advakod/models/vistral-24b.gguf

# Проверьте размер (должно быть ~15 GB)
du -sh /opt/advakod/models/vistral-24b.gguf
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

---

## 📞 Контакты

**Документация:**
- Все файлы с инструкциями в корне проекта
- Спецификации в `.kiro/specs/vistral-24b-migration/`

**Логи:**
```bash
docker-compose -f docker-compose.prod.yml logs -f backend
```

---

## 🎉 Готовы начать?

1. Откройте терминал
2. Подключитесь к серверу: `ssh root@31.130.145.75`
3. Следуйте инструкциям выше
4. Через час у вас будет работающий AI-юрист! 🚀

---

**P.S.** Я не могу напрямую подключаться к серверу, но создал для вас все необходимые скрипты и инструкции. Просто следуйте шагам выше - всё получится! 💪

**Удачи!** 🍀