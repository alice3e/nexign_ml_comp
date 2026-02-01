'''# train_qwen3.py
import os
import torch
from transformers import (
    Qwen3VLForConditionalGeneration,
    AutoProcessor,
    TrainingArguments,
    Trainer,
)
from peft import LoraConfig, get_peft_model, TaskType
from dataset import BPMNDataset, collate_fn

# =========================
# CONFIG
# =========================
MODEL_ID = "Qwen/Qwen3-VL-2B-Instruct"
OUTPUT_DIR = os.path.join("model_vlm_qwen3", "weights")
DATA_DIR = "data"

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

def train():
    print("Using device:", DEVICE)

    # 0. Processor
    processor = AutoProcessor.from_pretrained(
        MODEL_ID,
        min_pixels=256*28*28,
        max_pixels=512*28*28
    )

    # 1. Model
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16,
    )

    model.to(DEVICE)
    model.gradient_checkpointing_enable()

    # 2. LoRA
    peft_config = LoraConfig(
        r=16,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        target_modules=[
            "q_proj","k_proj","v_proj","o_proj",
            "gate_proj","up_proj","down_proj"
        ],
        task_type=TaskType.CAUSAL_LM,
    )

    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # 3. Dataset
    train_dataset = BPMNDataset(
        os.path.join(DATA_DIR, "train.jsonl"),
        os.path.join(DATA_DIR, "images"),
        MODEL_ID,
    )

    # 4. Training args (MPS safe)
    args = TrainingArguments(
        output_dir="checkpoints_temp",
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        num_train_epochs=5,
        learning_rate=2e-4,
        logging_steps=5,
        save_strategy="no",

        fp16=True,      # 
        bf16=False,     # 

        optim="adamw_torch",
        remove_unused_columns=False,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        data_collator=collate_fn,
    )

    print(" Training started...")
    trainer.train()

    print(" Saving adapters + processor...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    model.save_pretrained(OUTPUT_DIR)
    processor.save_pretrained(OUTPUT_DIR)

    print("✅ Done.")

if __name__ == "__main__":
    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    train()
'''

# train.py (modified to log params & weights to MLflow)
import os
import json
import torch
import mlflow
from transformers import (
    Qwen3VLForConditionalGeneration,
    AutoProcessor,
    TrainingArguments,
    Trainer,
)
from peft import LoraConfig, get_peft_model, TaskType
from dataset import BPMNDataset, collate_fn

# =========================
# CONFIG (можно переопределить через env/args)
# =========================
MODEL_ID = "Qwen/Qwen3-VL-2B-Instruct"
OUTPUT_DIR = os.path.join("model_vlm_qwen3", "weights")
DATA_DIR = "data"

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

# hyperparams (пример — вынесите в argparse если нужно)
HYPERPARAMS = {
    "per_device_train_batch_size": 1,
    "gradient_accumulation_steps": 4,
    "num_train_epochs": 5,
    "learning_rate": 2e-4,
    "logging_steps": 5,
    "save_strategy": "no",
    "fp16": True,
    "bf16": False,
    "max_new_tokens": 384,
    "do_sample": False,
    "prompt_length": 512,
    "torch_dtype": "torch.float16",
    "min_pixels": 256 * 28 * 28,
    "max_pixels": 512 * 28 * 28,
    "kv_cache": True,
    "quantize": False,
}

def train():
    print("Using device:", DEVICE)

    # optional: set experiment name
    mlflow.set_experiment("qwen3vl-adapter-tuning")

    with mlflow.start_run() as run:
        # log params
        mlflow.log_params(HYPERPARAMS)
        mlflow.set_tag("base_model", MODEL_ID)
        mlflow.set_tag("dataset", DATA_DIR)
        mlflow.set_tag("device", str(DEVICE))

        # 0. Processor
        processor = AutoProcessor.from_pretrained(
            MODEL_ID,
            min_pixels=HYPERPARAMS["min_pixels"],
            max_pixels=HYPERPARAMS["max_pixels"],
        )

        # 1. Model
        model = Qwen3VLForConditionalGeneration.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float16,
        )
        model.to(DEVICE)
        model.gradient_checkpointing_enable()

        # 2. LoRA (пример)
        peft_config = LoraConfig(
            r=16,
            lora_alpha=16,
            lora_dropout=0.05,
            bias="none",
            target_modules=[
                "q_proj","k_proj","v_proj","o_proj",
                "gate_proj","up_proj","down_proj"
            ],
            task_type=TaskType.CAUSAL_LM,
        )

        model = get_peft_model(model, peft_config)
        model.print_trainable_parameters()

        # 3. Dataset
        train_dataset = BPMNDataset(
            os.path.join(DATA_DIR, "train.jsonl"),
            os.path.join(DATA_DIR, "images"),
            MODEL_ID,
        )

        # 4. Training args (MPS safe)
        args = TrainingArguments(
            output_dir="checkpoints_temp",
            per_device_train_batch_size=HYPERPARAMS["per_device_train_batch_size"],
            gradient_accumulation_steps=HYPERPARAMS["gradient_accumulation_steps"],
            num_train_epochs=HYPERPARAMS["num_train_epochs"],
            learning_rate=HYPERPARAMS["learning_rate"],
            logging_steps=HYPERPARAMS["logging_steps"],
            save_strategy=HYPERPARAMS["save_strategy"],
            fp16=HYPERPARAMS["fp16"],
            bf16=HYPERPARAMS["bf16"],
            optim="adamw_torch",
            remove_unused_columns=False,
            report_to="none",
        )

        trainer = Trainer(
            model=model,
            args=args,
            train_dataset=train_dataset,
            data_collator=collate_fn,
        )

        print(" Training started...")
        trainer.train()

        print("💾 Saving adapters + processor locally...")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        model.save_pretrained(OUTPUT_DIR)
        processor.save_pretrained(OUTPUT_DIR)

        # save params snapshot for reproducibility
        params_path = os.path.join(OUTPUT_DIR, "params.json")
        with open(params_path, "w", encoding="utf-8") as f:
            json.dump(HYPERPARAMS, f, indent=2)

        # log weights folder as artifact (mlflow stores all files inside)
        mlflow.log_artifacts(OUTPUT_DIR, artifact_path="weights")

        # you can also log a short summary metric (if available)
        mlflow.set_tag("weights_artifact", f"weights (run_id={run.info.run_id})")
        print(" Done.")

if __name__ == "__main__":
    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    train()
