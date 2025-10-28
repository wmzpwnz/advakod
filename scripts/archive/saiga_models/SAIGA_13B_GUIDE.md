# 🤖 Руководство по установке Saiga 13B

**Дата:** 22 октября 2025  
**Разработчик:** Багбеков Азиз | Компания "Аврамир"

---

## ⚠️ ВАЖНО!

**Saiga 13B модель НЕ существует в открытом доступе!**

Доступные варианты:
- ✅ **Saiga Mistral 7B** (уже установлена) - 4.1 GB
- 📦 **Saiga Llama 8B** - ~5 GB
- 📦 **Llama 2 13B** - ~8 GB
- 📦 **Mistral 7B Instruct** - ~4 GB

---

## 🎯 РЕКОМЕНДАЦИЯ

### Оставьте Saiga 7B!

**Почему:**
1. ✅ Уже установлена и работает
2. ✅ Быстрая (важно для пользователей)
3. ✅ Хорошее качество для юридических консультаций
4. ✅ Работает на Mac без проблем
5. ✅ Система обратной связи улучшит качество

**Размер:** 4.1 GB  
**Скорость:** Быстро  
**Качество:** Отлично для 90% задач

---

## 📦 ЕСЛИ ВСЕ ЖЕ НУЖНА БОЛЬШАЯ МОДЕЛЬ

### Вариант 1: Saiga Llama 8B

**Ссылка:** https://huggingface.co/IlyaGusev/saiga_llama3_8b_gguf

**Установка:**
```bash
cd /Users/macbook/llama.cpp/models

# Скачать с HuggingFace
wget https://huggingface.co/IlyaGusev/saiga_llama3_8b_gguf/resolve/main/model-q4_K.gguf \
  -O saiga_llama3_8b_q4_K.gguf

# Обновить конфигурацию
echo "SAIGA_MODEL_PATH=/Users/macbook/llama.cpp/models/saiga_llama3_8b_q4_K.gguf" >> ~/Desktop/advakod/backend/.env

# Перезапустить backend
pkill -f "python.*main.py"
cd ~/Desktop/advakod/backend
source venv/bin/activate
python3 main.py
```

**Характеристики:**
- Размер: ~5 GB
- Качество: Лучше чем 7B
- Скорость: Немного медленнее

---

### Вариант 2: Llama 2 13B Chat

**Ссылка:** https://huggingface.co/TheBloke/Llama-2-13B-chat-GGUF

**Установка:**
```bash
cd /Users/macbook/llama.cpp/models

# Скачать
wget https://huggingface.co/TheBloke/Llama-2-13B-chat-GGUF/resolve/main/llama-2-13b-chat.Q4_K_M.gguf

# Обновить конфигурацию
echo "SAIGA_MODEL_PATH=/Users/macbook/llama.cpp/models/llama-2-13b-chat.Q4_K_M.gguf" >> ~/Desktop/advakod/backend/.env

# Перезапустить
pkill -f "python.*main.py"
cd ~/Desktop/advakod/backend
source venv/bin/activate
python3 main.py
```

**Характеристики:**
- Размер: ~8 GB
- Качество: Отличное
- Скорость: Медленнее
- ⚠️ НЕ специализирована для русского языка!

---

### Вариант 3: Mistral 7B Instruct v0.2

**Ссылка:** https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF

**Установка:**
```bash
cd /Users/macbook/llama.cpp/models

# Скачать
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf

# Обновить конфигурацию
echo "SAIGA_MODEL_PATH=/Users/macbook/llama.cpp/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf" >> ~/Desktop/advakod/backend/.env

# Перезапустить
pkill -f "python.*main.py"
cd ~/Desktop/advakod/backend
source venv/bin/activate
python3 main.py
```

**Характеристики:**
- Размер: ~4 GB
- Качество: Отличное
- Скорость: Быстро
- ⚠️ Хуже работает с русским языком

---

## 📊 СРАВНЕНИЕ МОДЕЛЕЙ

| Модель | Размер | Скорость | Качество RU | Рекомендация |
|--------|--------|----------|-------------|--------------|
| **Saiga 7B** ✅ | 4.1 GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | **ЛУЧШИЙ ВЫБОР** |
| Saiga Llama 8B | 5 GB | ⚡⚡ | ⭐⭐⭐⭐⭐ | Если нужно качество |
| Llama 2 13B | 8 GB | ⚡ | ⭐⭐⭐ | Не рекомендуется |
| Mistral 7B | 4 GB | ⚡⚡⚡ | ⭐⭐⭐ | Альтернатива |

---

## 🔧 ПРОВЕРКА ТЕКУЩЕЙ МОДЕЛИ

```bash
# Проверить какая модель используется
grep SAIGA_MODEL_PATH backend/.env

# Проверить размер
ls -lh /Users/macbook/llama.cpp/models/saiga*

# Проверить работу
curl http://localhost:8000/health
```

---

## 💡 ПОЧЕМУ SAIGA 7B ДОСТАТОЧНО?

1. **Специализирована для русского языка** 🇷🇺
2. **Быстрая** - пользователи не ждут ⚡
3. **Качество отличное** для юридических консультаций ⚖️
4. **Система обратной связи** улучшит ответы 📈
5. **Модераторы** исправят ошибки 👨‍💼
6. **Обучение на датасетах** повысит точность 🎓

---

## 🎯 ИТОГОВАЯ РЕКОМЕНДАЦИЯ

### ✅ ОСТАВЬТЕ SAIGA 7B!

**Она:**
- Уже работает
- Достаточно быстрая
- Хорошее качество
- Специализирована для РФ

**Если качество недостаточно:**
- Используйте систему обратной связи
- Модераторы исправят ошибки
- Создайте датасеты для обучения
- Улучшите промпты

**Только если КРИТИЧЕСКИ нужно:**
- Установите Saiga Llama 8B
- Но будьте готовы к медленной работе

---

## 👨‍💻 РАЗРАБОТЧИК

**Багбеков Азиз**  
Компания: **"Аврамир"**  
Email: aziz@bagbekov.ru  
Сайт: [A2codex.com](https://a2codex.com)

**A2codex.com - Ваш персональный ИИ-правовед 24/7!** 🏛️⚖️
