# 🚀 3 КОМАНДЫ ДЛЯ ЗАПУСКА АДВАКОД

## 🎯 ПРОСТО ВЫПОЛНИТЕ ЭТИ 3 КОМАНДЫ:

### **1️⃣ Скопируйте файлы на сервер:**
```bash
scp -r backend frontend docker-compose.prod.yml nginx.conf FINAL_DEPLOY.sh root@31.130.145.75:/opt/advakod/
```

### **2️⃣ Подключитесь к серверу:**
```bash
ssh root@31.130.145.75
```

### **3️⃣ Запустите финальный скрипт:**
```bash
cd /opt/advakod
chmod +x FINAL_DEPLOY.sh
bash FINAL_DEPLOY.sh
```

## 🎉 ВСЁ! САЙТ ЗАРАБОТАЕТ!

**Время выполнения:** 30-60 минут

**Результат:**
- ✅ Сайт: http://31.130.145.75
- ✅ API: http://31.130.145.75/api/v1
- ✅ AI-юрист с Vistral-24B готов к работе!

## 🤖 ЧТО ПОЛУЧИТЕ:

- **Текстовый чат** с AI-юристом (Vistral-24B)
- **Голосовое управление** (Borealis)
- **RAG система** с векторной базой
- **Анализ документов**

## 📚 ДОПОЛНИТЕЛЬНЫЕ ФАЙЛЫ:

- **FINAL_DEPLOY.sh** - Финальный скрипт развертывания
- **QUICK_FIX.sh** - Быстрое исправление проблем
- **CHECK_STATUS.sh** - Диагностика системы
- **SITE_NOT_WORKING.md** - Решение проблем

## 🆘 ЕСЛИ ЧТО-ТО НЕ РАБОТАЕТ:

1. **Проверьте статус:**
   ```bash
   bash CHECK_STATUS.sh
   ```

2. **Исправьте проблемы:**
   ```bash
   bash QUICK_FIX.sh
   ```

3. **Проверьте логи:**
   ```bash
   docker-compose -f docker-compose.prod.yml logs -f backend
   ```

**УДАЧНОГО РАЗВЕРТЫВАНИЯ!** 🚀