# Используем официальный Python образ
FROM python:3.11-slim

# Метаданные
LABEL maintainer="Backend API Service"
LABEL description="Backend API for diagram recognition service coordination"

# Создаем рабочую директорию
WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY app/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY app/ .

# Переменные окружения по умолчанию
ENV VLM_SERVICE_URL="http://vlm-inference:8002"
ENV ADAPTER_SERVICE_URL="http://adapter:8001"
ENV DB_SERVICE_URL="http://database:8003"
ENV REQUEST_TIMEOUT="120"

# Открываем порт
EXPOSE 8000

# Запуск приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]