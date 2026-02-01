import os
import torch
from transformers import (
    Qwen2VLForConditionalGeneration, 
    TrainingArguments, 
    Trainer,
    AutoProcessor # Добавили импорт процессора
)
from peft import LoraConfig, get_peft_model, TaskType
from dataset import BPMNDataset, collate_fn

# === КОНФИГУРАЦИЯ ===
MODEL_ID = "Qwen/Qwen2-VL-2B-Instruct"
# Сохраняем сразу в правильную папку, чтобы app.py и inference.py видели веса
OUTPUT_DIR = os.path.join("model_vlm_qwen2", "weights") 
DATA_DIR = "data"

def train():
    print(f"Загрузка модели {MODEL_ID}...")
    
    # 0. Загружаем процессор (чтобы потом его сохранить)
    processor = AutoProcessor.from_pretrained(MODEL_ID, min_pixels=256*28*28, max_pixels=512*28*28)

    # 1. Загрузка модели
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )
    model.gradient_checkpointing_enable()
    
    # 2. Настройка LoRA (УЛУЧШЕННАЯ)
    peft_config = LoraConfig(
        r=16, # Ранг матрицы
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        # ВАЖНО: Обучаем ВСЕ линейные слои, а не только attention. 
        # Это кардинально повышает умственные способности модели на новых задачах.
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        task_type="CAUSAL_LM",
    )
    
    model = get_peft_model(model, peft_config)
    print("Параметры модели:")
    model.print_trainable_parameters()

    # 3. Данные
    train_dataset = BPMNDataset(
        os.path.join(DATA_DIR, "train.jsonl"), 
        os.path.join(DATA_DIR, "images"), 
        MODEL_ID
    )
    
    # 4. Аргументы обучения (СБАЛАНСИРОВАННЫЕ)
    args = TrainingArguments(
        output_dir="checkpoints_temp", # Временная папка для логов
        per_device_train_batch_size=1, 
        gradient_accumulation_steps=4, # Накапливаем побольше (стабильнее градиент)
        num_train_epochs=5,            # 5 качественных эпох лучше, чем 10 быстрых
        learning_rate=2e-4,            # Классический LR, который не ломает веса
        logging_steps=5,
        save_strategy="no",            # Не сохраняем промежуточные, только финал
        fp16=False,
        bf16=True,
        use_cpu=False,
        optim="adamw_torch",
        remove_unused_columns=False,
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        data_collator=collate_fn,
    )

    print("🚀 Начинаем обучение...")
    trainer.train()
    
    print(f"💾 Сохранение модели в {OUTPUT_DIR}...")
    # Создаем папку если нет
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Сохраняем адаптеры
    model.save_pretrained(OUTPUT_DIR)
    # Сохраняем процессор (ОБЯЗАТЕЛЬНО)
    processor.save_pretrained(OUTPUT_DIR)
    
    print("✅ Готово! Теперь запускай inference.py")

if __name__ == "__main__":
    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    train()