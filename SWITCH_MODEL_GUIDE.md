# 🔄 Руководство по смене модели

**Дата:** 22 октября 2025  
**Разработчик:** Багбеков Азиз | Компания "Аврамир"

---

## 🎯 АВТОМАТИЧЕСКАЯ УСТАНОВКА

### Запустите скрипт:

```bash
./DOWNLOAD_SAIGA_8B.sh
```

**Скрипт автоматически:**
1. ✅ Скачает Saiga Llama 8B (~5 GB)
2. ✅ Обновит конфигурацию
3. ✅ Перезапустит backend
4. ✅ Проверит работу

---

## 📝 РУЧНАЯ УСТАНОВКА

### Шаг 1: Скачать модель

```bash
cd /Users/macbook/llama.cpp/models
wget https://huggingface.co/IlyaGusev/saiga_llama3_8b_gguf/resolve/main/model-q4_K.gguf \
  -O saiga_llama3_8b_q4_K.gguf
```

### Шаг 2: Обновить конфигурацию

```bash
# Открыть .env
nano /Users/macbook/Desktop/advakod/backend/.env

# Добавить или изменить строку:
SAIGA_MODEL_PATH=/Users/macbook/llama.cpp/models/saiga_llama3_8b_q4_K.gguf
```

### Шаг 3: Перезапустить backend

```bash
# Остановить
pkill -f "python.*main.py"

# Запустить
cd /Users/macbook/Desktop/advakod/backend
source venv/bin/activate
python3 main.py
```

---

## 🔍 ПРОВЕРКА

### Проверить какая модель используется:

```bash
# Проверить конфигурацию
grep SAIGA_MODEL_PATH backend/.env

# Проверить размер файла
ls -lh /Users/macbook/llama.cpp/models/saiga*

# Проверить работу backend
curl http://localhost:8000/health
```

---

## 🔄 ВЕРНУТЬСЯ К SAIGA 7B

Если новая модель не подошла:

```bash
# Обновить .env
echo "SAIGA_MODEL_PATH=/Users/macbook/llama.cpp/models/saiga_mistral_7b_q4_K.gguf" > backend/.env

# Перезапустить
pkill -f "python.*main.py"
cd backend && source venv/bin/activate && python3 main.py
```

---

## 📊 СРАВНЕНИЕ МОДЕЛЕЙ

### Saiga Mistral 7B (текущая):
- ✅ Размер: 4.1 GB
- ✅ Скорость: Очень быстрая
- ✅ Качество: Хорошее
- ✅ Русский язык: Отлично

### Saiga Llama 8B (новая):
- 📦 Размер: ~5 GB
- ⚡ Скорость: Быстрая
- ⭐ Качество: Отличное
- ✅ Русский язык: Отлично

---

## 💡 РЕКОМЕНДАЦИЯ

**Попробуйте Saiga 8B если:**
- Нужно лучшее качество ответов
- Готовы к небольшому замедлению
- Хотите более точные юридические консультации

**Оставьте Saiga 7B если:**
- Скорость важнее качества
- Текущее качество устраивает
- Система обратной связи улучшит ответы

---

## 🐛 TROUBLESHOOTING

### Модель не скачивается:

```bash
# Проверить wget
which wget

# Если нет - установить
brew install wget

# Попробовать снова
./DOWNLOAD_SAIGA_8B.sh
```

### Backend не запускается:

```bash
# Проверить логи
tail -f backend.log

# Проверить путь к модели
ls -la /Users/macbook/llama.cpp/models/saiga_llama3_8b_q4_K.gguf

# Проверить .env
cat backend/.env | grep SAIGA
```

### Модель загружается слишком долго:

```bash
# Проверить размер RAM
top

# Если мало памяти - вернуться к 7B
echo "SAIGA_MODEL_PATH=/Users/macbook/llama.cpp/models/saiga_mistral_7b_q4_K.gguf" > backend/.env
pkill -f "python.*main.py"
cd backend && source venv/bin/activate && python3 main.py
```

---

## 👨‍💻 РАЗРАБОТЧИК

**Багбеков Азиз**  
Компания: **"Аврамир"**  
Email: aziz@bagbekov.ru  
Сайт: [A2codex.com](https://a2codex.com)

**A2codex.com - Ваш персональный ИИ-правовед 24/7!** 🏛️⚖️
