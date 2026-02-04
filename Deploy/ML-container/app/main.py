"""
VLM Inference Service - FastAPI сервис для распознавания диаграмм
Использует Qwen3-VL-2B-Instruct с дообученными LoRA адаптерами
"""

import os
import time
import logging
from typing import Optional
from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
from io import BytesIO

from transformers import Qwen3VLForConditionalGeneration, AutoProcessor
from peft import PeftModel
from qwen_vl_utils import process_vision_info

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
BASE_MODEL_ID = os.getenv("BASE_MODEL_ID", "Qwen/Qwen3-VL-2B-Instruct")
ADAPTER_PATH = os.getenv("ADAPTER_PATH", "/app/models/weights")
DEVICE = os.getenv("DEVICE", "cpu")
TORCH_DTYPE = os.getenv("TORCH_DTYPE", "float16")
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "384"))
#os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# Глобальные переменные для модели
model = None
processor = None
model_load_time = None

# Промпт для модели
SYSTEM_PROMPT = (
    "Ты эксперт по BPMN. Выдавай ответ строго в формате Markdown-таблицы. "
    "Заголовок таблицы должен быть точно: | № | Наименование действия | Роль |."
)

# Метрики
inference_count = 0
total_inference_time = 0.0


def load_model_and_processor():
    """
    Загружает базовую модель и LoRA адаптеры при старте сервиса.
    Выполняется один раз при инициализации.
    """
    global model, processor, model_load_time
    
    logger.info("=" * 60)
    logger.info("🚀 Инициализация VLM Inference Service")
    logger.info("=" * 60)
    logger.info(f"📦 Базовая модель: {BASE_MODEL_ID}")
    logger.info(f"🔧 Адаптеры: {ADAPTER_PATH}")
    logger.info(f"💻 Устройство: {DEVICE}")
    logger.info(f"🔢 Тип данных: {TORCH_DTYPE}")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    try:
        # Определяем устройство
        if DEVICE == "cuda" and torch.cuda.is_available():
            device = torch.device("cuda")
            logger.info("✅ CUDA доступна, используем GPU")
        elif DEVICE == "mps" and torch.backends.mps.is_available():
            device = torch.device("mps")
            logger.info("✅ MPS доступна, используем Apple Silicon GPU")
        else:
            device = torch.device("cpu")
            logger.info("⚠️  Используем CPU (может быть медленно)")
        
        # Определяем dtype
        dtype = torch.float16 if TORCH_DTYPE == "float16" else torch.float32
        logger.info(f"🔢 Используем dtype: {dtype}")
        
        # 1. Загрузка базовой модели
        logger.info("⏳ Загрузка базовой модели...")
        model = Qwen3VLForConditionalGeneration.from_pretrained(
            BASE_MODEL_ID,
            torch_dtype=dtype,
            device_map="auto" if DEVICE == "cuda" else None
        )
        
        if DEVICE != "cuda":
            model = model.to(device)
        
        logger.info("✅ Базовая модель загружена")
        
        # 2. Загрузка процессора
        logger.info("⏳ Загрузка процессора...")
        try:
            # Пытаемся загрузить из адаптера (если там есть конфиг)
            processor = AutoProcessor.from_pretrained(
                ADAPTER_PATH,
                min_pixels=256*28*28,
                max_pixels=512*28*28
            )
            logger.info("✅ Процессор загружен из адаптера")
        except Exception as e:
            logger.warning(f"⚠️  Не удалось загрузить процессор из адаптера: {e}")
            processor = AutoProcessor.from_pretrained(
                BASE_MODEL_ID,
                min_pixels=256*28*28,
                max_pixels=512*28*28
            )
            logger.info("✅ Процессор загружен из базовой модели")
        
        # 3. Подключение LoRA адаптеров
        if os.path.exists(ADAPTER_PATH):
            logger.info("⏳ Подключение LoRA адаптеров...")
            try:
                model = PeftModel.from_pretrained(model, ADAPTER_PATH)
                model.eval()
                logger.info("✅ LoRA адаптеры успешно подключены")
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки LoRA адаптеров: {e}")
                logger.warning("⚠️  Продолжаем работу с базовой моделью")
        else:
            logger.warning(f"⚠️  Адаптеры не найдены в {ADAPTER_PATH}")
            logger.warning("⚠️  Работаем на базовой модели без дообучения")
        
        model_load_time = time.time() - start_time
        
        logger.info("=" * 60)
        logger.info(f"✅ Модель успешно инициализирована за {model_load_time:.2f} сек")
        logger.info("=" * 60)
        
        # Логируем использование памяти
        if torch.cuda.is_available():
            memory_allocated = torch.cuda.memory_allocated() / (1024**3)
            memory_reserved = torch.cuda.memory_reserved() / (1024**3)
            logger.info(f"💾 GPU память: {memory_allocated:.2f} GB выделено, {memory_reserved:.2f} GB зарезервировано")
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА при загрузке модели: {e}")
        logger.error("=" * 60)
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info("🔄 Запуск сервиса...")
    load_model_and_processor()
    logger.info("✅ Сервис готов к работе")
    
    yield
    
    # Shutdown
    logger.info("🛑 Остановка сервиса...")
    logger.info(f"📊 Всего обработано запросов: {inference_count}")
    if inference_count > 0:
        avg_time = total_inference_time / inference_count
        logger.info(f"⏱️  Среднее время инференса: {avg_time:.2f} сек")


# Создание FastAPI приложения
app = FastAPI(
    title="VLM Inference Service",
    description="Сервис распознавания диаграмм с использованием Qwen3-VL",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """
    Проверка здоровья сервиса
    """
    return {
        "status": "healthy" if model is not None else "initializing",
        "model_loaded": model is not None,
        "processor_loaded": processor is not None,
        "device": DEVICE,
        "model_load_time": model_load_time
    }


@app.get("/metrics")
async def get_metrics():
    """
    Получение метрик работы сервиса
    """
    avg_inference_time = (
        total_inference_time / inference_count if inference_count > 0 else 0
    )
    
    metrics = {
        "inference_count": inference_count,
        "total_inference_time": round(total_inference_time, 2),
        "avg_inference_time": round(avg_inference_time, 2),
        "model_load_time": round(model_load_time, 2) if model_load_time else None,
    }
    
    # Добавляем метрики GPU если доступно
    if torch.cuda.is_available():
        metrics["gpu_memory_allocated_gb"] = round(
            torch.cuda.memory_allocated() / (1024**3), 2
        )
        metrics["gpu_memory_reserved_gb"] = round(
            torch.cuda.memory_reserved() / (1024**3), 2
        )
    
    return metrics


@app.post("/infer")
async def infer(file: UploadFile = File(...)):
    """
    Выполняет инференс модели на загруженном изображении
    
    Args:
        file: Изображение диаграммы (PNG, JPG, JPEG)
    
    Returns:
        JSON с описанием алгоритма
    """
    global inference_count, total_inference_time
    
    if model is None or processor is None:
        logger.error("❌ Модель не загружена")
        raise HTTPException(
            status_code=503,
            detail="Модель еще не загружена, попробуйте позже"
        )
    
    # Валидация типа файла
    if not file.content_type.startswith("image/"):
        logger.warning(f"⚠️  Неверный тип файла: {file.content_type}")
        raise HTTPException(
            status_code=400,
            detail=f"Ожидается изображение, получено: {file.content_type}"
        )
    
    logger.info("=" * 60)
    logger.info(f"📥 Получен запрос на инференс")
    logger.info(f"📄 Файл: {file.filename}")
    logger.info(f"📦 Тип: {file.content_type}")
    
    try:
        # Чтение и обработка изображения
        start_time = time.time()
        
        contents = await file.read()
        image = Image.open(BytesIO(contents)).convert("RGB")
        
        logger.info(f"🖼️  Размер изображения: {image.size}")
        
        # Подготовка сообщений для модели
        messages = [{
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": SYSTEM_PROMPT}
            ]
        }]
        
        # Применение chat template
        text_input = processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Обработка vision inputs
        image_inputs, video_inputs = process_vision_info(messages)
        
        # Подготовка входных данных
        inputs = processor(
            text=[text_input],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt"
        )
        
        # Перемещаем на нужное устройство
        device = next(model.parameters()).device
        inputs = {k: v.to(device) if isinstance(v, torch.Tensor) else v 
                  for k, v in inputs.items()}
        
        logger.info("⏳ Запуск генерации...")
        generation_start = time.time()
        
        # Генерация
        with torch.inference_mode():
            generated_ids = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=False
            )
        
        generation_time = time.time() - generation_start
        logger.info(f"✅ Генерация завершена за {generation_time:.2f} сек")
        
        # Декодирование результата
        generated_ids_trimmed = [
            out_ids[len(in_ids):] 
            for in_ids, out_ids in zip(inputs["input_ids"], generated_ids)
        ]
        
        output_text = processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]
        
        total_time = time.time() - start_time
        
        # Обновление метрик
        inference_count += 1
        total_inference_time += total_time
        
        logger.info(f"✅ Инференс завершен успешно")
        logger.info(f"⏱️  Общее время: {total_time:.2f} сек")
        logger.info(f"📊 Длина ответа: {len(output_text)} символов")
        logger.info("=" * 60)
        
        return JSONResponse(
            content={
                "description": output_text,
                "metadata": {
                    "inference_time": round(total_time, 2),
                    "generation_time": round(generation_time, 2),
                    "image_size": list(image.size),
                    "model": BASE_MODEL_ID,
                    "device": str(device)
                }
            }
        )
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ Ошибка при инференсе: {e}")
        logger.error("=" * 60)
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обработке изображения: {str(e)}"
        )


@app.get("/")
async def root():
    """Корневой эндпоинт с информацией о сервисе"""
    return {
        "service": "VLM Inference Service",
        "version": "1.0.0",
        "model": BASE_MODEL_ID,
        "status": "ready" if model is not None else "initializing",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "infer": "/infer (POST)",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)