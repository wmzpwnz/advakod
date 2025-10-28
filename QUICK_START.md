# ⚡ Быстрый старт - 5 команд

## 🎯 Что нужно сделать

Просто выполните эти команды на сервере **31.130.145.75**

---

## 📋 Команды

### 1. Подключитесь к серверу
```bash
ssh root@31.130.145.75
# Пароль: pG4Ju#i+i5+UPd
```

### 2. Создайте скрипт настройки сервера
```bash
cat > /root/1_setup_server.sh << 'SCRIPT_END'
# Вставьте сюда содержимое файла 1_setup_server.sh
SCRIPT_END

chmod +x /root/1_setup_server.sh
bash /root/1_setup_server.sh
```

### 3. Создайте скрипт загрузки моделей
```bash
cat > /root/2_download_models.sh << 'SCRIPT_END'
# Вставьте сюда содержимое файла 2_download_models.sh
SCRIPT_END

chmod +x /root/2_download_models.sh
bash /root/2_download_models.sh
```

⏱️ **Подождите 20-40 минут** пока загрузятся модели (~17 GB)

### 4. Скопируйте проект
```bash
# На вашей локальной машине:
scp -r backend frontend docker-compose.prod.yml nginx.conf root@31.130.145.75:/opt/advakod/
```

### 5. Запустите проект
```bash
# На сервере:
cd /opt/advakod
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml logs -f backend
```

⏱️ **Подождите 5-10 минут** пока загрузятся модели в память

---

## ✅ Готово!

Проверьте: `curl http://localhost/api/v1/health`

Если видите `{"status": "healthy"}` - всё работает! 🎉

---

## 📝 Полная инструкция

Смотрите файл **DEPLOY_INSTRUCTIONS.md** для детальных инструкций.

---

## 🆘 Нужна помощь?

1. Проверьте логи: `docker-compose logs -f backend`
2. Проверьте ресурсы: `free -h` и `docker stats`
3. Проверьте модели: `ls -lh /opt/advakod/models/`