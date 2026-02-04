# VLM Inference Service

Микросервис для распознавания диаграмм с использованием Qwen3-VL-2B-Instruct с дообученными LoRA адаптерами.

## Структура

```
ML-container/
├── app/
│   ├── main.py              # FastAPI приложение
│   └── requirements.txt     # Python зависимости
├── docker-volumes/
│   ├── base-model/
│   │   └── download_qwen3.py  # Скрипт загрузки базовой модели
│   └── weights/             # LoRA адаптеры (монтируется в контейнер)
│       ├── adapter_config.json
│       ├── adapter_model.safetensors
│       ├── chat_template.jinja
│       ├── params.json
│       ├── processor_config.json
│       ├── tokenizer_config.json
│       └── tokenizer.json
├── Dockerfile
├── .dockerignore
└── README.md
```

## Подготовка к запуску

### 1. Загрузка базовой модели

Базовая модель Qwen3-VL-2B-Instruct (~4-5 GB) будет автоматически загружена при первом запуске контейнера из HuggingFace Hub. Модель кэшируется в Docker volume для переиспользования.

Если хотите предварительно загрузить модель:

```bash
cd docker-volumes/base-model
pip install huggingface-hub
python download_qwen3.py
```

### 2. Проверка LoRA адаптеров

Убедитесь, что в `docker-volumes/weights/` находятся файлы адаптеров:
- `adapter_config.json`
- `adapter_model.safetensors`
- `processor_config.json`
- `tokenizer_config.json`
- и другие

## Сборка образа

```bash
docker build -t vlm-inference:latest .
```

## Запуск контейнера

### Автоматический выбор устройства

Сервис автоматически определяет доступное устройство:
- Если указан `DEVICE=cuda` и CUDA доступна → использует GPU
- Если указан `DEVICE=mps` и MPS доступна (Mac M1/M2/M3) → использует Apple Silicon
- Если устройство недоступно или указан `DEVICE=cpu` → fallback на CPU

**Важно:** Для GPU нужно добавить `--gpus all`, иначе контейнер не увидит GPU!

### CPU режим (fallback, работает везде)

```bash
docker run -d \
  --name vlm-inference \
  -p 8002:8002 \
  -v $(pwd)/docker-volumes/weights:/app/models/weights:ro \
  -v $(pwd)/docker-volumes/base-model:/root/.cache/huggingface \
  -e DEVICE=cpu \
  -e TORCH_DTYPE=float16 \
  vlm-inference:latest
```

### GPU режим (NVIDIA CUDA)

```bash
docker run -d \
  --name vlm-inference \
  --gpus all \
  -p 8002:8002 \
  -v $(pwd)/docker-volumes/weights:/app/models/weights:ro \
  -v $(pwd)/docker-volumes/base-model:/root/.cache/huggingface \
  -e DEVICE=cuda \
  -e TORCH_DTYPE=float16 \
  vlm-inference:latest
```

**Примечание:** Требуется NVIDIA Docker runtime. Установка:
```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### Apple Silicon (MPS, тестирование на Mac)

```bash
docker run -d \
  --name vlm-inference \
  -p 8002:8002 \
  -v $(pwd)/docker-volumes/weights:/app/models/weights:ro \
  -v $(pwd)/docker-volumes/base-model:/root/.cache/huggingface \
  -e DEVICE=mps \
  -e TORCH_DTYPE=float16 \
  vlm-inference:latest
```

**Примечание:** Требуется Docker Desktop для Mac с поддержкой MPS (экспериментальная функция).

## Переменные окружения

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| `BASE_MODEL_ID` | ID модели на HuggingFace | `Qwen/Qwen3-VL-2B-Instruct` |
| `ADAPTER_PATH` | Путь к LoRA адаптерам | `/app/models/weights` |
| `DEVICE` | Устройство для инференса (`cpu`/`cuda`/`mps`) | `cpu` |
| `TORCH_DTYPE` | Тип данных PyTorch (`float16`/`float32`) | `float16` |
| `MAX_NEW_TOKENS` | Максимум токенов генерации | `384` |
| `HF_HOME` | Директория кэша HuggingFace | `/root/.cache/huggingface` |

## API Endpoints

### POST /infer

Выполняет инференс на изображении диаграммы.

**Request:**
```bash
curl -X POST "http://localhost:8002/infer" \
  -F "file=@diagram.png"
```

**Response:**
```json
{
  "description": "| № | Наименование действия | Роль |\n|---|---|---|\n| 1 | Начало процесса | Система |",
  "metadata": {
    "inference_time": 7.52,
    "generation_time": 6.89,
    "image_size": [1024, 768],
    "model": "Qwen/Qwen3-VL-2B-Instruct",
    "device": "cpu"
  }
}
```

### GET /health

Проверка здоровья сервиса.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "processor_loaded": true,
  "device": "cpu",
  "model_load_time": 45.23
}
```

### GET /metrics

Получение метрик работы сервиса.

**Response:**
```json
{
  "inference_count": 42,
  "total_inference_time": 315.84,
  "avg_inference_time": 7.52,
  "model_load_time": 45.23,
  "gpu_memory_allocated_gb": 5.8,
  "gpu_memory_reserved_gb": 6.2
}
```

### GET /

Информация о сервисе.

### GET /docs

Swagger UI документация (автоматически генерируется FastAPI).

## Логирование

Сервис использует структурированное логирование с уровнями:
- **INFO** - нормальная работа, метрики
- **WARNING** - предупреждения (например, адаптеры не найдены)
- **ERROR** - ошибки при обработке запросов

Просмотр логов:
```bash
docker logs -f vlm-inference
```

## Производительность

### Требования к ресурсам

| Режим | RAM | VRAM | Время инференса |
|-------|-----|------|-----------------|
| CPU (float16) | ~8 GB | - | 15-20 сек |
| GPU (float16) | ~4 GB | ~6 GB | 5-10 сек |
| MPS (float16) | ~6 GB | - | 8-12 сек |
| GPU (int8 квантование) | ~3 GB | ~4 GB | 7-12 сек |

### Оптимизация

**Для CPU:**
- Используйте `TORCH_DTYPE=float16` для уменьшения памяти
- Рассмотрите квантование до int8 через `bitsandbytes`
- Установите `OMP_NUM_THREADS` для оптимального использования ядер

**Для GPU:**
- Используйте `DEVICE=cuda` и `--gpus all`
- Для GPU с памятью <8GB рассмотрите квантование
- Используйте `torch.compile()` для ускорения (требует PyTorch 2.0+)

**Для Apple Silicon:**
- Используйте `DEVICE=mps`
- MPS работает быстрее CPU, но медленнее CUDA
- Убедитесь, что используете последнюю версию PyTorch с поддержкой MPS

## Troubleshooting

### Модель не загружается

**Проблема:** Ошибка при загрузке модели из HuggingFace Hub.

**Решение:**
1. Проверьте интернет-соединение
2. Убедитесь в наличии свободного места (~5 GB)
3. Если модель приватная, установите `HF_TOKEN`:
   ```bash
   docker run -e HF_TOKEN=your_token ...
   ```

### GPU не обнаружен

**Проблема:** Указан `DEVICE=cuda`, но используется CPU.

**Решение:**
1. Убедитесь, что добавили `--gpus all` в docker run
2. Проверьте, что NVIDIA Docker runtime установлен:
   ```bash
   docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
   ```
3. Проверьте драйверы NVIDIA на хосте:
   ```bash
   nvidia-smi
   ```

### Out of Memory (OOM)

**Проблема:** Недостаточно памяти для загрузки модели.

**Решение:**
1. Уменьшите `MAX_NEW_TOKENS`
2. Используйте квантование (int8)
3. Увеличьте лимиты памяти Docker:
   ```bash
   docker run --memory=10g ...
   ```

### Медленный инференс

**Проблема:** Инференс занимает >20 секунд.

**Решение:**
1. Используйте GPU вместо CPU (`DEVICE=cuda` + `--gpus all`)
2. Проверьте, что используется `float16` а не `float32`
3. Уменьшите размер входного изображения
4. Проверьте загрузку системы (`htop`, `nvidia-smi`)

### LoRA адаптеры не загружаются

**Проблема:** Предупреждение "Адаптеры не найдены".

**Решение:**
1. Проверьте, что volume правильно смонтирован:
   ```bash
   docker exec vlm-inference ls -la /app/models/weights
   ```
2. Убедитесь, что файлы адаптеров присутствуют
3. Проверьте права доступа к файлам

## Мониторинг

### Healthcheck

Docker автоматически проверяет здоровье контейнера каждые 30 секунд:

```bash
docker ps  # Смотрим статус в колонке STATUS
```

### Метрики

Получение метрик через API:
```bash
curl http://localhost:8002/metrics
```

### Prometheus (опционально)

Для интеграции с Prometheus добавьте экспортер метрик (TODO).

## Масштабирование

### Горизонтальное

Запустите несколько реплик сервиса:

```bash
docker run -d --name vlm-inference-1 --gpus '"device=0"' -p 8002:8002 ...
docker run -d --name vlm-inference-2 --gpus '"device=1"' -p 8003:8002 ...
docker run -d --name vlm-inference-3 --gpus '"device=2"' -p 8004:8002 ...
```

Используйте балансировщик нагрузки (nginx, traefik) для распределения запросов.

### Вертикальное

Увеличьте ресурсы контейнера:

```bash
docker run -d \
  --cpus=8 \
  --memory=16g \
  --gpus all \
  ...
```

## Интеграция с docker-compose

См. корневой `docker-compose.yml` для интеграции с другими сервисами.