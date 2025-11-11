# 🚀 Руководство по развертыванию на Production

**Сервер:** advacodex.com  
**Дата:** 22 октября 2025  
**Разработчик:** Багбеков Азиз | Компания "Аврамир"

---

## 📊 ТЕКУЩИЙ СТАТУС

✅ **Nginx работает** - показывает дефолтную страницу  
❌ **Backend НЕ запущен**  
❌ **Frontend НЕ настроен**

---

## 🎯 ЧТО НУЖНО СДЕЛАТЬ

### 1. Загрузить код на сервер

Если код еще не на сервере:

```bash
# На локальной машине
tar -czf a2codex_complete.tar.gz \
  --exclude='node_modules' \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='*.pyc' \
  --exclude='build' \
  --exclude='dist' \
  .

# Загрузить на сервер (через FTP/SFTP/SCP)
scp a2codex_complete.tar.gz root@advacodex.com:/opt/
```

### 2. Распаковать на сервере

```bash
# Подключиться к серверу
ssh root@advacodex.com

# Распаковать
cd /opt
mkdir -p a2codex
cd a2codex
tar -xzf ../a2codex_complete.tar.gz
```

### 3. Установить зависимости

```bash
cd /opt/a2codex

# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 4. Применить миграции

```bash
cd /opt/a2codex/backend
source venv/bin/activate

# Применить миграции
alembic upgrade head

# Инициализировать категории
python3 init_feedback_system.py
```

### 5. Запустить сервер

```bash
cd /opt/a2codex
chmod +x START_PRODUCTION_SERVER.sh
./START_PRODUCTION_SERVER.sh
```

---

## 🔧 ЧТО ДЕЛАЕТ СКРИПТ

1. **Останавливает** старые процессы
2. **Запускает Backend** (Python FastAPI на порту 8000)
3. **Собирает Frontend** (React production build)
4. **Настраивает Nginx** (проксирует запросы)
5. **Перезагружает Nginx**

---

## 📁 СТРУКТУРА NGINX

```nginx
server {
    listen 80;
    server_name advacodex.com www.advacodex.com;

    # Frontend (React build)
    location / {
        root /opt/a2codex/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        # ... proxy settings
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        # ... websocket settings
    }
}
```

---

## 🔍 ПРОВЕРКА РАБОТЫ

### После запуска проверьте:

```bash
# 1. Backend работает
curl http://localhost:8000/health
# Должен вернуть: {"status":"healthy",...}

# 2. Frontend собран
ls -la /opt/a2codex/frontend/build/
# Должны быть файлы: index.html, static/, ...

# 3. Nginx работает
sudo systemctl status nginx
# Должен быть: active (running)

# 4. Сайт доступен
curl http://advacodex.com
# Должен вернуть HTML страницу React
```

---

## 📊 ЛОГИ

### Backend:
```bash
tail -f /opt/a2codex/logs/backend.log
```

### Nginx:
```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

---

## 🔄 УПРАВЛЕНИЕ

### Остановить:
```bash
pkill -f "python.*main.py"
```

### Перезапустить:
```bash
cd /opt/a2codex
./START_PRODUCTION_SERVER.sh
```

### Проверить процессы:
```bash
ps aux | grep -E "python.*main.py"
```

---

## 🐛 TROUBLESHOOTING

### Проблема: Backend не запускается

```bash
# Проверить логи
tail -n 50 /opt/a2codex/logs/backend.log

# Проверить порт 8000
lsof -i :8000

# Запустить вручную для отладки
cd /opt/a2codex/backend
source venv/bin/activate
python3 main.py
```

### Проблема: Frontend не собирается

```bash
# Проверить зависимости
cd /opt/a2codex/frontend
npm list

# Пересобрать
rm -rf build node_modules
npm install
npm run build
```

### Проблема: Nginx показывает ошибку

```bash
# Проверить конфигурацию
sudo nginx -t

# Проверить логи
sudo tail -f /var/log/nginx/error.log

# Перезапустить nginx
sudo systemctl restart nginx
```

### Проблема: 502 Bad Gateway

Это значит nginx не может подключиться к backend:

```bash
# Проверить, что backend работает
curl http://localhost:8000/health

# Если не работает - запустить
cd /opt/a2codex/backend
source venv/bin/activate
nohup python3 main.py > ../logs/backend.log 2>&1 &
```

---

## 🔐 БЕЗОПАСНОСТЬ

### Настроить HTTPS (Let's Encrypt):

```bash
# Установить certbot
sudo apt install certbot python3-certbot-nginx

# Получить сертификат
sudo certbot --nginx -d advacodex.com -d www.advacodex.com

# Автообновление
sudo certbot renew --dry-run
```

### Настроить firewall:

```bash
# Разрешить HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Запретить прямой доступ к backend
sudo ufw deny 8000/tcp
```

---

## 📚 ДОПОЛНИТЕЛЬНО

### Автозапуск при перезагрузке:

Создать systemd service:

```bash
sudo nano /etc/systemd/system/a2codex-backend.service
```

```ini
[Unit]
Description=A2codex Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/a2codex/backend
Environment="PATH=/opt/a2codex/backend/venv/bin"
ExecStart=/opt/a2codex/backend/venv/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable a2codex-backend
sudo systemctl start a2codex-backend
```

---

## ✅ CHECKLIST

- [ ] Код загружен на сервер
- [ ] Зависимости установлены (backend + frontend)
- [ ] Миграции применены
- [ ] Категории инициализированы
- [ ] Backend запущен (порт 8000)
- [ ] Frontend собран (build/)
- [ ] Nginx настроен
- [ ] Nginx перезагружен
- [ ] Сайт доступен (http://advacodex.com)
- [ ] API работает (/api/v1/)
- [ ] Docs доступны (/docs)
- [ ] HTTPS настроен (опционально)
- [ ] Firewall настроен (опционально)
- [ ] Автозапуск настроен (опционально)

---

## 🎉 ГОТОВО!

После выполнения всех шагов:

✅ Сайт доступен: **http://advacodex.com**  
✅ API работает: **http://advacodex.com/api/v1/**  
✅ Docs доступны: **http://advacodex.com/docs**  
✅ Система обратной связи работает  
✅ Панель модерации доступна  

---

## 👨‍💻 РАЗРАБОТЧИК

**Багбеков Азиз**  
Компания: **"Аврамир"**  
Email: aziz@bagbekov.ru  
Сайт: [A2codex.com](https://a2codex.com)

**A2codex.com - Ваш персональный ИИ-правовед 24/7!** 🏛️⚖️
