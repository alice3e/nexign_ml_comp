"""
Adapter Service - сервис конвертации диаграмм в PNG
Пока поддерживает только изображения (pass-through)
Заглушки для BPMN, PlantUML, Mermaid, Draw.io
"""

import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import Response

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Поддерживаемые форматы
SUPPORTED_IMAGE_FORMATS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}
SUPPORTED_DIAGRAM_FORMATS = {'.bpmn', '.puml', '.mmd', '.drawio'}
ALL_SUPPORTED_FORMATS = SUPPORTED_IMAGE_FORMATS | SUPPORTED_DIAGRAM_FORMATS

# Метрики
total_conversions = 0
successful_conversions = 0
failed_conversions = 0


def get_file_extension(filename: str) -> str:
    """Получает расширение файла в нижнем регистре"""
    return os.path.splitext(filename)[1].lower() if filename else ''


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 Запуск Adapter Service")
    logger.info("=" * 60)
    logger.info(f"📁 Поддерживаемые изображения: {', '.join(SUPPORTED_IMAGE_FORMATS)}")
    logger.info(f"📊 Форматы диаграмм (TODO): {', '.join(SUPPORTED_DIAGRAM_FORMATS)}")
    logger.info("=" * 60)
    logger.info("✅ Adapter Service готов к работе")
    
    yield
    
    # Shutdown
    logger.info("🛑 Остановка Adapter Service")
    logger.info(f"📊 Всего конвертаций: {total_conversions}")
    logger.info(f"✅ Успешных: {successful_conversions}")
    logger.info(f"❌ Ошибок: {failed_conversions}")


# Создание FastAPI приложения
app = FastAPI(
    title="Adapter Service",
    description="Сервис конвертации диаграмм в PNG формат",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Корневой эндпоинт с информацией о сервисе"""
    return {
        "service": "Adapter Service",
        "version": "1.0.0",
        "status": "running",
        "supported_formats": {
            "images": list(SUPPORTED_IMAGE_FORMATS),
            "diagrams_todo": list(SUPPORTED_DIAGRAM_FORMATS)
        },
        "endpoints": {
            "convert": "/convert (POST)",
            "health": "/health (GET)",
            "metrics": "/metrics (GET)",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "converters": {
            "images": "ready",
            "bpmn": "not_implemented",
            "plantuml": "not_implemented",
            "mermaid": "not_implemented",
            "drawio": "not_implemented"
        }
    }


@app.get("/metrics")
async def get_metrics():
    """Получение метрик работы сервиса"""
    success_rate = (
        (successful_conversions / total_conversions * 100) 
        if total_conversions > 0 else 0
    )
    
    return {
        "total_conversions": total_conversions,
        "successful_conversions": successful_conversions,
        "failed_conversions": failed_conversions,
        "success_rate": round(success_rate, 2)
    }


@app.post("/convert")
async def convert_diagram(file: UploadFile = File(...)):
    """
    Конвертирует диаграмму в PNG формат
    
    Текущая реализация:
    - Изображения (PNG, JPG, etc.) - pass-through (возвращает как есть)
    - Диаграммы (BPMN, PlantUML, etc.) - заглушка (возвращает ошибку)
    
    Args:
        file: Файл диаграммы
    
    Returns:
        PNG изображение
    """
    global total_conversions, successful_conversions, failed_conversions
    
    total_conversions += 1
    
    logger.info("=" * 60)
    logger.info(f"📥 Получен запрос на конвертацию")
    logger.info(f"📄 Файл: {file.filename}")
    logger.info(f"📦 Тип: {file.content_type}")
    
    try:
        # Определяем расширение файла
        file_ext = get_file_extension(file.filename)
        
        if not file_ext:
            logger.warning("⚠️  Файл без расширения")
            failed_conversions += 1
            raise HTTPException(
                status_code=400,
                detail="Файл должен иметь расширение"
            )
        
        logger.info(f"🔍 Расширение: {file_ext}")
        
        # Проверяем поддерживаемые форматы
        if file_ext not in ALL_SUPPORTED_FORMATS:
            logger.warning(f"⚠️  Неподдерживаемый формат: {file_ext}")
            failed_conversions += 1
            raise HTTPException(
                status_code=400,
                detail=f"Неподдерживаемый формат: {file_ext}. "
                       f"Поддерживаются: {', '.join(ALL_SUPPORTED_FORMATS)}"
            )
        
        # Читаем содержимое файла
        content = await file.read()
        file_size = len(content)
        
        logger.info(f"📊 Размер файла: {file_size / 1024:.2f} KB")
        
        # Обработка изображений (pass-through)
        if file_ext in SUPPORTED_IMAGE_FORMATS:
            logger.info("✅ Изображение - pass-through (без конвертации)")
            successful_conversions += 1
            logger.info("=" * 60)
            
            # Возвращаем изображение как есть
            return Response(
                content=content,
                media_type="image/png",
                headers={
                    "X-Conversion-Type": "pass-through",
                    "X-Original-Format": file_ext,
                    "X-File-Size": str(file_size)
                }
            )
        
        # Обработка диаграмм (заглушка)
        elif file_ext in SUPPORTED_DIAGRAM_FORMATS:
            logger.warning(f"⚠️  Конвертация {file_ext} еще не реализована")
            failed_conversions += 1
            logger.info("=" * 60)
            
            raise HTTPException(
                status_code=501,
                detail=f"Конвертация {file_ext} в PNG пока не реализована. "
                       f"Используйте изображения: {', '.join(SUPPORTED_IMAGE_FORMATS)}"
            )
        
        else:
            # Не должно сюда попасть, но на всякий случай
            logger.error(f"❌ Неожиданный формат: {file_ext}")
            failed_conversions += 1
            logger.info("=" * 60)
            
            raise HTTPException(
                status_code=500,
                detail=f"Внутренняя ошибка при обработке {file_ext}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        failed_conversions += 1
        logger.error("=" * 60)
        logger.error(f"❌ Неожиданная ошибка: {e}")
        logger.error("=" * 60)
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при конвертации: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)