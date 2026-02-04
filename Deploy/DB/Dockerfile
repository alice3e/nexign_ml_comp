# Используем официальный Python образ
FROM python:3.11-slim

# Метаданные
LABEL maintainer="Database Service"
LABEL description="SQLite database service for logging inference requests"

# Создаем рабочую директорию
WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY app/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY app/ .

# Создаем директорию для базы данных
RUN mkdir -p /data

# Переменные окружения по умолчанию
ENV DB_PATH="/data/requests.db"

# Volume для базы данных
VOLUME ["/data"]

# Открываем порт
EXPOSE 8003

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8003/health').raise_for_status()" || exit 1

# Запуск приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003", "--log-level", "info"]