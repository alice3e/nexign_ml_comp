import torch
from PIL import Image
from transformers import Qwen3VLForConditionalGeneration, AutoProcessor
from peft import PeftModel
from qwen_vl_utils import process_vision_info

# === КОНФИГУРАЦИЯ ===
BASE_MODEL_ID = "Qwen/Qwen3-VL-2B-Instruct"
ADAPTER_PATH = "model_vlm_qwen3/weights"   # папка с LoRA-адаптерами + processor
TEST_IMAGE_PATH = "data/images/bpmn_table_048.png"


def run_inference():
    print("1. Загрузка базовой модели Qwen3-VL...")

    model = Qwen3VLForConditionalGeneration.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )

    print("2. Загрузка процессора...")
    # Обычно безопаснее грузить processor из папки с адаптерами,
    # т.к. там сохранены настройки, использованные при обучении
    try:
        processor = AutoProcessor.from_pretrained(ADAPTER_PATH)
        print("✅ Процессор загружен из папки адаптеров")
    except Exception:
        processor = AutoProcessor.from_pretrained(BASE_MODEL_ID)
        print("⚠️ Процессор загружен из BASE_MODEL_ID")

    print("3. Подключение LoRA-адаптеров...")
    try:
        model = PeftModel.from_pretrained(model, ADAPTER_PATH)
        print("✅ Адаптеры успешно загружены!")
    except Exception as e:
        print(f"⚠️ Не удалось загрузить адаптеры: {e}")
        print("Работаем на базовой модели...")

    model.eval()

    # === Подготовка изображения ===
    image = Image.open(TEST_IMAGE_PATH).convert("RGB")

    prompt = (
        "Ты эксперт по BPMN. "
        "Твоя задача — проанализировать диаграмму и создать структурированную "
        "таблицу Markdown с шагами алгоритма."
    )

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt},
            ],
        }
    ]

    # === Препроцессинг ===
    if hasattr(processor, "apply_chat_template"):
        text = processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
    else:
        # fallback, если вдруг нет apply_chat_template
        text = prompt

    image_inputs, video_inputs = process_vision_info(messages)

    proc_kwargs = {
        "text": [text],
        "padding": True,
        "return_tensors": "pt",
    }
    if image_inputs is not None:
        proc_kwargs["images"] = image_inputs
    if video_inputs is not None:
        proc_kwargs["videos"] = video_inputs

    inputs = processor(**proc_kwargs)
    inputs = inputs.to(model.device)

    # === Генерация ===
    print("4. Генерация ответа...")
    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=1024,
            do_sample=False,
        )

    # Убираем входные токены
    generated_ids_trimmed = [
        out_ids[len(in_ids):]
        for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]

    output_text = processor.batch_decode(
        generated_ids_trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )

    print("\n=== РЕЗУЛЬТАТ МОДЕЛИ ===\n")
    print(output_text[0])


if __name__ == "__main__":
    run_inference()
