import os
# Включаем зеркало прямо в коде, чтобы наверняка
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from huggingface_hub import snapshot_download

MODEL_ID = "Qwen/Qwen2-VL-2B-Instruct"

print(f"🚀 Начинаю скачивание модели {MODEL_ID}...")
print("Это может занять время (~4.5 ГБ), но должно работать быстро через зеркало.")

try:
    path = snapshot_download(
        repo_id=MODEL_ID,
        repo_type="model",
        resume_download=True  # Позволяет продолжить, если оборвется
    )
    print(f"\n✅ Успешно скачано в: {path}")
    print("Теперь можно запускать uv run model_vlm/train.py")
except Exception as e:
    print(f"\n❌ Ошибка скачивания: {e}")