"""
Database Service - FastAPI сервис для работы с SQLite базой данных
Предоставляет API для логирования и получения статистики
"""

import os
import logging
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from database import (
    init_database,
    log_inference_request,
    get_request_by_hash,
    get_statistics,
    get_recent_requests
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Pydantic модели для валидации
class LogRequest(BaseModel):
    file_name: str
    file_type: str
    file_size: int
    file_hash: str
    was_converted: bool
    conversion_time: Optional[float] = None
    model_name: str
    device_type: str
    description: str
    inference_time: float
    generation_time: float
    total_time: float
    image_size: Optional[List[int]] = None
    max_tokens: Optional[int] = None
    torch_dtype: Optional[str] = None
    status: str = "success"
    error_message: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 Запуск Database Service")
    logger.info("=" * 60)
    
    # Инициализация базы данных
    init_database()
    
    logger.info("✅ Database Service готов к работе")
    
    yield
    
    # Shutdown
    logger.info("🛑 Остановка Database Service")


# Создание FastAPI приложения
app = FastAPI(
    title="Database Service",
    description="SQLite база данных для логирования запросов",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Корневой эндпоинт с информацией о сервисе"""
    return {
        "service": "Database Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "log": "/log (POST)",
            "statistics": "/statistics (GET)",
            "recent": "/recent (GET)",
            "health": "/health (GET)"
        }
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "database": "ready"
    }


@app.post("/log")
async def log_request(data: LogRequest):
    """
    Логирует запрос в базу данных
    
    Args:
        data: Данные запроса для логирования
    
    Returns:
        ID созданной записи
    """
    try:
        log_id = log_inference_request(
            file_name=data.file_name,
            file_type=data.file_type,
            file_size=data.file_size,
            file_hash=data.file_hash,
            was_converted=data.was_converted,
            conversion_time=data.conversion_time,
            model_name=data.model_name,
            device_type=data.device_type,
            description=data.description,
            inference_time=data.inference_time,
            generation_time=data.generation_time,
            total_time=data.total_time,
            image_size=tuple(data.image_size) if data.image_size else None,
            max_tokens=data.max_tokens,
            torch_dtype=data.torch_dtype,
            status=data.status,
            error_message=data.error_message
        )
        
        return {"id": log_id, "status": "logged"}
        
    except Exception as e:
        logger.error(f"❌ Ошибка при логировании: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при логировании: {str(e)}"
        )


@app.get("/statistics")
async def get_stats():
    """
    Получает статистику по всем запросам
    
    Returns:
        Статистика
    """
    try:
        stats = get_statistics()
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"❌ Ошибка при получении статистики: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении статистики: {str(e)}"
        )


@app.get("/recent")
async def get_recent(limit: int = 20):
    """
    Получает последние запросы
    
    Args:
        limit: Количество запросов (по умолчанию 20)
    
    Returns:
        Список последних запросов
    """
    try:
        recent = get_recent_requests(limit=limit)
        return JSONResponse(content={"requests": recent})
    except Exception as e:
        logger.error(f"❌ Ошибка при получении последних запросов: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении последних запросов: {str(e)}"
        )


@app.get("/by_hash/{file_hash}")
async def get_by_hash(file_hash: str):
    """
    Получает запрос по хэшу файла (для дедупликации)
    
    Args:
        file_hash: SHA256 хэш файла
    
    Returns:
        Данные запроса или None
    """
    try:
        result = get_request_by_hash(file_hash)
        if result:
            return JSONResponse(content=result)
        else:
            return JSONResponse(content={"found": False})
    except Exception as e:
        logger.error(f"❌ Ошибка при поиске по хэшу: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при поиске: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)