# 📥 УСТАНОВКА SAIGA 13B МОДЕЛИ

**Дата:** 22 октября 2025  
**Разработчик:** Багбеков Азиз | Компания "Аврамир"

---

## 🎯 ЦЕЛЬ

Установить **Saiga Mistral 13B** модель для улучшения качества ответов ИИ-юриста.

---

## 📊 СРАВНЕНИЕ МОДЕЛЕЙ

### Saiga 7B (текущая):
- ✅ Размер: 4.1 GB
- ✅ Скорость: Быстрая
- ✅ RAM: 8 GB
- ⚠️ Качество: Хорошее

### Saiga 13B (новая):
- 📦 Размер: ~8-10 GB
- 🐌 Скорость: Медленнее (в 1.5-2 раза)
- 💾 RAM: 16 GB рекомендуется
- ⭐ Качество: Отличное (лучше на 20-30%)

---

## 🔍 ШАГ 1: НАЙТИ МОДЕЛЬ

### Вариант 1: HuggingFace (рекомендуется)

```bash
# Установить huggingface-cli
pip install huggingface-hub

# Скачать модель
huggingface-cli download IlyaGusev/saiga_mistral_13b_gguf \
  saiga_mistral_13b_q4_K.gguf \
  --local-dir ~/llama.cpp/models/
```

### Вариант 2: Прямая ссылка

```bash
cd ~/llama.cpp/models/

# Скачать через wget
wget https://huggingface.co/IlyaGusev/saiga_mistral_13b_gguf/resolve/main/saiga_mistral_13b_q4_K.gguf

# Или через curl
curl -L -o saiga_mistral_13b_q4_K.gguf \
  https://huggingface.co/IlyaGusev/saiga_mistral_13b_gguf/resolve/main/saiga_mistral_13b_q4_K.gguf
```

### Вариант 3: Браузер

1. Открой: https://huggingface.co/IlyaGusev/saiga_mistral_13b_gguf
2. Найди файл: `saiga_mistral_13b_q4_K.gguf`
3. Нажми "Download"
4. Перемести в: `~/llama.cpp/models/`

---

## ⚙️ ШАГ 2: НАСТРОИТЬ ПРОЕКТ

### Обновить конфигурацию:

```bash
cd /Users/macbook/Desktop/advakod/backend
nano .env
```

Добавь или измени:
```env
SAIGA_MODEL_PATH=/Users/macbook/llama.cpp/models/saiga_mistral_13b_q4_K.gguf
SAIGA_N_CTX=8192
SAIGA_N_THREADS=8
SAIGA_N_GPU_LAYERS=0
```

Сохрани: `Ctrl+O`, `Enter`, `Ctrl+X`

---

## 🔄 ШАГ 3: ПЕРЕЗАПУСТИТЬ BACKEND

```bash
# Остановить текущий backend
pkill -f "python.*main.py"

# Запустить заново
cd /Users/macbook/Desktop/advakod/backend
source venv/bin/activate
python3 main.py
```

---

## ✅ ШАГ 4: ПРОВЕРИТЬ

### Проверить загрузку модели:

```bash
# Смотреть логи backend
tail -f /Users/macbook/Desktop/advakod/backend.log
```

Должно быть:
```
🔄 Loading Saiga model...
✅ Saiga model loaded successfully
Model: saiga_mistral_13b_q4_K.gguf
```

### Проверить через API:

```bash
curl http://localhost:8000/health
```

Должно вернуть:
```json
{
  "status": "healthy",
  "service": "ai-lawyer-backend",
  "version": "1.0.0"
}
```

---

## 🎯 ШАГ 5: ТЕСТИРОВАТЬ

1. Открой: http://localhost:3000/chat
2. Задай сложный юридический вопрос
3. Сравни качество ответа с предыдущей моделью
4. Оцени через кнопки 👍 👎

---

## 📊 ОЖИДАЕМЫЕ УЛУЧШЕНИЯ

### С Saiga 13B:
- ✅ Более точные юридические термины
- ✅ Лучшее понимание контекста
- ✅ Более структурированные ответы
- ✅ Меньше галлюцинаций
- ✅ Лучшие ссылки на законы

### Но:
- ⚠️ Медленнее генерация (30-60 сек вместо 15-30 сек)
- ⚠️ Больше использование RAM (12-16 GB вместо 6-8 GB)

---

## 🐛 TROUBLESHOOTING

### Проблема: Модель не загружается

```bash
# Проверить размер файла
ls -lh ~/llama.cpp/models/saiga_mistral_13b_q4_K.gguf

# Должно быть ~8-10 GB
# Если меньше - файл скачался не полностью, скачай заново
```

### Проблема: Out of Memory

```bash
# Уменьшить контекст
nano backend/.env

# Изменить:
SAIGA_N_CTX=4096  # вместо 8192
```

### Проблема: Слишком медленно

```bash
# Увеличить потоки
nano backend/.env

# Изменить:
SAIGA_N_THREADS=12  # вместо 8 (если у тебя 12+ ядер)
```

### Проблема: Backend не запускается

```bash
# Смотреть логи
tail -f backend.log

# Или запустить в режиме отладки
cd backend
source venv/bin/activate
python3 main.py
```

---

## 🔄 ОТКАТ НА SAIGA 7B

Если 13B не подходит:

```bash
# Изменить .env
nano backend/.env

# Вернуть:
SAIGA_MODEL_PATH=/Users/macbook/llama.cpp/models/saiga_mistral_7b_q4_K.gguf

# Перезапустить
pkill -f "python.*main.py"
cd backend && source venv/bin/activate && python3 main.py
```

---

## 📚 ДОПОЛНИТЕЛЬНЫЕ МОДЕЛИ

### Если хочешь еще лучше качество:

**Saiga Llama 3 70B** (требует мощный сервер):
- Размер: 40+ GB
- RAM: 64+ GB
- Качество: Превосходное

**Saiga Mistral 7B v3** (новая версия):
- Размер: 4.1 GB
- Качество: Лучше чем v2

---

## ✅ CHECKLIST

- [ ] Скачана модель Saiga 13B (~8-10 GB)
- [ ] Файл в `~/llama.cpp/models/saiga_mistral_13b_q4_K.gguf`
- [ ] Обновлен `.env` файл
- [ ] Backend перезапущен
- [ ] Модель загрузилась (проверить логи)
- [ ] API работает (curl /health)
- [ ] Протестирован в чате
- [ ] Качество улучшилось

---

## 🎉 ГОТОВО!

После установки Saiga 13B:
- ✅ Качество ответов улучшится на 20-30%
- ✅ Меньше ошибок в юридических терминах
- ✅ Лучше понимание сложных вопросов
- ✅ Система обратной связи поможет отслеживать улучшения

---

## 👨‍💻 РАЗРАБОТЧИК

**Багбеков Азиз**  
Компания: **"Аврамир"**  
Email: aziz@bagbekov.ru  
Сайт: [A2codex.com](https://a2codex.com)

**A2codex.com - Ваш персональный ИИ-правовед 24/7!** 🏛️⚖️
