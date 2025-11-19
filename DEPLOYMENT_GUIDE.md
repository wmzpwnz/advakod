# 🚀 Руководство по деплою АДВАКОД в облако

## 🌐 Варианты деплоя

### 1. **DigitalOcean Droplet** (Рекомендуется)
**Стоимость**: $20-40/месяц
**Время настройки**: 30 минут

```bash
# Создаем Droplet (Ubuntu 22.04, 4GB RAM, 2 CPU)
# Подключаемся по SSH
ssh root@your-server-ip

# Устанавливаем Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Клонируем проект
git clone https://github.com/your-repo/advakod.git
cd advakod

# Запускаем продакшен
chmod +x setup_production.sh
./setup_production.sh
```

### 2. **AWS EC2** 
**Стоимость**: $25-50/месяц
**Время настройки**: 45 минут

```bash
# Создаем EC2 instance (t3.medium, Ubuntu 22.04)
# Настраиваем Security Groups:
# - Port 80 (HTTP)
# - Port 443 (HTTPS) 
# - Port 22 (SSH)
# - Port 8000 (API, только для админов)

# Подключаемся
ssh -i your-key.pem ubuntu@your-ec2-ip

# Устанавливаем Docker
sudo apt update
sudo apt install docker.io docker-compose
sudo usermod -aG docker ubuntu

# Деплоим
git clone https://github.com/your-repo/advakod.git
cd advakod
./setup_production.sh
```

### 3. **Google Cloud Platform**
**Стоимость**: $20-40/месяц
**Время настройки**: 40 минут

```bash
# Создаем VM instance (e2-standard-2)
# Включаем HTTP/HTTPS трафик
# Подключаемся
gcloud compute ssh your-instance

# Устанавливаем Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Деплоим
git clone https://github.com/your-repo/advakod.git
cd advakod
./setup_production.sh
```

### 4. **Hetzner Cloud** (Самый дешевый)
**Стоимость**: $10-20/месяц
**Время настройки**: 25 минут

```bash
# Создаем CX21 сервер (4GB RAM, 2 CPU)
# Подключаемся
ssh root@your-server-ip

# Устанавливаем Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Деплоим
git clone https://github.com/your-repo/advakod.git
cd advakod
./setup_production.sh
```

## 🔧 Настройка домена и SSL

### 1. Покупка домена
- **Namecheap**: $10-15/год
- **GoDaddy**: $12-20/год
- **Cloudflare**: Бесплатный DNS

### 2. Настройка DNS
```bash
# A запись
yourdomain.com -> YOUR_SERVER_IP
www.yourdomain.com -> YOUR_SERVER_IP

# CNAME для API
api.yourdomain.com -> yourdomain.com
```

### 3. SSL сертификат (Let's Encrypt)
```bash
# Устанавливаем Certbot
sudo apt install certbot python3-certbot-nginx

# Получаем сертификат
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Автообновление
sudo crontab -e
# Добавляем: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Мониторинг и масштабирование

### 1. Базовый мониторинг
```bash
# Устанавливаем htop для мониторинга ресурсов
sudo apt install htop

# Мониторим логи
docker-compose -f docker-compose.prod.yml logs -f
```

### 2. Продвинутый мониторинг
```bash
# Устанавливаем Prometheus + Grafana
docker-compose -f docker-compose.prod.yml up -d prometheus grafana

# Доступ к Grafana: http://yourdomain.com:3001
# Логин: admin / admin
```

### 3. Автоматические бэкапы
```bash
# Создаем скрипт бэкапа
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec advakod_postgres pg_dump -U advakod advakod_db > backup_$DATE.sql
aws s3 cp backup_$DATE.sql s3://your-backup-bucket/
rm backup_$DATE.sql
EOF

chmod +x backup.sh

# Добавляем в cron (ежедневно в 2:00)
crontab -e
# 0 2 * * * /path/to/backup.sh
```

## 🚀 CI/CD Pipeline

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to server
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /path/to/advakod
            git pull origin main
            docker-compose -f docker-compose.prod.yml down
            docker-compose -f docker-compose.prod.yml up -d --build
```

## 💰 Стоимость по провайдерам

| Провайдер | Конфигурация | Стоимость/месяц | Рекомендация |
|-----------|--------------|-----------------|--------------|
| **Hetzner** | CX21 (4GB RAM) | $10-15 | 🥇 Лучшее соотношение цена/качество |
| **DigitalOcean** | 4GB RAM | $20-25 | 🥈 Хорошая документация |
| **AWS** | t3.medium | $25-35 | 🥉 Для enterprise |
| **GCP** | e2-standard-2 | $20-30 | 🥉 Для Google экосистемы |

## 🔒 Безопасность

### 1. Firewall
```bash
# Настраиваем UFW
sudo ufw enable
sudo ufw allow 22    # SSH
sudo ufw allow 80   # HTTP
sudo ufw allow 443  # HTTPS
sudo ufw deny 8000  # API только через Nginx
```

### 2. Обновления
```bash
# Автоматические обновления безопасности
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 3. Мониторинг безопасности
```bash
# Устанавливаем fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

## 📈 Масштабирование

### Горизонтальное масштабирование
```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  backend:
    deploy:
      replicas: 3
    environment:
      - LOAD_BALANCER=true
```

### Вертикальное масштабирование
- **2GB RAM**: До 100 пользователей
- **4GB RAM**: До 500 пользователей  
- **8GB RAM**: До 2000 пользователей
- **16GB RAM**: До 10000 пользователей

## 🎯 Рекомендуемый план деплоя

### Этап 1: MVP (1-2 дня)
1. Hetzner CX21 сервер
2. Базовый домен
3. Let's Encrypt SSL
4. Простой деплой

### Этап 2: Production (1 неделя)
1. Настройка мониторинга
2. Автоматические бэкапы
3. CI/CD pipeline
4. Безопасность

### Этап 3: Scale (по необходимости)
1. Load balancer
2. Multiple servers
3. CDN
4. Database clustering

## 🚨 Чек-лист перед деплоем

- [ ] Домен куплен и настроен
- [ ] SSL сертификат получен
- [ ] Переменные окружения настроены
- [ ] Бэкапы настроены
- [ ] Мониторинг работает
- [ ] Firewall настроен
- [ ] CI/CD pipeline готов
- [ ] Тесты пройдены

**Готово к деплою! 🚀**
