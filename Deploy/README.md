# Сервис распознавания диаграмм - Deployment

Полная микросервисная система для распознавания алгоритмов по диаграммам с использованием VLM модели Qwen3-VL.

## Архитектура

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ :8501
       ▼
┌─────────────┐
│  Frontend   │ (Streamlit)
└──────┬──────┘
       │ :8000
       ▼
┌─────────────┐
│   Backend   │ (FastAPI)
└──┬───┬───┬──┘
   │   │   │
   │   │   └─────────┐
   │   │             │ :8003
   │   │      ┌──────▼──────┐
   │   │      │  Database   │ (SQLite)
   │   │      └─────────────┘
   │   │
   │   │ :8001
   │   ▼
   │ ┌─────────────┐
   │ │   Adapter   │ (Format Converter)
   │ └─────────────┘
   │
   │ :8002
   ▼
┌─────────────┐
│VLM Inference│ (Qwen3-VL + LoRA)
└─────────────┘
```

## Компоненты

| Сервис | Порт | Описание |
|--------|------|----------|
| Frontend | 8501 | Streamlit UI для загрузки диаграмм |
| Backend | 8000 | FastAPI координатор |
| VLM Inference | 8002 | Распознавание диаграмм |
| Adapter | 8001 | Конвертация форматов |
| Database | 8003 | SQLite логирование |

## Быстрый старт

### Предварительные требования

- Docker и Docker Compose
- 4+ GB свободного места (для модели)
- 8+ GB RAM (16 GB рекомендуется)
- Опционально: NVIDIA GPU с 8 GB VRAM

### 1. Подготовка

```bash
cd Deploy

# Создайте .env файл (опционально)
cp .env.example .env

# Убедитесь, что веса модели на месте
ls -la ML-container/docker-volumes/weights/
# Должны быть: adapter_config.json, adapter_model.safetensors, и др.
```

### 2. Запуск всех сервисов

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Проверка статуса
docker-compose ps
```

### 3. Доступ к сервисам

- **Frontend UI**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **VLM Service**: http://localhost:8002
- **Adapter Service**: http://localhost:8001
- **Database Service**: http://localhost:8003

## Управление

### Остановка

```bash
# Остановить все сервисы
docker-compose stop

# Остановить и удалить контейнеры
docker-compose down

# Удалить контейнеры и volumes
docker-compose down -v
```

### Перезапуск отдельного сервиса

```bash
# Перезапустить backend
docker-compose restart backend

# Пересобрать и перезапустить
docker-compose up -d --build backend
```

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f vlm-inference
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Масштабирование

```bash
# Запустить несколько реплик VLM сервиса
docker-compose up -d --scale vlm-inference=3
```

## Конфигурация

### Переменные окружения

Создайте файл `.env` на основе `.env.example`:

```bash
# VLM Inference
DEVICE=cpu          # cpu, cuda, mps
TORCH_DTYPE=float16
MAX_NEW_TOKENS=384

# Backend
REQUEST_TIMEOUT=120
```

### GPU поддержка

Для использования NVIDIA GPU:

1. Установите [NVIDIA Docker runtime](https://github.com/NVIDIA/nvidia-docker)

2. Измените в `docker-compose.yml`:
```yaml
vlm-inference:
  environment:
    - DEVICE=cuda
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

3. Перезапустите:
```bash
docker-compose up -d --build vlm-inference
```

## Volumes и данные

### Структура данных

```
Deploy/
├── ML-container/docker-volumes/
│   ├── base-model/hub/          # Базовая модель (кэш HF)
│   └── weights/                 # LoRA адаптеры
└── DB/docker-volumes/
    └── sqlite-db/               # SQLite база данных
```

### Backup базы данных

```bash
# Создать backup
docker-compose exec database sqlite3 /data/requests.db ".backup /data/backup.db"

# Копировать на хост
docker cp database:/data/backup.db ./backup_$(date +%Y%m%d).db
```

## Мониторинг

### Healthchecks

```bash
# Проверить здоровье всех сервисов
docker-compose ps

# Проверить конкретный сервис
curl http://localhost:8000/health
curl http://localhost:8002/health
curl http://localhost:8001/health
curl http://localhost:8003/health
```

### Метрики

```bash
# Backend метрики
curl http://localhost:8000/metrics

# VLM метрики
curl http://localhost:8002/metrics

# Adapter метрики
curl http://localhost:8001/metrics

# Database статистика
curl http://localhost:8003/statistics
```

## Troubleshooting

### VLM сервис не запускается

**Проблема:** Контейнер vlm-inference постоянно перезапускается

**Решение:**
1. Проверьте логи: `docker-compose logs vlm-inference`
2. Убедитесь, что веса модели на месте
3. Проверьте доступную память: `docker stats`
4. Увеличьте лимиты памяти в docker-compose.yml

### Frontend не подключается к Backend

**Проблема:** "Backend недоступен" в UI

**Решение:**
1. Проверьте, что backend запущен: `docker-compose ps backend`
2. Проверьте логи backend: `docker-compose logs backend`
3. Проверьте сеть: `docker network inspect deploy_diagram-network`

### Медленный инференс

**Проблема:** Обработка занимает >20 секунд

**Решение:**
1. Используйте GPU вместо CPU
2. Уменьшите MAX_NEW_TOKENS
3. Проверьте загрузку системы: `docker stats`

### База данных не сохраняется

**Проблема:** Данные теряются после перезапуска

**Решение:**
1. Проверьте volume: `docker volume ls`
2. Убедитесь, что путь `./DB/docker-volumes/sqlite-db` существует
3. Проверьте права доступа к директории

## Производительность

### Требования к ресурсам

| Режим | CPU | RAM | VRAM | Время |
|-------|-----|-----|------|-------|
| CPU | 4+ cores | 10 GB | - | 15-20s |
| GPU | 2+ cores | 6 GB | 8 GB | 5-10s |

### Оптимизация

1. **Кэширование**: База данных кэширует результаты по хэшу файла
2. **Параллелизм**: Запустите несколько реплик VLM сервиса
3. **GPU**: Используйте NVIDIA GPU для ускорения
4. **Квантование**: Используйте int8 квантование для экономии памяти

## Разработка

### Локальная разработка

```bash
# Запустить только зависимости
docker-compose up -d database adapter vlm-inference

# Запустить backend локально
cd backend/app
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Запустить frontend локально
cd frontend/app
pip install -r requirements.txt
streamlit run main.py
```

### Пересборка после изменений

```bash
# Пересобрать все
docker-compose build

# Пересобрать конкретный сервис
docker-compose build backend

# Пересобрать и перезапустить
docker-compose up -d --build backend
```

## Безопасность

### Рекомендации для продакшна

1. **Измените CORS** в backend на конкретные домены
2. **Добавьте аутентификацию** для API
3. **Используйте HTTPS** через reverse proxy (nginx)
4. **Ограничьте размер файлов** в backend
5. **Настройте rate limiting**
6. **Используйте secrets** для чувствительных данных

### Пример nginx конфигурации

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Обновление

### Обновление модели

```bash
# Остановить VLM сервис
docker-compose stop vlm-inference

# Обновить веса
cp new_weights/* ML-container/docker-volumes/weights/

# Перезапустить
docker-compose up -d vlm-inference
```

### Обновление кода

```bash
# Получить изменения
git pull

# Пересобрать и перезапустить
docker-compose up -d --build
```

## Поддержка

Для получения помощи:
1. Проверьте логи: `docker-compose logs`
2. Проверьте документацию каждого сервиса в соответствующих README
3. Проверьте issues в репозитории

## Лицензии

Все компоненты используют лицензии, совместимые с Apache 2.0 и MIT:
- FastAPI: MIT
- Streamlit: Apache 2.0
- Qwen3-VL: Apache 2.0
- PyTorch: BSD-3-Clause
- SQLite: Public Domain