# Multi-stage build для оптимизации размера образа
FROM python:3.11-slim as base

# Устанавливаем системные зависимости (включая Chrome для Selenium)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libgomp1 \
    wget \
    gnupg \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Chrome для Selenium (новый метод без apt-key)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем ChromeDriver (используем chrome-for-testing)
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1) \
    && wget -O /tmp/chromedriver.zip "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/$(curl -s https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_VERSION})/linux64/chromedriver-linux64.zip" 2>/dev/null || \
    wget -O /tmp/chromedriver.zip "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/120.0.6099.109/linux64/chromedriver-linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/bin/chromedriver || mv /tmp/chromedriver /usr/bin/chromedriver \
    && rm -rf /tmp/chromedriver* \
    && chmod +x /usr/bin/chromedriver

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем llama-cpp-python с оптимизацией для CPU
RUN pip install --no-cache-dir llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

# Production stage
FROM python:3.11-slim as production

# Устанавливаем только runtime зависимости (включая Chrome)
RUN apt-get update && apt-get install -y \
    curl \
    libgomp1 \
    wget \
    gnupg \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Chrome для Selenium (новый метод без apt-key)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем ChromeDriver (используем chrome-for-testing)
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1) \
    && wget -O /tmp/chromedriver.zip "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/$(curl -s https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_VERSION})/linux64/chromedriver-linux64.zip" 2>/dev/null || \
    wget -O /tmp/chromedriver.zip "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/120.0.6099.109/linux64/chromedriver-linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/bin/chromedriver || mv /tmp/chromedriver /usr/bin/chromedriver \
    && rm -rf /tmp/chromedriver* \
    && chmod +x /usr/bin/chromedriver

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash advakod

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости из base stage
COPY --from=base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=base /usr/local/bin /usr/local/bin

# Создаем директории для данных
RUN mkdir -p /app/logs /app/uploads /app/temp /opt/advakod/models

# Копируем исходный код
COPY . .

# Устанавливаем права доступа
RUN chown -R advakod:advakod /app /opt/advakod

# Убеждаемся, что директории имеют правильные права
RUN chmod -R 755 /app/logs /app/uploads /app/temp

# Создаем файл логов с правильными правами
RUN touch /app/logs/security.log && chown advakod:advakod /app/logs/security.log && chmod 644 /app/logs/security.log

# Переключаемся на пользователя advakod
USER advakod

# Открываем порт
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Запускаем приложение
CMD ["python", "main.py"]
