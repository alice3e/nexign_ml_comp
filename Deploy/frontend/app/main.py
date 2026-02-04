"""
Frontend UI Service - Streamlit интерфейс для загрузки диаграмм
Простой и удобный веб-интерфейс для демонстрации возможностей сервиса
"""

import os
import requests
import streamlit as st
from datetime import datetime
from typing import Optional, Dict, Any

# Конфигурация
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_ENDPOINT = f"{BACKEND_URL}/api/v1/process"
STATISTICS_ENDPOINT = f"{BACKEND_URL}/api/v1/statistics"
RECENT_ENDPOINT = f"{BACKEND_URL}/api/v1/recent"

# Поддерживаемые форматы
SUPPORTED_FORMATS = [
    "png", "jpg", "jpeg", "gif", "bmp",  # Изображения
    "bpmn", "puml", "mmd", "drawio"      # Диаграммы
]

# Настройка страницы
st.set_page_config(
    page_title="Распознавание диаграмм",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Кастомный CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)


def check_backend_health() -> bool:
    """Проверяет доступность backend сервиса"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_statistics() -> Optional[Dict[str, Any]]:
    """Получает статистику из backend"""
    try:
        response = requests.get(STATISTICS_ENDPOINT, timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def get_recent_requests() -> Optional[Dict[str, Any]]:
    """Получает последние запросы из backend"""
    try:
        response = requests.get(RECENT_ENDPOINT, timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def process_diagram(file) -> Optional[Dict[str, Any]]:
    """Отправляет файл на обработку в backend"""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        response = requests.post(API_ENDPOINT, files=files, timeout=120)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Ошибка сервера: {response.status_code}")
            st.error(response.text)
            return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Превышено время ожидания. Попробуйте еще раз.")
        return None
    except Exception as e:
        st.error(f"❌ Ошибка при обработке: {str(e)}")
        return None


# Заголовок
st.markdown('<div class="main-header">📊 Сервис распознавания диаграмм</div>', unsafe_allow_html=True)

# Sidebar с информацией и статистикой
with st.sidebar:
    st.header("ℹ️ Информация")
    
    # Проверка доступности backend
    if check_backend_health():
        st.markdown('<div class="success-box">✅ Backend доступен</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="error-box">❌ Backend недоступен</div>', unsafe_allow_html=True)
        st.stop()
    
    st.markdown("---")
    
    # Поддерживаемые форматы
    st.subheader("📁 Поддерживаемые форматы")
    st.markdown("**Изображения:**")
    st.markdown("• PNG, JPG, JPEG, GIF, BMP")
    st.markdown("**Диаграммы:**")
    st.markdown("• BPMN (.bpmn)")
    st.markdown("• PlantUML (.puml)")
    st.markdown("• Mermaid (.mmd)")
    st.markdown("• Draw.io (.drawio)")
    
    st.markdown("---")
    
    # Статистика
    st.subheader("📈 Статистика")
    stats = get_statistics()
    
    if stats:
        total = stats.get("total_requests", 0)
        successful = stats.get("successful", 0)
        success_rate = (successful / total * 100) if total > 0 else 0
        avg_time = stats.get("avg_processing_time", 0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Всего запросов", total)
            st.metric("Успешных", successful)
        with col2:
            st.metric("Success Rate", f"{success_rate:.1f}%")
            st.metric("Среднее время", f"{avg_time:.1f}s" if avg_time else "N/A")
        
        # Статистика по устройствам
        if stats.get("by_device"):
            st.markdown("**По устройствам:**")
            for device_stat in stats["by_device"]:
                device = device_stat.get("device_type", "unknown")
                count = device_stat.get("count", 0)
                avg = device_stat.get("avg_time", 0)
                st.markdown(f"• {device}: {count} ({avg:.1f}s)")
    else:
        st.info("Статистика недоступна")

# Основная область
tab1, tab2 = st.tabs(["🔍 Распознавание", "📜 История"])

with tab1:
    st.header("Загрузите диаграмму для распознавания")
    
    # Информационное сообщение
    st.markdown("""
    <div class="info-box">
    💡 <b>Как это работает:</b><br>
    1. Загрузите файл диаграммы (изображение или исходный формат)<br>
    2. Система автоматически конвертирует его в PNG (если нужно)<br>
    3. VLM модель распознает структуру и генерирует описание<br>
    4. Результат отображается в виде таблицы с шагами алгоритма
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Загрузка файла
    uploaded_file = st.file_uploader(
        "Выберите файл диаграммы",
        type=SUPPORTED_FORMATS,
        help="Поддерживаются изображения и форматы диаграмм"
    )
    
    if uploaded_file is not None:
        # Отображаем информацию о файле
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Имя файла", uploaded_file.name)
        with col2:
            file_size_kb = len(uploaded_file.getvalue()) / 1024
            st.metric("Размер", f"{file_size_kb:.2f} KB")
        with col3:
            st.metric("Тип", uploaded_file.type)
        
        # Если это изображение, показываем превью
        if uploaded_file.type.startswith("image/"):
            st.image(uploaded_file, caption="Загруженная диаграмма", use_container_width=True)
        
        st.markdown("")
        
        # Кнопка обработки
        if st.button("🚀 Распознать диаграмму", type="primary", use_container_width=True):
            with st.spinner("⏳ Обработка диаграммы... Это может занять до 20 секунд"):
                result = process_diagram(uploaded_file)
                
                if result:
                    st.success("✅ Диаграмма успешно распознана!")
                    
                    # Результат
                    st.markdown("### 📋 Описание алгоритма")
                    description = result.get("description", "")
                    st.markdown(description)
                    
                    # Метаданные
                    st.markdown("### 📊 Метаданные")
                    metadata = result.get("metadata", {})
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Время обработки", f"{metadata.get('processing_time', 0):.2f}s")
                    with col2:
                        st.metric("Время инференса", f"{metadata.get('inference_time', 0):.2f}s")
                    with col3:
                        st.metric("Модель", metadata.get('model', 'N/A').split('/')[-1])
                    with col4:
                        st.metric("Устройство", metadata.get('device', 'N/A'))
                    
                    # Дополнительная информация
                    with st.expander("🔍 Подробная информация"):
                        st.json(metadata)

with tab2:
    st.header("История запросов")
    
    if st.button("🔄 Обновить", use_container_width=True):
        st.rerun()
    
    recent = get_recent_requests()
    
    if recent and recent.get("requests"):
        requests_list = recent["requests"]
        
        st.markdown(f"**Показано последних запросов: {len(requests_list)}**")
        st.markdown("")
        
        for idx, req in enumerate(requests_list, 1):
            with st.expander(f"#{idx} - {req.get('file_name', 'N/A')} ({req.get('request_timestamp', 'N/A')})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**Файл:**")
                    st.markdown(f"• Имя: {req.get('file_name', 'N/A')}")
                    st.markdown(f"• Тип: {req.get('file_type', 'N/A')}")
                    st.markdown(f"• Статус: {req.get('status', 'N/A')}")
                
                with col2:
                    st.markdown("**Модель:**")
                    st.markdown(f"• {req.get('model_name', 'N/A')}")
                    st.markdown(f"• Устройство: {req.get('device_type', 'N/A')}")
                
                with col3:
                    st.markdown("**Производительность:**")
                    st.markdown(f"• Время: {req.get('total_processing_time_sec', 0):.2f}s")
                    st.markdown(f"• Длина ответа: {req.get('description_length', 0)} символов")
    else:
        st.info("История запросов пуста")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6c757d; font-size: 0.9rem;">
    <p>Сервис распознавания алгоритмов по диаграммам | Powered by Qwen3-VL</p>
</div>
""", unsafe_allow_html=True)