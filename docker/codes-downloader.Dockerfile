# Dockerfile для скачивания кодексов
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    build-essential \
    cmake \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt
COPY backend/requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY backend/app/ ./app/
COPY backend/scripts/ ./scripts/

# Создаем директории для данных
RUN mkdir -p /app/data/legal_documents/codes \
    /app/logs \
    /app/temp

# Устанавливаем права доступа
RUN chmod +x /app/scripts/download_codes.py

# Создаем пользователя для безопасности
RUN useradd -m -u 1000 codesdownloader && \
    chown -R codesdownloader:codesdownloader /app

USER codesdownloader

# Команда по умолчанию - запускаем систему кодексов в фоновом режиме (без интерактивного ввода)
CMD ["python", "-c", "import sys; sys.path.insert(0, '/app'); from scripts.start_codes_system import CodesSystemManager; manager = CodesSystemManager(); manager.initialize_system(); manager.run_system()"]
