"""
Database module для логирования запросов и результатов
Использует SQLite для простоты и портативности
"""

import os
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import json
import logging

logger = logging.getLogger(__name__)

# Путь к базе данных
DB_PATH = os.getenv("DB_PATH", "/app/data/requests.db")


def init_database():
    """
    Инициализирует базу данных и создает таблицы если их нет
    """
    # Создаем директорию для БД если не существует
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Создаем таблицу для логирования запросов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inference_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- Информация о запросе
            request_timestamp TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size_bytes INTEGER NOT NULL,
            file_hash TEXT NOT NULL,
            
            -- Информация о конвертации
            was_converted BOOLEAN NOT NULL,
            conversion_time_sec REAL,
            
            -- Информация о модели
            model_name TEXT NOT NULL,
            device_type TEXT NOT NULL,
            
            -- Параметры инференса
            max_tokens INTEGER,
            torch_dtype TEXT,
            
            -- Результаты
            description_text TEXT NOT NULL,
            description_length INTEGER NOT NULL,
            
            -- Метрики производительности
            inference_time_sec REAL NOT NULL,
            generation_time_sec REAL NOT NULL,
            total_processing_time_sec REAL NOT NULL,
            
            -- Информация об изображении
            image_width INTEGER,
            image_height INTEGER,
            
            -- Статус
            status TEXT NOT NULL,
            error_message TEXT,
            
            -- Дополнительные метаданные (JSON)
            metadata TEXT,
            
            -- Индексы для быстрого поиска
            UNIQUE(file_hash, request_timestamp)
        )
    """)
    
    # Создаем индексы для оптимизации запросов
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_file_hash 
        ON inference_logs(file_hash)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp 
        ON inference_logs(request_timestamp)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_status 
        ON inference_logs(status)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_model_device 
        ON inference_logs(model_name, device_type)
    """)
    
    conn.commit()
    conn.close()
    
    logger.info(f"✅ База данных инициализирована: {DB_PATH}")


@contextmanager
def get_db_connection():
    """
    Context manager для работы с БД
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Для доступа к колонкам по имени
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Ошибка БД: {e}")
        raise
    finally:
        conn.close()


def log_inference_request(
    file_name: str,
    file_type: str,
    file_size: int,
    file_hash: str,
    was_converted: bool,
    conversion_time: Optional[float],
    model_name: str,
    device_type: str,
    description: str,
    inference_time: float,
    generation_time: float,
    total_time: float,
    image_size: Optional[tuple],
    max_tokens: Optional[int] = None,
    torch_dtype: Optional[str] = None,
    status: str = "success",
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """
    Логирует запрос на инференс в базу данных
    
    Returns:
        ID созданной записи
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Подготавливаем данные
            timestamp = datetime.utcnow().isoformat()
            description_length = len(description) if description else 0
            image_width = image_size[0] if image_size else None
            image_height = image_size[1] if image_size else None
            metadata_json = json.dumps(metadata) if metadata else None
            
            # Вставляем запись
            cursor.execute("""
                INSERT INTO inference_logs (
                    request_timestamp, file_name, file_type, file_size_bytes, file_hash,
                    was_converted, conversion_time_sec,
                    model_name, device_type,
                    max_tokens, torch_dtype,
                    description_text, description_length,
                    inference_time_sec, generation_time_sec, total_processing_time_sec,
                    image_width, image_height,
                    status, error_message, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp, file_name, file_type, file_size, file_hash,
                was_converted, conversion_time,
                model_name, device_type,
                max_tokens, torch_dtype,
                description, description_length,
                inference_time, generation_time, total_time,
                image_width, image_height,
                status, error_message, metadata_json
            ))
            
            log_id = cursor.lastrowid
            
            logger.info(f"📝 Запрос залогирован в БД (ID: {log_id})")
            return log_id
            
    except Exception as e:
        logger.error(f"❌ Ошибка при логировании в БД: {e}")
        # Не прерываем работу если логирование не удалось
        return -1


def get_request_by_hash(file_hash: str) -> Optional[Dict[str, Any]]:
    """
    Получает последний запрос с таким же хэшем файла (для дедупликации)
    
    Returns:
        Словарь с данными запроса или None если не найдено
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM inference_logs 
                WHERE file_hash = ? AND status = 'success'
                ORDER BY request_timestamp DESC 
                LIMIT 1
            """, (file_hash,))
            
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
            
    except Exception as e:
        logger.error(f"❌ Ошибка при поиске по хэшу: {e}")
        return None


def get_statistics() -> Dict[str, Any]:
    """
    Получает статистику по всем запросам
    
    Returns:
        Словарь со статистикой
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Общая статистика
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed,
                    AVG(total_processing_time_sec) as avg_processing_time,
                    AVG(inference_time_sec) as avg_inference_time,
                    AVG(generation_time_sec) as avg_generation_time,
                    MIN(total_processing_time_sec) as min_processing_time,
                    MAX(total_processing_time_sec) as max_processing_time
                FROM inference_logs
            """)
            
            stats = dict(cursor.fetchone())
            
            # Статистика по устройствам
            cursor.execute("""
                SELECT 
                    device_type,
                    COUNT(*) as count,
                    AVG(inference_time_sec) as avg_time
                FROM inference_logs
                WHERE status = 'success'
                GROUP BY device_type
            """)
            
            stats['by_device'] = [dict(row) for row in cursor.fetchall()]
            
            # Статистика по моделям
            cursor.execute("""
                SELECT 
                    model_name,
                    COUNT(*) as count,
                    AVG(inference_time_sec) as avg_time
                FROM inference_logs
                WHERE status = 'success'
                GROUP BY model_name
            """)
            
            stats['by_model'] = [dict(row) for row in cursor.fetchall()]
            
            # Статистика по типам файлов
            cursor.execute("""
                SELECT 
                    file_type,
                    COUNT(*) as count,
                    SUM(CASE WHEN was_converted THEN 1 ELSE 0 END) as converted_count
                FROM inference_logs
                GROUP BY file_type
            """)
            
            stats['by_file_type'] = [dict(row) for row in cursor.fetchall()]
            
            return stats
            
    except Exception as e:
        logger.error(f"❌ Ошибка при получении статистики: {e}")
        return {}


def get_recent_requests(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Получает последние N запросов
    
    Args:
        limit: Количество запросов
        
    Returns:
        Список словарей с данными запросов
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    id, request_timestamp, file_name, file_type,
                    model_name, device_type, status,
                    total_processing_time_sec, description_length
                FROM inference_logs
                ORDER BY request_timestamp DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
            
    except Exception as e:
        logger.error(f"❌ Ошибка при получении последних запросов: {e}")
        return []


def cleanup_old_records(days: int = 30):
    """
    Удаляет записи старше указанного количества дней
    
    Args:
        days: Количество дней для хранения
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cutoff_date = datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
            cutoff_str = cutoff_date.isoformat()
            
            cursor.execute("""
                DELETE FROM inference_logs
                WHERE request_timestamp < ?
            """, (cutoff_str,))
            
            deleted_count = cursor.rowcount
            
            logger.info(f"🗑️  Удалено {deleted_count} старых записей (старше {days} дней)")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке старых записей: {e}")