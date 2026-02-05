import streamlit as st
import os
import cv2
import numpy as np
from processor import DiagramParser
from generator import LLMTableGenerator, ensure_model_exists
from PIL import Image

# --- КОНФИГУРАЦИЯ ---
BLOCKS_PATH = 'hybrid_model_arrows_blocks/blocks/weights/best.pt'
ARROWS_PATH = 'hybrid_model_arrows_blocks/arrows/weights/best.pt'
TEMP_DIR = "temp"

st.set_page_config(
    page_title="BPMN to Table AI",
    page_icon="🤖",
    layout="wide"
)

# --- ИНИЦИАЛИЗАЦИЯ МОДЕЛЕЙ ---
@st.cache_resource
def load_systems():
    if not os.path.exists(BLOCKS_PATH) or not os.path.exists(ARROWS_PATH):
        st.error(f"Файлы весов не найдены!")
        return None, None
    
    parser = DiagramParser(BLOCKS_PATH, ARROWS_PATH)
    generator = LLMTableGenerator(model_name="llama3.2")
    
    # Используем spinner - он есть во всех версиях
    with st.spinner("Проверка локальной нейросети Ollama..."):
        ensure_model_exists("llama3.2")
    
    return parser, generator

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

parser, generator = load_systems()

# --- ИНТЕРФЕЙС ---
st.title("🤖 BPMN Diagram to Table")
st.write("Загрузите изображение схемы для генерации регламента.")

# Заменяем колонки на более старый синтаксис для надежности
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Загрузка схемы")
    uploaded_file = st.file_uploader("Выберите файл", type=["png", "jpg", "jpeg"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Исходная схема")

with col2:
    st.subheader("2. Результат")
    if uploaded_file and parser and generator:
        if st.button("🚀 Обработать схему"):
            
            with st.spinner("Анализируем изображение..."):
                try:
                    temp_path = os.path.join(TEMP_DIR, uploaded_file.name)
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Обработка
                    graph_data = parser.process_image(temp_path)
                    
                    if not graph_data or not graph_data.get("nodes"):
                        st.warning("Элементы не найдены.")
                    else:
                        final_table = generator.generate_table(graph_data)
                        
                        st.success("Готово!")
                        st.markdown(final_table)
                        
                        st.download_button(
                            label="📥 Скачать таблицу (.md)",
                            data=final_table,
                            file_name=f"reglament.md",
                            mime="text/markdown"
                        )
                except Exception as e:
                    st.error(f"Ошибка: {e}")
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
    else:
        st.info("Ожидание загрузки файла...")

# --- ПОДВАЛ (Заменяем st.divider на Markdown черту) ---
st.markdown("---")
st.caption("Nexign Project AI • YOLOv8 + EasyOCR + Llama 3.2")