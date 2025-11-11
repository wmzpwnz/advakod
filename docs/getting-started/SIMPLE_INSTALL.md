# 🚀 ПРОСТАЯ УСТАНОВКА SAIGA 8B

## ШАГ 1: Установи wget

```bash
brew install wget
```

## ШАГ 2: Вернись в проект

```bash
cd /Users/macbook/Desktop/advakod
```

## ШАГ 3: Скачай модель

```bash
cd /Users/macbook/llama.cpp/models
wget https://huggingface.co/IlyaGusev/saiga_llama3_8b_gguf/resolve/main/model-q4_K.gguf -O saiga_llama3_8b_q4_K.gguf
```

## ШАГ 4: Обновить конфигурацию

```bash
cd /Users/macbook/Desktop/advakod
echo "SAIGA_MODEL_PATH=/Users/macbook/llama.cpp/models/saiga_llama3_8b_q4_K.gguf" >> backend/.env
```

## ШАГ 5: Перезапустить backend

```bash
pkill -f "python.*main.py"
cd /Users/macbook/Desktop/advakod/backend
source venv/bin/activate
python3 main.py
```

---

## ИЛИ ИСПОЛЬЗУЙ CURL (без wget):

```bash
cd /Users/macbook/llama.cpp/models
curl -L https://huggingface.co/IlyaGusev/saiga_llama3_8b_gguf/resolve/main/model-q4_K.gguf -o saiga_llama3_8b_q4_K.gguf
```

---

## ИЛИ ОСТАВЬ SAIGA 7B!

Она уже работает и достаточно хороша! 

Просто открой: **http://localhost:3000**
