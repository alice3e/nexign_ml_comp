import os
import torch
import streamlit as st
from PIL import Image
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
# В твоем примере используется Qwen3VLForConditionalGeneration. 
# Если библиотека transformers обновлена под Qwen3, этот импорт сработает.
# Если нет — используем фолбэк на Qwen2VL (архитектурно они совместимы).
try:
    from transformers import Qwen3VLForConditionalGeneration
except ImportError:
    from transformers import Qwen2VLForConditionalGeneration as Qwen3VLForConditionalGeneration

from peft import PeftModel
from qwen_vl_utils import process_vision_info

# === КОНФИГУРАЦИЯ ===
BASE_MODEL_ID = "Qwen/Qwen3-VL-2B-Instruct"
# Путь к весам: берем из ENV или ищем рядом в папке weights
ADAPTER_PATH = os.getenv("MODEL_PATH", os.path.join("model_vlm_qwen3", "weights"))
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

# === КЭШИРОВАНИЕ ЗАГРУЗКИ МОДЕЛИ ===
@st.cache_resource
def load_model_and_processor():
    """
    Загружает модель один раз и держит её в памяти.
    Логика 1-в-1 как в твоем validate.py
    """
    print(f"🔄 Инициализация модели на устройстве: {DEVICE}")
    print(f"📂 Адаптеры: {ADAPTER_PATH}")

    # 1. Процессор
    # Пытаемся загрузить из адаптера, если там есть конфиг, иначе из базы
    try:
        proc = AutoProcessor.from_pretrained(ADAPTER_PATH, min_pixels=256*28*28, max_pixels=512*28*28)
    except:
        proc = AutoProcessor.from_pretrained(BASE_MODEL_ID, min_pixels=256*28*28, max_pixels=512*28*28)

    # 2. Модель
    # Используем float16 как в твоем примере
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        BASE_MODEL_ID, 
        torch_dtype=torch.float16,
        device_map=DEVICE # Streamlit иногда лучше работает с явным device_map
    )
    
    # 3. Адаптеры
    if os.path.exists(ADAPTER_PATH):
        try:
            model = PeftModel.from_pretrained(model, ADAPTER_PATH)
            model.eval() # Режим инференса
            print("✅ LoRA адаптеры успешно подключены")
        except Exception as e:
            st.error(f"Ошибка загрузки LoRA: {e}")
    else:
        print("⚠️ Адаптеры не найдены, используется базовая модель")

    return model, proc

# === ИНТЕРФЕЙС ===
st.set_page_config(page_title="Qwen3 BPMN Reader", page_icon="📊", layout="centered")

st.title("📊 BPMN Diagram Reader")
st.caption(f"Model: `{BASE_MODEL_ID}` | Device: `{DEVICE}`")

# Сайдбар с инфо
with st.sidebar:
    st.header("Статус системы")
    if os.path.exists(ADAPTER_PATH):
        st.success("🟢 Адаптеры найдены")
    else:
        st.warning("🟠 Режим базовой модели")
    
    st.info("Загрузите изображение диаграммы, чтобы получить описание алгоритма в виде таблицы.")

# Основная область
uploaded_file = st.file_uploader("Загрузите диаграмму (PNG, JPG)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # Отображаем картинку
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Загруженная схема", use_column_width=True)

    # Кнопка действия
    if st.button("⚡ Распознать алгоритм", type="primary"):
        with st.spinner("Анализ диаграммы..."):
            try:
                # Получаем модель (из кэша)
                model, processor = load_model_and_processor()

                # Промпт как в validate.py
                PROMPT = "Ты эксперт по BPMN. Выдавай ответ строго в формате Markdown-таблицы. Заголовок таблицы должен быть точно: | № | Наименование действия | Роль |."

                # Подготовка инпутов
                messages = [{"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": PROMPT}]}]
                
                text_input = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                image_inputs, video_inputs = process_vision_info(messages)
                
                inputs = processor(
                    text=[text_input], 
                    images=image_inputs, 
                    videos=video_inputs,
                    padding=True, 
                    return_tensors="pt"
                ).to(DEVICE)

                # Генерация
                with torch.inference_mode(): # Аналог torch.no_grad()
                    generated_ids = model.generate(
                        **inputs, 
                        max_new_tokens=384, # Как в твоем validate.py
                        do_sample=False
                    )

                # Декодирование (отрезаем промпт)
                generated_ids_trimmed = [
                    out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
                ]
                output_text = processor.batch_decode(
                    generated_ids_trimmed, 
                    skip_special_tokens=True, 
                    clean_up_tokenization_spaces=False
                )[0]

                # Вывод результата
                st.success("Готово!")
                st.markdown("### Результат:")
                st.markdown(output_text)
            
            except Exception as e:
                st.error(f"Ошибка при генерации: {e}")