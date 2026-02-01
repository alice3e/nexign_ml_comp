import json
import random
import os

DATA_DIR = "data"
INPUT_FILE = os.path.join(DATA_DIR, "metadata.jsonl")
TRAIN_FILE = os.path.join(DATA_DIR, "train.jsonl")
VAL_FILE = os.path.join(DATA_DIR, "val.jsonl")

def main():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Перемешиваем
    random.seed(42)
    random.shuffle(lines)
    
    # Разбиваем 90/10
    split_idx = int(len(lines) * 0.9)
    train_data = lines[:split_idx]
    val_data = lines[split_idx:]
    
    with open(TRAIN_FILE, 'w', encoding='utf-8') as f:
        f.writelines(train_data)
        
    with open(VAL_FILE, 'w', encoding='utf-8') as f:
        f.writelines(val_data)
        
    print(f"Готово! Train: {len(train_data)}, Val: {len(val_data)}")

if __name__ == "__main__":
    main()