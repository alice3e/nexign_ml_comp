import os
import torch
import streamlit as st
from PIL import Image
# Пытаемся импортировать класс для новых версий Qwen (2.5 и 3)
try:
    from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
except ImportError:
    # Если библиотека старая, пробуем старый класс, но это может не сработать для Qwen3
    from transformers import Qwen2VLForConditionalGeneration as Qwen2_5_VLForConditionalGeneration
    from transformers import AutoProcessor

from peft import PeftModel
from qwen_vl_utils import process_vision_info

# === КОНФИГУРАЦИЯ ===
# ID модели, который ты просила
BASE_MODEL_ID = "Qwen/Qwen3-VL-2B-Instruct"

# Путь к весам (сохраняем в папку model_vlm_qwen3 для порядка)
ADAPTER_PATH = os.getenv("MODEL_PATH", os.path.join("model_vlm_qwen3", "weights"))

# === ЗАГРУЗКА МОДЕЛИ ===
@st.cache_resource
def load_model_and_processor():
    st.toast(f"Загрузка модели: {BASE_MODEL_ID}...", icon="⏳")
    print(f"🔄 Загрузка {BASE_MODEL_ID} из: {ADAPTER_PATH}")
    
    # 1. Грузим базу
    try:
        # Используем bfloat16 для Mac/MPS
        base_model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            BASE_MODEL_ID,
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )
    except OSError:
        st.error(f"❌ Модель '{BASE_MODEL_ID}' не найдена на HuggingFace. Проверьте название или доступ.")
        st.stop()
    except Exception as e:
        st.error(f"Ошибка загрузки модели: {e}")
        st.stop()
    
    # 2. Грузим адаптеры (LoRA)
    if os.path.exists(ADAPTER_PATH):
        try:
            model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
            print("✅ LoRA адаптеры подключены.")
            st.toast("LoRA адаптеры подключены!", icon="✅")
        except Exception as e:
            st.error(f"Ошибка загрузки весов LoRA: {e}")
            model = base_model
    else:
        st.warning(f"⚠️ Веса не найдены в {ADAPTER_PATH}. Работаем на базовой модели.")
        model = base_model

    # 3. Грузим процессор
    try:
        # Сначала ищем локальный процессор (если сохраняли при обучении)
        processor = AutoProcessor.from_pretrained(ADAPTER_PATH, min_pixels=256*28*28, max_pixels=512*28*28)
    except:
        # Если нет — качаем из хаба
        processor = AutoProcessor.from_pretrained(BASE_MODEL_ID, min_pixels=256*28*28, max_pixels=512*28*28)
        
    return model, processor

# === ИНТЕРФЕЙС ===
st.set_page_config(page_title="Qwen3 BPMN", page_icon="🔮", layout="centered")

st.title("🔮 BPMN Reader (Qwen3-VL)")
st.caption(f"Model ID: `{BASE_MODEL_ID}`")

# Сайдбар
with st.sidebar:
    st.header("Статус")
    if os.path.exists(ADAPTER_PATH):
        st.success(f"Fine-tuned weights detected")
    else:
        st.warning("Base model mode")
    
    st.markdown("---")
    st.markdown("**Настройки:**")
    # Можно добавить ползунок температуры, если нужно
    temperature = st.slider("Temperature", 0.0, 1.0, 0.1)

# Загрузка
uploaded_file = st.file_uploader("Загрузите диаграмму", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Входное изображение", use_column_width=True)
    
    if st.button("✨ Генерировать описание", type="primary"):
        with st.spinner("Анализ диаграммы..."):
            # Загрузка (один раз)
            model, processor = load_model_and_processor()
            
            # Промпт
            prompt = "Ты эксперт по BPMN. Проанализируй диаграмму и создай Markdown таблицу с шагами алгоритма."
            
            messages = [{"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": prompt}]}]
            
            text_input = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            image_inputs, video_inputs = process_vision_info(messages)
            
            inputs = processor(
                text=[text_input], images=image_inputs, videos=video_inputs,
                padding=True, return_tensors="pt"
            ).to(model.device)

            # Генерация
            with torch.no_grad():
                generated_ids = model.generate(
                    **inputs, 
                    max_new_tokens=1024, 
                    do_sample=False if temperature == 0 else True,
                    temperature=temperature if temperature > 0 else None
                )

            # Декодирование
            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            output_text = processor.batch_decode(
                generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )[0]

            st.markdown("### Результат:")
            st.markdown(output_text)