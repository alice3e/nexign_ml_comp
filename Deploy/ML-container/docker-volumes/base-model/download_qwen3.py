import os
import sys
from pathlib import Path

# Включаем зеркало для ускорения загрузки (опционально)
# os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from huggingface_hub import snapshot_download

# Конфигурация
MODEL_ID = "Qwen/Qwen3-VL-2B-Instruct"
CACHE_DIR = os.environ.get("HF_HOME", "/root/.cache/huggingface")

def download_model():
    """
    Скачивает базовую модель Qwen3-VL-2B-Instruct из HuggingFace Hub.
    Модель кэшируется в HF_HOME для переиспользования.
    """
    print("=" * 60)
    print(f"🚀 Загрузка модели: {MODEL_ID}")
    print(f"📂 Директория кэша: {CACHE_DIR}")
    print("=" * 60)
    
    # Проверяем доступность директории
    cache_path = Path(CACHE_DIR)
    cache_path.mkdir(parents=True, exist_ok=True)
    
    try:
        print("\n⏳ Начинаю загрузку... (это может занять несколько минут)")
        print("💡 Модель весит ~4-5 GB, убедитесь в наличии свободного места\n")
        
        path = snapshot_download(
            repo_id=MODEL_ID,
            cache_dir=CACHE_DIR,
            resume_download=True,
            # Игнорируем ненужные файлы для экономии места
            ignore_patterns=[
                "*.msgpack",
                "*.h5",
                "*.ot",
                "*.md",  # README файлы
                ".gitattributes"
            ],
        )
        
        print("\n" + "=" * 60)
        print("✅ Модель успешно загружена!")
        print(f"📍 Путь: {path}")
        print("=" * 60)
        
        # Проверяем размер загруженной модели
        total_size = sum(f.stat().st_size for f in Path(path).rglob('*') if f.is_file())
        print(f"💾 Размер на диске: {total_size / (1024**3):.2f} GB\n")
        
        return path
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Ошибка при загрузке модели: {e}")
        print("=" * 60)
        print("\n💡 Возможные причины:")
        print("  - Отсутствует интернет-соединение")
        print("  - Недостаточно места на диске")
        print("  - Проблемы с доступом к HuggingFace Hub")
        print("  - Неверное имя модели")
        print("\n🔧 Попробуйте:")
        print("  - Проверить подключение к интернету")
        print("  - Освободить место на диске (требуется ~5 GB)")
        print("  - Установить переменную HF_TOKEN если модель приватная")
        sys.exit(1)

if __name__ == "__main__":
    download_model()
