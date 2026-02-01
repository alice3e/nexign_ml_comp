import os
# Включаем зеркало
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from huggingface_hub import snapshot_download

# MODEL_ID для Qwen3-VL (проверьте актуальное название на HF)
MODEL_ID = "Qwen/Qwen3-VL-2B-Instruct"  # или другая версия

print(f"🚀 Начинаю скачивание модели {MODEL_ID}...")
print("Обратите внимание: Qwen3-VL может быть больше по размеру")

try:
    path = snapshot_download(
        repo_id=MODEL_ID,
        repo_type="model",
        resume_download=True,
        # Можете добавить для больших моделей:
        # ignore_patterns=["*.msgpack", "*.h5", "*.ot"],
    )
    print(f"\n✅ Успешно скачано в: {path}")
except Exception as e:
    print(f"\n❌ Ошибка скачивания: {e}")