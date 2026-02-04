# План миграции VLM модели в микросервисную архитектуру

## 1. Анализ текущей реализации

### 1.1 Как работает VLM инференс

Из анализа кода в `nexign_ml_comp-sasha/` выявлено:

**Базовая модель:**
- Используется `Qwen3-VL-2B-Instruct` от HuggingFace
- Модель загружается через `Qwen3VLForConditionalGeneration.from_pretrained()`
- Поддерживает работу на CPU, GPU и MPS (Apple Silicon)

**Дообученные веса (LoRA адаптеры):**
- Находятся в `nexign_ml_comp-sasha/model_vlm_qwen3/weights.zip`
- Подключаются через библиотеку `peft` (Parameter-Efficient Fine-Tuning)
- Используется `PeftModel.from_pretrained(base_model, adapter_path)`
- Адаптеры накладываются поверх базовой модели, не заменяя её полностью

**Процесс инференса:**
```python
# 1. Загрузка базовой модели
model = Qwen3VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen3-VL-2B-Instruct",
    torch_dtype=torch.float16
)

# 2. Подключение LoRA адаптеров
model = PeftModel.from_pretrained(model, "path/to/weights")

# 3. Загрузка процессора (токенизатор + image processor)
processor = AutoProcessor.from_pretrained(adapter_path_or_base)

# 4. Подготовка входных данных
messages = [{
    "role": "user",
    "content": [
        {"type": "image", "image": pil_image},
        {"type": "text", "text": prompt}
    ]
}]

# 5. Обработка через процессор
text = processor.apply_chat_template(messages, tokenize=False)
image_inputs, video_inputs = process_vision_info(messages)
inputs = processor(text=[text], images=image_inputs, padding=True, return_tensors="pt")

# 6. Генерация
with torch.inference_mode():
    outputs = model.generate(**inputs, max_new_tokens=384, do_sample=False)

# 7. Декодирование результата
result = processor.batch_decode(outputs, skip_special_tokens=True)[0]
```

**Ключевые зависимости:**
- `transformers>=4.49.0` - для работы с моделью
- `torch>=2.10.0` - PyTorch
- `peft>=0.18.1` - для LoRA адаптеров
- `qwen-vl-utils>=0.0.14` - утилиты для обработки vision inputs
- `pillow>=12.1.0` - работа с изображениями
- `accelerate>=0.26.0` - оптимизация загрузки моделей

### 1.2 Особенности работы с весами

**Структура весов:**
- Базовая модель (~4-5 GB) скачивается из HuggingFace Hub
- LoRA адаптеры (~50-200 MB) хранятся локально в `weights/`
- Адаптеры содержат только дельты весов, не полную модель

**Требования к ресурсам:**
- GPU: RTX 5060 8GB - инференс ~5-10 сек
- CPU: с квантованием - до 20 сек
- RAM: ~8 GB для модели + overhead

## 2. Микросервисная архитектура

### 2.1 Компоненты системы

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  UI Service │ (Nginx + Static HTML/JS)
│  Port: 80   │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  Backend API        │ (FastAPI)
│  Port: 8000         │
│  - Координация      │
│  - Валидация        │
│  - Логирование      │
└──────┬──────────────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌─────────────┐   ┌──────────────┐
│  Adapter    │   │ VLM Inference│
│  Service    │   │   Service    │
│  Port: 8001 │   │  Port: 8002  │
│             │   │              │
│ - BPMN→PNG  │   │ - Qwen3-VL   │
│ - PlantUML  │   │ - LoRA       │
│ - Mermaid   │   │ - Генерация  │
│ - Draw.io   │   │   описаний   │
└─────────────┘   └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Model Weights│
                  │   (Volume)   │
                  │              │
                  │ - Base model │
                  │ - LoRA adapt │
                  └──────────────┘
```

### 2.2 VLM Inference Service - детальный дизайн

**Ответственность:**
- Загрузка и инициализация модели при старте
- Прием PNG изображений через REST API
- Выполнение инференса
- Возврат текстового описания

**API эндпоинты:**
```
POST /inference
  - Input: multipart/form-data с полем "image" (PNG/JPG)
  - Output: {"description": "текст описания алгоритма"}
  - Timeout: 25 секунд

GET /health
  - Output: {"status": "ready", "model_loaded": true}

GET /metrics
  - Output: {"latency_avg": 7.5, "memory_mb": 6800, "requests_total": 42}
```

**Dockerfile стратегия:**
```dockerfile
FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода сервиса
COPY vlm_service/ /app/
WORKDIR /app

# Volume для весов модели
VOLUME ["/app/models"]

# Переменные окружения
ENV MODEL_BASE_PATH=/app/models/base
ENV MODEL_ADAPTER_PATH=/app/models/weights
ENV DEVICE=cpu
ENV TORCH_DTYPE=float16

EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
```

**Управление весами:**
1. **Базовая модель** - скачивается при первом запуске или предзагружается в образ
2. **LoRA адаптеры** - монтируются через volume из распакованного `weights.zip`
3. **Кэширование** - HuggingFace cache в `/root/.cache/huggingface`

### 2.3 Backend API Service

**Ответственность:**
- Прием файлов от клиента
- Определение типа файла и маршрутизация
- Вызов Adapter Service при необходимости
- Вызов VLM Inference Service
- Логирование в БД
- Возврат результата клиенту

**Логика обработки:**
```python
async def process_diagram(file: UploadFile):
    # 1. Определить тип файла
    file_type = detect_file_type(file)
    
    # 2. Конвертация если нужно
    if file_type in ['bpmn', 'puml', 'mmd', 'drawio']:
        png_data = await adapter_service.convert(file, file_type)
    else:
        png_data = await file.read()
    
    # 3. Вызов VLM
    result = await vlm_service.infer(png_data)
    
    # 4. Логирование
    await db.log_request(file_hash, result, metadata)
    
    # 5. Возврат
    return {"description": result}
```

### 2.4 Adapter Service

**Ответственность:**
- Конвертация различных форматов диаграмм в PNG
- Поддержка BPMN, PlantUML, Mermaid, Draw.io

**Технологии:**
- Python FastAPI
- `plantweb` для PlantUML
- `mermaid-cli` (Node.js) для Mermaid
- `bpmn-js` + Puppeteer для BPMN
- `drawio` CLI для Draw.io

### 2.5 UI Service

**Ответственность:**
- Простой веб-интерфейс для демонстрации
- Форма загрузки файла
- Отображение результата

**Технологии:**
- Статический HTML/CSS/JavaScript
- Bootstrap для UI
- Nginx для раздачи статики

## 3. Docker Compose конфигурация

### 3.1 Структура volumes

```yaml
volumes:
  model_cache:
    # HuggingFace cache для базовой модели
  model_weights:
    # LoRA адаптеры
  db_data:
    # SQLite база данных
```

### 3.2 Сервисы

```yaml
services:
  backend:
    build: ./services/backend
    ports:
      - "8000:8000"
    depends_on:
      - vlm-inference
      - adapter
    environment:
      - VLM_SERVICE_URL=http://vlm-inference:8002
      - ADAPTER_SERVICE_URL=http://adapter:8001
  
  vlm-inference:
    build: ./services/vlm_inference
    ports:
      - "8002:8002"
    volumes:
      - model_cache:/root/.cache/huggingface
      - ./nexign_ml_comp-sasha/model_vlm_qwen3/weights:/app/models/weights:ro
    environment:
      - DEVICE=cpu  # или cuda для GPU
      - TORCH_DTYPE=float16
    deploy:
      resources:
        limits:
          memory: 10G
        reservations:
          memory: 8G
  
  adapter:
    build: ./services/adapter
    ports:
      - "8001:8001"
  
  ui:
    build: ./services/ui
    ports:
      - "80:80"
    depends_on:
      - backend
```

## 4. План реализации

### Этап 1: Подготовка структуры проекта
- [ ] Создать директории для каждого сервиса
- [ ] Распаковать `weights.zip` в нужное место
- [ ] Создать базовые Dockerfile для каждого сервиса

### Этап 2: VLM Inference Service
- [ ] Портировать логику из `inference.py` в FastAPI приложение
- [ ] Реализовать эндпоинты `/infer`, `/health`, `/metrics`
- [ ] Настроить загрузку модели и адаптеров
- [ ] Добавить обработку ошибок и таймауты
- [ ] Создать requirements.txt с зависимостями

### Этап 3: Backend API Service
- [ ] Создать FastAPI приложение с эндпоинтом `/api/v1/process`
- [ ] Реализовать логику определения типа файла
- [ ] Добавить HTTP клиенты для вызова других сервисов
- [ ] Настроить логирование в SQLite
- [ ] Добавить Swagger документацию

### Этап 4: Adapter Service
- [ ] Реализовать базовый FastAPI сервис
- [ ] Добавить конвертеры для каждого формата
- [ ] Настроить зависимости (Node.js, Java если нужно)

### Этап 5: UI Service
- [ ] Создать простой HTML интерфейс
- [ ] Добавить форму загрузки файла
- [ ] Реализовать отображение результата
- [ ] Настроить Nginx конфигурацию

### Этап 6: Docker Compose
- [ ] Создать docker-compose.yml
- [ ] Настроить volumes для весов модели
- [ ] Настроить сеть между сервисами
- [ ] Добавить healthchecks

### Этап 7: Документация и тестирование
- [ ] Написать README с инструкциями по запуску
- [ ] Создать примеры запросов
- [ ] Протестировать на CPU и GPU
- [ ] Измерить метрики производительности

## 5. Ключевые технические решения

### 5.1 Управление весами модели

**Проблема:** Базовая модель ~4-5 GB, нужно избежать дублирования в каждом контейнере.

**Решение:**
1. Использовать Docker volume для HuggingFace cache
2. При первом запуске модель скачивается в volume
3. Последующие запуски используют кэшированную модель
4. LoRA адаптеры монтируются read-only из хоста

### 5.2 Оптимизация производительности

**CPU режим:**
- Использовать `torch.float16` для уменьшения памяти
- Рассмотреть квантование до int8 через `bitsandbytes`
- Установить `torch.set_num_threads()` для оптимального использования ядер

**GPU режим:**
- Использовать `device_map="auto"` для автоматического размещения
- Настроить CUDA_VISIBLE_DEVICES в docker-compose

### 5.3 Масштабируемость

**Горизонтальное масштабирование:**
- VLM Inference Service - stateless, можно запустить несколько реплик
- Backend добавить балансировку между репликами VLM
- Использовать Redis для кэширования результатов по хэшу изображения

**Вертикальное масштабирование:**
- Увеличить лимиты памяти в docker-compose
- Использовать более мощный GPU

## 6. Риски и митигация

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Модель не помещается в 8GB GPU | Средняя | Высокое | Использовать квантование, уменьшить batch size |
| Долгая загрузка модели при старте | Высокая | Среднее | Использовать readiness probe, показывать статус загрузки |
| Несовместимость версий transformers | Средняя | Высокое | Зафиксировать версии в requirements.txt |
| Веса адаптеров повреждены | Низкая | Высокое | Добавить валидацию при загрузке, fallback на базовую модель |

## 7. Следующие шаги

1. Распаковать `weights.zip` и изучить структуру
2. Создать минимальный VLM Inference Service
3. Протестировать загрузку модели и инференс
4. Постепенно добавлять остальные компоненты