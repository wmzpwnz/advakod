# 🤖 Доступные модели Saiga

## ✅ РЕАЛЬНО СУЩЕСТВУЮЩИЕ МОДЕЛИ:

### 1. Saiga Mistral 7B (У ТЕБЯ СЕЙЧАС)
- **Размер:** 4.1 GB
- **Ссылка:** https://huggingface.co/IlyaGusev/saiga_mistral_7b_gguf
- **Статус:** ✅ Установлена
- **Качество:** Отличное для юридических консультаций

### 2. Saiga Llama 8B
- **Размер:** ~5 GB
- **Ссылка:** https://huggingface.co/IlyaGusev/saiga_llama3_8b_gguf
- **Статус:** ❌ Не установлена
- **Качество:** Лучше чем 7B

### 3. Saiga Llama 3 70B (ОГРОМНАЯ!)
- **Размер:** ~40 GB
- **Ссылка:** https://huggingface.co/IlyaGusev/saiga_llama3_70b_gguf
- **Статус:** ❌ Слишком большая для Mac
- **Качество:** Лучшее, но требует мощный сервер

---

## ❌ НЕ СУЩЕСТВУЕТ:

- ❌ Saiga Llama 13B
- ❌ Saiga Llama 14B
- ❌ Saiga Mistral 13B

---

## 💡 РЕКОМЕНДАЦИЯ:

### ОСТАВЬ SAIGA 7B!

**Почему:**
1. ✅ Уже работает
2. ✅ Быстрая
3. ✅ Хорошее качество
4. ✅ Система обратной связи улучшит ответы
5. ✅ Модераторы исправят ошибки

### ИЛИ установи Saiga 8B:

```bash
# Установи wget
brew install wget

# Скачай модель
cd /Users/macbook/llama.cpp/models
wget https://huggingface.co/IlyaGusev/saiga_llama3_8b_gguf/resolve/main/model-q4_K.gguf -O saiga_llama3_8b_q4_K.gguf

# Обновить конфигурацию
cd /Users/macbook/Desktop/advakod
echo "SAIGA_MODEL_PATH=/Users/macbook/llama.cpp/models/saiga_llama3_8b_q4_K.gguf" >> backend/.env

# Перезапустить
pkill -f "python.*main.py"
cd backend && source venv/bin/activate && python3 main.py
```

---

## 🎯 ИТОГ:

**Saiga 14B НЕ СУЩЕСТВУЕТ!**

Доступны только:
- 7B (у тебя)
- 8B (можно установить)
- 70B (слишком большая)

**Рекомендую оставить 7B и открыть сайт:**

**http://localhost:3000**

Система обратной связи уже работает! 🎉
