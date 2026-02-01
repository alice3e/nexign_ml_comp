# validate.py
import time
import json
import os
import torch
import psutil
import pandas as pd
import Levenshtein
from tqdm import tqdm
from PIL import Image
from transformers import AutoProcessor
from peft import PeftModel

# Попытки импортировать специфичные классы (не упадёт, если их нет)
try:
    from transformers import Qwen3VLForConditionalGeneration as _QWEN3_CLASS
except Exception:
    _QWEN3_CLASS = None

try:
    from transformers import Qwen2VLForConditionalGeneration as _QWEN2_CLASS
except Exception:
    _QWEN2_CLASS = None

from qwen_vl_utils import process_vision_info

# === КОНФИГУРАЦИЯ ===
# Эти базовые id используются при детектировании/фоллбэке
QWEN2_BASE = "Qwen/Qwen2-VL-2B-Instruct"
QWEN3_BASE = "Qwen/Qwen3-VL-2B-Instruct"

# Поменяйте по необходимости
ADAPTER_PATH = "model_vlm_qwen3/weights"   # или model_vlm_qwen3/weights
VAL_FILE = "data/val.jsonl"
IMAGES_DIR = "data/images"

# detect device: prefer mps, then cuda, then cpu
if torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
elif torch.cuda.is_available():
    DEVICE = torch.device("cuda")
else:
    DEVICE = torch.device("cpu")


def get_memory_usage():
    """Возвращает потребление памяти процесса в МБ"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def parse_markdown_table(text):
    """Простая эвристика для подсчета строк в таблице"""
    lines = text.split("\n")
    # Считаем строки, которые начинаются с |, но не являются разделителем --- и не заголовком
    data_lines = [l for l in lines if l.strip().startswith("|") and ("---" not in l) and ("Наименование" not in l)]
    return len(data_lines)


def detect_adapter_variant(adapter_path: str) -> str:
    """
    Пытается определить, для какой модели (qwen2 или qwen3) сохранены адаптеры/processor.
    Возвращает 'qwen3', 'qwen2' или 'unknown'.
    """
    if not os.path.isdir(adapter_path):
        return "unknown"

    candidates = [
        "preprocessor_config.json",
        "adapter_config.json",  # PEFT
        "config.json",
        "tokenizer_config.json",
    ]

    for fname in candidates:
        p = os.path.join(adapter_path, fname)
        if not os.path.exists(p):
            continue
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue

        # Проверяем значения в json на вхождение qwen3/qwen2
        def inspect_obj(o):
            if isinstance(o, str):
                s = o.lower()
                if "qwen3" in s or "qwen-3" in s:
                    return "qwen3"
                if "qwen2" in s or "qwen-2" in s:
                    return "qwen2"
            elif isinstance(o, dict):
                for v in o.values():
                    res = inspect_obj(v)
                    if res:
                        return res
            elif isinstance(o, list):
                for v in o:
                    res = inspect_obj(v)
                    if res:
                        return res
            return None

        res = inspect_obj(data)
        if res:
            return res

    # Попытка по имени папки
    name = os.path.basename(os.path.normpath(adapter_path)).lower()
    if "qwen3" in name or "qwen_3" in name or "qwen-3" in name:
        return "qwen3"
    if "qwen2" in name or "qwen_2" in name or "qwen-2" in name:
        return "qwen2"

    return "unknown"


def choose_model_class(variant: str):
    """
    Возвращает tuple (model_class, base_model_id).
    Пытается выбрать Qwen3 сначала, затем Qwen2.
    """
    if variant == "qwen3":
        if _QWEN3_CLASS is not None:
            return _QWEN3_CLASS, QWEN3_BASE
        # если класс не импортирован, всё равно попробуем QWEN3_BASE при загрузке
        return None, QWEN3_BASE
    if variant == "qwen2":
        if _QWEN2_CLASS is not None:
            return _QWEN2_CLASS, QWEN2_BASE
        return None, QWEN2_BASE
    # unknown: предпочесть Qwen3 если доступен, иначе Qwen2
    if _QWEN3_CLASS is not None:
        return _QWEN3_CLASS, QWEN3_BASE
    if _QWEN2_CLASS is not None:
        return _QWEN2_CLASS, QWEN2_BASE
    # оба недоступны — вернём None, и будем пытаться загружать динамически
    return None, QWEN3_BASE


def validate():
    print("=== ЗАПУСК ВАЛИДАЦИИ ===")
    print("ADAPTER_PATH:", ADAPTER_PATH)
    variant = detect_adapter_variant(ADAPTER_PATH)
    print("Detected adapter variant:", variant)

    model_class, base_model_id = choose_model_class(variant)
    print("Chosen base model id:", base_model_id)
    mem_start = get_memory_usage()

    # Подбор dtype и загрузки в зависимости от устройства
    if DEVICE.type == "mps":
        torch_dtype = torch.float16
        use_device_map = False
    elif DEVICE.type == "cuda":
        torch_dtype = torch.bfloat16
        use_device_map = True
    else:
        torch_dtype = torch.float32
        use_device_map = False

    model = None
    processor = None

    # 1) Попытка загружать модель с variant-first стратегией:
    load_errors = []
    tried_classes = []
    # список кандидатов: если detect вернул qwen3/qwen2, сначала пробуем соответствующий,
    # затем пробуем другой (фоллбэк)
    candidates = []
    if variant == "qwen3":
        candidates = [("qwen3", _QWEN3_CLASS, QWEN3_BASE), ("qwen2", _QWEN2_CLASS, QWEN2_BASE)]
    elif variant == "qwen2":
        candidates = [("qwen2", _QWEN2_CLASS, QWEN2_BASE), ("qwen3", _QWEN3_CLASS, QWEN3_BASE)]
    else:
        candidates = [("qwen3", _QWEN3_CLASS, QWEN3_BASE), ("qwen2", _QWEN2_CLASS, QWEN2_BASE)]

    for name, cls, base in candidates:
        try:
            print(f"Пытаемся загрузить модель {name} (base id {base}) ...")
            if cls is not None:
                # Класс доступен в импортированной библиотеке
                if use_device_map and hasattr(torch, "device") and DEVICE.type == "cuda":
                    model = cls.from_pretrained(base, torch_dtype=torch_dtype, device_map="auto")
                else:
                    model = cls.from_pretrained(base, torch_dtype=torch_dtype)
                    model.to(DEVICE)
            else:
                # если класс не импортирован, пробуем generic from_pretrained через AutoModel (динамический)
                # здесь всё равно используем base id, transformers подберёт корректную реализацию
                from transformers import AutoModelForCausalLM
                if use_device_map and DEVICE.type == "cuda":
                    model = AutoModelForCausalLM.from_pretrained(base, torch_dtype=torch_dtype, device_map="auto")
                else:
                    model = AutoModelForCausalLM.from_pretrained(base, torch_dtype=torch_dtype)
                    model.to(DEVICE)
            print(f"Модель {name} загружена.")
            model_base_used = base
            break
        except Exception as e:
            err = f"Ошибка загрузки модели {name}: {e}"
            load_errors.append(err)
            tried_classes.append(name)
            print(err)
            model = None

    if model is None:
        print("Не удалось загрузить ни Qwen3, ни Qwen2 через доступные классы. Выводим ошибки и выходим.")
        for e in load_errors:
            print(e)
        return

    # 2) Загружаем процессор — предпочитаем ADAPTER_PATH
    try:
        processor = AutoProcessor.from_pretrained(ADAPTER_PATH)
        print("Processor загружен из ADAPTER_PATH:", ADAPTER_PATH)
    except Exception:
        try:
            processor = AutoProcessor.from_pretrained(model_base_used, min_pixels=256*28*28, max_pixels=512*28*28)
            print("Processor загружен из base model:", model_base_used)
        except Exception as e:
            print("Не удалось загрузить processor:", e)
            return

    # 3) Попытка загрузки LoRA адаптеров (PEFT)
    try:
        model = PeftModel.from_pretrained(model, ADAPTER_PATH)
        print("✅ Адаптеры LoRA загружены из:", ADAPTER_PATH)
    except Exception as e:
        print("⚠️ Адаптеры не найдены/не удалось загрузить. Валидируем на базовой модели. Ошибка:", e)

    mem_model_loaded = get_memory_usage()
    print(f"Память после загрузки модели: {mem_model_loaded:.1f} MB (+{mem_model_loaded - mem_start:.1f} MB)")

    # 4) Загрузка валидационных данных
    with open(VAL_FILE, "r", encoding="utf-8") as f:
        val_data = [json.loads(line) for line in f]
    print(f"Валидация на {len(val_data)} примерах...")

    metrics = {"latency": [], "text_similarity": [], "step_count_diff": []}

    # Используем единый строгий prompt и add_generation_prompt=False
    prompt = (
        "Ты эксперт по BPMN. Выдавай ответ строго в формате Markdown-таблицы. "
        "Заголовок таблицы должен быть точно: | № | Наименование действия | Роль |."
    )

    model.eval()

    for item in tqdm(val_data):
        image_path = os.path.join(IMAGES_DIR, item["file_name"])
        ground_truth = item["text"]

        image = Image.open(image_path).convert("RGB")
        messages = [{"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": prompt}]}]

        # формируем текст входа с add_generation_prompt=False (чтобы совпадало с training)
        if hasattr(processor, "apply_chat_template"):
            text_input = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        else:
            text_input = prompt

        image_inputs, video_inputs = process_vision_info(messages)
        proc_kwargs = {"text": [text_input], "padding": True, "return_tensors": "pt"}
        if image_inputs is not None:
            proc_kwargs["images"] = image_inputs
        if video_inputs is not None:
            proc_kwargs["videos"] = video_inputs

        inputs = processor(**proc_kwargs)

        # Переносим входы на нужное устройство (если модель не в device_map)
        try:
            inputs = inputs.to(model.device)
        except Exception:
            # Если model.device не установлен (например, device_map="auto"), перенесём на DEVICE вручную
            inputs = {k: (v.to(DEVICE) if hasattr(v, "to") else v) for k, v in inputs.items()}

        start_time = time.perf_counter()
        with torch.no_grad():
            generated_ids = model.generate(**inputs, max_new_tokens=1024, do_sample=False)
        end_time = time.perf_counter()

        latency = end_time - start_time
        metrics["latency"].append(latency)

        # Триммим с учётом длины входных токенов
        # В некоторых ситуациях inputs.input_ids может быть tensor или attribute access style
        in_ids = inputs["input_ids"] if isinstance(inputs, dict) else inputs.input_ids
        generated_ids_trimmed = [out_ids[len(in_ids):] for in_ids, out_ids in zip(in_ids, generated_ids)]

        prediction = processor.batch_decode(generated_ids_trimmed, skip_special_tokens=True)[0]

        sim = Levenshtein.ratio(prediction, ground_truth)
        metrics["text_similarity"].append(sim)

        gt_steps = parse_markdown_table(ground_truth)
        pred_steps = parse_markdown_table(prediction)
        metrics["step_count_diff"].append(abs(gt_steps - pred_steps))

    # 5) Отчет
    df = pd.DataFrame(metrics)
    print("\n" + "=" * 30)
    print("📊 РЕЗУЛЬТАТЫ ВАЛИДАЦИИ")
    print("=" * 30)
    print(f"Среднее время (Latency): {df['latency'].mean():.2f} сек/img")
    print(f"Макс время:              {df['latency'].max():.2f} сек/img")
    print(f"Требование (<20 сек):    {'✅ PASS' if df['latency'].max() < 20 else '❌ FAIL'}")
    print("-" * 30)
    print(f"Сходство текста (Sim):   {df['text_similarity'].mean():.2%}")
    print(f"Ошибки в кол-ве шагов:   {df['step_count_diff'].mean():.2f}")
    print("-" * 30)
    print(f"Потребление RAM:         {mem_model_loaded:.1f} MB")
    print(f"Требование (<8 GB):      {'✅ PASS' if mem_model_loaded < 8192 else '❌ FAIL'}")
    print("=" * 30)

    df.to_csv("validation_results.csv", index=False)
    print("Детальный лог сохранен в validation_results.csv")


if __name__ == "__main__":
    validate()
