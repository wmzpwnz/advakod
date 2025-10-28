# 🚀 Быстрое развертывание АДВАКОД

## ⚠️ Проблема с SSH
SSH порт 22 недоступен. Возможные решения:

### 1. Проверьте SSH сервис на сервере
```bash
# Подключитесь к серверу через веб-консоль провайдера
systemctl status ssh
systemctl start ssh
systemctl enable ssh
```

### 2. Проверьте firewall
```bash
# UFW
sudo ufw status
sudo ufw allow 22/tcp

# iptables
sudo iptables -L
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
```

### 3. Проверьте SSH конфигурацию
```bash
# Проверьте файл /etc/ssh/sshd_config
sudo nano /etc/ssh/sshd_config

# Убедитесь что:
# Port 22
# PermitRootLogin yes
# PasswordAuthentication yes

# Перезапустите SSH
sudo systemctl restart ssh
```

## 🔄 Альтернативные способы развертывания

### Вариант 1: Веб-консоль провайдера
1. Войдите в веб-консоль вашего хостинг-провайдера
2. Скачайте все файлы проекта на сервер
3. Выполните команды развертывания

### Вариант 2: SCP загрузка файлов
```bash
# Загрузите файлы на сервер
scp -r ./backend root@89.23.98.167:/opt/advakod/
scp -r ./frontend root@89.23.98.167:/opt/advakod/
scp docker-compose.prod.yml root@89.23.98.167:/opt/advakod/
scp nginx.conf root@89.23.98.167:/opt/advakod/
scp env.production root@89.23.98.167:/opt/advakod/
scp *.sh root@89.23.98.167:/opt/advakod/
```

### Вариант 3: Git клонирование
```bash
# На сервере
git clone <your-repo-url> /opt/advakod
cd /opt/advakod
```

## 📋 Команды для выполнения на сервере

### 1. Установка Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker
```

### 2. Установка Docker Compose
```bash
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

### 3. Создание директорий
```bash
mkdir -p /opt/advakod
mkdir -p /opt/advakod/models
mkdir -p /opt/advakod/backups
mkdir -p /opt/advakod/logs
```

### 4. Настройка .env
```bash
cd /opt/advakod
cp env.production .env

# Отредактируйте .env файл
nano .env
```

### 5. Загрузка модели Saiga 13B
```bash
cd /opt/advakod
chmod +x *.sh
./download_saiga_13b.sh
```

### 6. Запуск сервисов
```bash
cd /opt/advakod
docker-compose -f docker-compose.prod.yml up -d
```

### 7. Настройка SSL
```bash
cd /opt/advakod
./setup_ssl.sh advacodex.com admin@advacodex.com
```

## 🔧 Проверка развертывания

### Проверка сервисов
```bash
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f
```

### Проверка API
```bash
curl http://localhost/api/v1/health
curl https://advacodex.com/api/v1/health
```

## 🆘 Если ничего не работает

### Создайте архив с файлами
```bash
# На локальной машине
tar -czf advakod-deployment.tar.gz backend/ frontend/ docker-compose.prod.yml nginx.conf env.production *.sh
```

### Загрузите через веб-интерфейс
1. Загрузите архив на сервер
2. Распакуйте: `tar -xzf advakod-deployment.tar.gz`
3. Выполните команды развертывания

## 📞 Контакты для поддержки
Если нужна помощь - обращайтесь!
