# inference_qwen3.py
import torch
from PIL import Image
from transformers import Qwen3VLForConditionalGeneration, AutoProcessor
from peft import PeftModel
from qwen_vl_utils import process_vision_info

BASE_MODEL_ID = "Qwen/Qwen3-VL-2B-Instruct"
ADAPTER_PATH = "model_vlm_qwen3/weights"
TEST_IMAGE_PATH = "data/images/bpmn_table_048.png"

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

SYSTEM_PROMPT = (
    "Ты эксперт по BPMN. Выдавай ответ строго в формате Markdown-таблицы. "
    "Заголовок таблицы должен быть точно: | № | Наименование действия | Роль |."
)

def run():
    print("Using device:", DEVICE)

    # Base model
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.float16,
    ).to(DEVICE)

    # Processor
    try:
        processor = AutoProcessor.from_pretrained(ADAPTER_PATH)
    except:
        processor = AutoProcessor.from_pretrained(BASE_MODEL_ID)

    # Load LoRA
    try:
        model = PeftModel.from_pretrained(model, ADAPTER_PATH)
        print("LoRA loaded")
    except Exception as e:
        print("LoRA not loaded:", e)

    model.eval()

    image = Image.open(TEST_IMAGE_PATH).convert("RGB")

    messages = [{
        "role": "user",
        "content": [
            {"type": "image", "image": image},
            {"type": "text", "text": SYSTEM_PROMPT},
        ],
    }]

    if hasattr(processor, "apply_chat_template"):
        text = processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False
        )
    else:
        text = SYSTEM_PROMPT

    image_inputs, video_inputs = process_vision_info(messages)

    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        return_tensors="pt",
        padding=True
    ).to(DEVICE)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=1024,
            do_sample=False
        )

    trimmed = [
        o[len(i):] for i, o in zip(inputs.input_ids, outputs)
    ]

    result = processor.batch_decode(
        trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False
    )[0]

    print("\n=== RESULT ===\n")
    print(result)

if __name__ == "__main__":
    run()
