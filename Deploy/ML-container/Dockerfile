# Используем официальный Python образ
FROM python:3.11-slim

# Метаданные
LABEL maintainer="VLM Inference Service"
LABEL description="Qwen3-VL inference service for diagram recognition"

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY app/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY app/ .

# Создаем директории для моделей
RUN mkdir -p /app/models/base /app/models/weights

# Переменные окружения по умолчанию
ENV BASE_MODEL_ID="Qwen/Qwen3-VL-2B-Instruct"
ENV ADAPTER_PATH="/app/models/weights"
ENV DEVICE="cpu"
ENV TORCH_DTYPE="float16"
ENV MAX_NEW_TOKENS="384"
ENV HF_HOME="/root/.cache/huggingface"

# Volumes для моделей
VOLUME ["/app/models/weights", "/root/.cache/huggingface"]

# Открываем порт
EXPOSE 8002

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8002/health').raise_for_status()" || exit 1

# Запуск приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--log-level", "info"]