# Используем официальный Python образ
FROM python:3.11-slim

# Метаданные
LABEL maintainer="Frontend UI Service"
LABEL description="Streamlit UI for diagram recognition service"

# Создаем рабочую директорию
WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY app/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY app/ .

# Переменные окружения по умолчанию
ENV BACKEND_URL="http://backend:8000"

# Открываем порт Streamlit
EXPOSE 8501

# Запуск Streamlit
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]