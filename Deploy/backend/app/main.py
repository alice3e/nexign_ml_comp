"""
Backend API Service - координирует работу микросервисов
Принимает файлы, определяет тип, вызывает Adapter и VLM сервисы
"""

import os
import hashlib
import logging
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
VLM_SERVICE_URL = os.getenv("VLM_SERVICE_URL", "http://localhost:8002")
ADAPTER_SERVICE_URL = os.getenv("ADAPTER_SERVICE_URL", "http://localhost:8001")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "120"))

# Поддерживаемые форматы файлов
SUPPORTED_IMAGE_FORMATS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}
SUPPORTED_DIAGRAM_FORMATS = {'.bpmn', '.puml', '.mmd', '.drawio'}
ALL_SUPPORTED_FORMATS = SUPPORTED_IMAGE_FORMATS | SUPPORTED_DIAGRAM_FORMATS

# Метрики
total_requests = 0
successful_requests = 0
failed_requests = 0


def get_file_extension(filename: str) -> str:
    """Получает расширение файла в нижнем регистре"""
    return os.path.splitext(filename)[1].lower() if filename else ''


def calculate_file_hash(content: bytes) -> str:
    """Вычисляет SHA256 хэш содержимого файла"""
    return hashlib.sha256(content).hexdigest()


async def check_service_health(service_url: str, service_name: str) -> bool:
    """Проверяет доступность сервиса"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{service_url}/health")
            if response.status_code == 200:
                logger.info(f"✅ {service_name} доступен")
                return True
            else:
                logger.warning(f"⚠️  {service_name} вернул статус {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"❌ {service_name} недоступен: {e}")
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 Запуск Backend API Service")
    logger.info("=" * 60)
    logger.info(f"🔗 VLM Service: {VLM_SERVICE_URL}")
    logger.info(f"🔗 Adapter Service: {ADAPTER_SERVICE_URL}")
    logger.info(f"⏱️  Request Timeout: {REQUEST_TIMEOUT}s")
    logger.info("=" * 60)
    
    # Проверяем доступность сервисов
    vlm_available = await check_service_health(VLM_SERVICE_URL, "VLM Service")
    adapter_available = await check_service_health(ADAPTER_SERVICE_URL, "Adapter Service")
    
    if not vlm_available:
        logger.warning("⚠️  VLM Service недоступен при старте")
    if not adapter_available:
        logger.warning("⚠️  Adapter Service недоступен при старте")
    
    logger.info("✅ Backend API готов к работе")
    
    yield
    
    # Shutdown
    logger.info("🛑 Остановка Backend API Service")
    logger.info(f"📊 Всего запросов: {total_requests}")
    logger.info(f"✅ Успешных: {successful_requests}")
    logger.info(f"❌ Ошибок: {failed_requests}")


# Создание FastAPI приложения
app = FastAPI(
    title="Backend API Service",
    description="Координирует работу сервисов распознавания диаграмм",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшне указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Корневой эндпоинт с информацией о сервисе"""
    return {
        "service": "Backend API Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "process": "/api/v1/process (POST)",
            "health": "/health (GET)",
            "metrics": "/metrics (GET)",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса и зависимостей"""
    vlm_healthy = await check_service_health(VLM_SERVICE_URL, "VLM Service")
    adapter_healthy = await check_service_health(ADAPTER_SERVICE_URL, "Adapter Service")
    
    overall_status = "healthy" if vlm_healthy else "degraded"
    
    return {
        "status": overall_status,
        "services": {
            "vlm": "healthy" if vlm_healthy else "unhealthy",
            "adapter": "healthy" if adapter_healthy else "unhealthy"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/metrics")
async def get_metrics():
    """Получение метрик работы сервиса"""
    success_rate = (
        (successful_requests / total_requests * 100) 
        if total_requests > 0 else 0
    )
    
    return {
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "failed_requests": failed_requests,
        "success_rate": round(success_rate, 2)
    }


@app.post("/api/v1/process")
async def process_diagram(file: UploadFile = File(...)):
    """
    Основной эндпоинт для обработки диаграмм
    
    Принимает файл диаграммы, определяет тип, конвертирует если нужно,
    отправляет на распознавание в VLM сервис и возвращает результат.
    
    Args:
        file: Файл диаграммы (PNG, JPG, BPMN, PlantUML, Mermaid, Draw.io)
    
    Returns:
        JSON с описанием алгоритма и метаданными
    """
    global total_requests, successful_requests, failed_requests
    
    total_requests += 1
    request_start = datetime.utcnow()
    
    logger.info("=" * 60)
    logger.info(f"📥 Получен запрос на обработку")
    logger.info(f"📄 Файл: {file.filename}")
    logger.info(f"📦 Тип: {file.content_type}")
    
    try:
        # 1. Валидация файла
        file_ext = get_file_extension(file.filename)
        
        if not file_ext:
            logger.warning("⚠️  Файл без расширения")
            raise HTTPException(
                status_code=400,
                detail="Файл должен иметь расширение"
            )
        
        if file_ext not in ALL_SUPPORTED_FORMATS:
            logger.warning(f"⚠️  Неподдерживаемый формат: {file_ext}")
            raise HTTPException(
                status_code=400,
                detail=f"Неподдерживаемый формат файла: {file_ext}. "
                       f"Поддерживаются: {', '.join(ALL_SUPPORTED_FORMATS)}"
            )
        
        logger.info(f"✅ Формат файла: {file_ext}")
        
        # 2. Чтение содержимого файла
        file_content = await file.read()
        file_size = len(file_content)
        file_hash = calculate_file_hash(file_content)
        
        logger.info(f"📊 Размер файла: {file_size / 1024:.2f} KB")
        logger.info(f"🔑 Хэш файла: {file_hash[:16]}...")
        
        # 3. Определение необходимости конвертации
        needs_conversion = file_ext in SUPPORTED_DIAGRAM_FORMATS
        
        if needs_conversion:
            logger.info(f"🔄 Требуется конвертация из {file_ext} в PNG")
            
            # Вызов Adapter Service для конвертации
            try:
                async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                    files = {"file": (file.filename, file_content, file.content_type)}
                    
                    logger.info(f"📤 Отправка в Adapter Service...")
                    response = await client.post(
                        f"{ADAPTER_SERVICE_URL}/convert",
                        files=files
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"❌ Adapter Service вернул ошибку: {response.status_code}")
                        raise HTTPException(
                            status_code=502,
                            detail=f"Ошибка конвертации: {response.text}"
                        )
                    
                    # Получаем PNG из ответа
                    png_content = response.content
                    logger.info(f"✅ Конвертация завершена, размер PNG: {len(png_content) / 1024:.2f} KB")
                    
            except httpx.TimeoutException:
                logger.error("❌ Timeout при конвертации")
                raise HTTPException(
                    status_code=504,
                    detail="Превышено время ожидания конвертации"
                )
            except httpx.RequestError as e:
                logger.error(f"❌ Ошибка соединения с Adapter Service: {e}")
                raise HTTPException(
                    status_code=503,
                    detail="Adapter Service недоступен"
                )
        else:
            logger.info("✅ Файл уже в формате изображения, конвертация не требуется")
            png_content = file_content
        
        # 4. Отправка в VLM Service для распознавания
        logger.info("📤 Отправка в VLM Service для распознавания...")
        
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                files = {"file": ("diagram.png", png_content, "image/png")}
                
                response = await client.post(
                    f"{VLM_SERVICE_URL}/infer",
                    files=files
                )
                
                if response.status_code != 200:
                    logger.error(f"❌ VLM Service вернул ошибку: {response.status_code}")
                    raise HTTPException(
                        status_code=502,
                        detail=f"Ошибка распознавания: {response.text}"
                    )
                
                result = response.json()
                logger.info("✅ Распознавание завершено успешно")
                
        except httpx.TimeoutException:
            logger.error("❌ Timeout при распознавании")
            raise HTTPException(
                status_code=504,
                detail="Превышено время ожидания распознавания"
            )
        except httpx.RequestError as e:
            logger.error(f"❌ Ошибка соединения с VLM Service: {e}")
            raise HTTPException(
                status_code=503,
                detail="VLM Service недоступен"
            )
        
        # 5. Формирование ответа
        request_end = datetime.utcnow()
        processing_time = (request_end - request_start).total_seconds()
        
        successful_requests += 1
        
        response_data = {
            "description": result.get("description", ""),
            "metadata": {
                "file_name": file.filename,
                "file_type": file_ext,
                "file_size_kb": round(file_size / 1024, 2),
                "file_hash": file_hash,
                "converted": needs_conversion,
                "processing_time": round(processing_time, 2),
                "timestamp": request_end.isoformat(),
                **result.get("metadata", {})
            }
        }
        
        logger.info(f"✅ Запрос обработан успешно за {processing_time:.2f} сек")
        logger.info("=" * 60)
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        failed_requests += 1
        raise
    except Exception as e:
        failed_requests += 1
        logger.error("=" * 60)
        logger.error(f"❌ Неожиданная ошибка: {e}")
        logger.error("=" * 60)
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)