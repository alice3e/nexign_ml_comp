'''import os, time, json, torch, psutil, Levenshtein
from PIL import Image
from transformers import Qwen3VLForConditionalGeneration, AutoProcessor
from peft import PeftModel
from qwen_vl_utils import process_vision_info

# короткий компактный валидатор для MPS
DEVICE = torch.device("mps")
BASE = "Qwen/Qwen3-VL-2B-Instruct"
HERE = os.path.dirname(__file__)
ADAPTER = os.environ.get("ADAPTER_PATH", os.path.join(HERE, "weights"))
VAL = os.environ.get("VAL_FILE", os.path.join("data", "val.jsonl"))
IMDIR = os.environ.get("IMAGES_DIR", os.path.join("data", "images"))

def steps(text):
    return len([l for l in text.splitlines() if l.strip().startswith("|") and "Наименование" not in l and "---" not in l])

m = Qwen3VLForConditionalGeneration.from_pretrained(BASE, torch_dtype=torch.float16)
m.to(DEVICE)
proc = AutoProcessor.from_pretrained(ADAPTER)
m = PeftModel.from_pretrained(m, ADAPTER)
m.eval()

data = [json.loads(l) for l in open(VAL, encoding="utf-8")]
lat, sim, sd = [], [], []
PROMPT = "Ты эксперт по BPMN. Выдавай ответ строго в формате Markdown-таблицы. Заголовок таблицы должен быть точно: | № | Наименование действия | Роль |."
for it in data:
    img = Image.open(os.path.join(IMDIR, it['file_name'])).convert('RGB')
    messages = [{"role":"user","content":[{"type":"image","image":img},{"type":"text","text":PROMPT}]}]
    text = proc.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    image_inputs, video_inputs = process_vision_info(messages)
    kwargs = {"text":[text], "padding":True, "return_tensors":"pt"}
    if image_inputs is not None:
        kwargs["images"] = image_inputs
    inp = proc(**kwargs).to(DEVICE)
    t0 = time.perf_counter()
    with torch.inference_mode():
        out = m.generate(**inp, max_new_tokens=384, do_sample=False)
    t1 = time.perf_counter()
    lat.append(t1 - t0)
    in_ids = inp['input_ids']
    trimmed = [o[len(in_ids):] for in_ids, o in zip(in_ids, out)]
    pred = proc.batch_decode(trimmed, skip_special_tokens=True)[0]
    sim.append(Levenshtein.ratio(pred, it['text']))
    sd.append(abs(steps(pred) - steps(it['text'])))

import pandas as pd
metrics = {
    "latency": lat,
    "text_similarity": sim,
    "step_count_diff": sd,
}
df = pd.DataFrame(metrics)
mem_mb = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
print("" + "=" * 30)
print("📊 РЕЗУЛЬТАТЫ ВАЛИДАЦИИ")
print("=" * 30)
print(f"Среднее время (Latency): {df['latency'].mean():.2f} сек/img")
print(f"Макс время:              {df['latency'].max():.2f} сек/img")
print(f"Требование (<20 сек):    {'✅ PASS' if df['latency'].max() < 20 else '❌ FAIL'}")
print("-" * 30)
print(f"Сходство текста (Sim):   {df['text_similarity'].mean():.2%}")
print(f"Ошибки в кол-ве шагов:   {df['step_count_diff'].mean():.2f}")
print("-" * 30)
print(f"Потребление RAM:         {mem_mb:.1f} MB")
print(f"Требование (<8 GB):      {'✅ PASS' if mem_mb < 8192 else '❌ FAIL'}")
print("=" * 30)
df.to_csv("validation_results.csv", index=False)
print("Детальный лог сохранен в validation_results.csv")
'''

# validate.py (modified to log metrics & csv to MLflow)
import os
import time
import json
import mlflow
import torch
import psutil
import pandas as pd
import numpy as np
import Levenshtein
from PIL import Image
from transformers import AutoProcessor
from peft import PeftModel
from qwen_vl_utils import process_vision_info

# поправка: корректный путь до текущего файла
HERE = os.path.dirname(__file__)
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

# параметры валидации (можно взять из params.json или передать в argv)
BASE = "Qwen/Qwen3-VL-2B-Instruct"
ADAPTER = os.environ.get("ADAPTER_PATH", os.path.join(HERE, "weights"))
VAL = os.environ.get("VAL_FILE", os.path.join("data", "val.jsonl"))
IMDIR = os.environ.get("IMAGES_DIR", os.path.join("data", "images"))

VALIDATION_PARAMS = {
    "max_new_tokens": 384,
    "do_sample": False,
    "prompt_length": 512,
    "torch_dtype": "torch.float16",
    # можно расширить...
}

def steps(text):
    return len([l for l in text.splitlines() if l.strip().startswith("|") and "Наименование" not in l and "---" not in l])

def load_model_and_processor(base, adapter):
    proc = AutoProcessor.from_pretrained(adapter)
    m = torch.load if False else None  # placeholder
    # load base model + peft adapter
    from transformers import Qwen3VLForConditionalGeneration
    from peft import PeftModel
    m = Qwen3VLForConditionalGeneration.from_pretrained(base, torch_dtype=torch.float16)
    m.to(DEVICE)
    m = PeftModel.from_pretrained(m, adapter)
    m.eval()
    return m, proc

def validate():
    mlflow.set_experiment("qwen3vl-adapter-tuning")
    with mlflow.start_run() as run:
        # Log validation params and tags
        mlflow.log_params(VALIDATION_PARAMS)
        mlflow.set_tag("adapter_path", ADAPTER)
        mlflow.set_tag("val_file", VAL)
        mlflow.set_tag("images_dir", IMDIR)
        mlflow.set_tag("device", str(DEVICE))

        m, proc = load_model_and_processor(BASE, ADAPTER)

        data = [json.loads(l) for l in open(VAL, encoding="utf-8")]
        lat, sim, sd = [], [], []
        preds = []

        PROMPT = "Ты эксперт по BPMN. Выдавай ответ строго в формате Markdown-таблицы. Заголовок таблицы должен быть точно: | № | Наименование действия | Роль |."

        for it in data:
            img = Image.open(os.path.join(IMDIR, it['file_name'])).convert('RGB')
            messages = [{"role":"user","content":[{"type":"image","image":img},{"type":"text","text":PROMPT}]}]
            text = proc.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
            image_inputs, video_inputs = process_vision_info(messages)
            kwargs = {"text":[text], "padding":True, "return_tensors":"pt"}
            if image_inputs is not None:
                kwargs["images"] = image_inputs
            inp = proc(**kwargs).to(DEVICE)

            t0 = time.perf_counter()
            with torch.inference_mode():
                out = m.generate(**inp, max_new_tokens=VALIDATION_PARAMS["max_new_tokens"], do_sample=VALIDATION_PARAMS["do_sample"])
            t1 = time.perf_counter()

            in_ids = inp['input_ids']
            # trimmed: remove input tokens from generated sequence
            trimmed = [o[len(in_ids_):] for in_ids_, o in zip(in_ids, out)]
            pred = proc.batch_decode(trimmed, skip_special_tokens=True)[0]

            latency = t1 - t0
            lsim = Levenshtein.ratio(pred, it['text'])
            step_diff = abs(steps(pred) - steps(it['text']))

            lat.append(latency)
            sim.append(lsim)
            sd.append(step_diff)
            preds.append({
                "file_name": it['file_name'],
                "pred_text": pred,
                "ref_text": it['text'],
                "text_similarity": lsim,
                "pred_steps": steps(pred),
                "ref_steps": steps(it['text']),
                "step_count_diff": step_diff,
                "latency_sec": latency,
            })

        df = pd.DataFrame(preds)

        # aggregate metrics
        def p95(x): return float(np.percentile(x, 95))
        metrics = {
            "latency_mean": float(np.mean(lat)),
            "latency_max": float(np.max(lat)),
            "latency_p95": p95(lat),
            "text_similarity_mean": float(np.mean(sim)),
            "text_similarity_median": float(np.median(sim)),
            "text_similarity_p95": p95(sim),
            "step_count_diff_mean": float(np.mean(sd)),
        }

        # log aggregated metrics
        mlflow.log_metrics(metrics)

        # log resource usage as metric
        mem_mb = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        mlflow.log_metric("memory_rss_mb", mem_mb)

        # save per-sample csv and log as artifact
        csv_path = os.path.join("validation_results.csv")
        df.to_csv(csv_path, index=False, encoding="utf-8")
        mlflow.log_artifact(csv_path, artifact_path="validation")

        # save top-10 worst predictions (by text_similarity) as example file
        worst = df.sort_values("text_similarity").head(10)
        worst_path = os.path.join("worst_examples.txt")
        with open(worst_path, "w", encoding="utf-8") as f:
            for _, r in worst.iterrows():
                f.write(f"FILE: {r['file_name']}\nSIM: {r['text_similarity']:.4f}\nPRED:\n{r['pred_text']}\nREF:\n{r['ref_text']}\n---\n\n")
        mlflow.log_artifact(worst_path, artifact_path="validation")

        # log the adapter/weights folder (если существует)
        if os.path.isdir(ADAPTER):
            mlflow.log_artifacts(ADAPTER, artifact_path="weights_used_for_validation")

        # print summary (console)
        print("=" * 30)
        print("📊 РЕЗУЛЬТАТЫ ВАЛИДАЦИИ")
        print("=" * 30)
        print(f"Среднее время (Latency): {metrics['latency_mean']:.2f} сек/img")
        print(f"Макс время:              {metrics['latency_max']:.2f} сек/img")
        print(f"Сходство текста (Sim):   {metrics['text_similarity_mean']:.2%}")
        print(f"Ошибки в кол-ве шагов:   {metrics['step_count_diff_mean']:.2f}")
        print(f"Потребление RAM:         {mem_mb:.1f} MB")
        print("=" * 30)
        print("Детальный лог сохранен в validation_results.csv и в MLflow.")

if __name__ == "__main__":
    validate()
