import json
import os
import torch
from torch.utils.data import Dataset
from PIL import Image
from transformers import AutoProcessor
from qwen_vl_utils import process_vision_info

class BPMNDataset(Dataset):
    def __init__(self, jsonl_file, image_dir, processor_id):
        self.data = []
        self.image_dir = image_dir
        # Загружаем процессор
        self.processor = AutoProcessor.from_pretrained(processor_id, min_pixels=256*28*28, max_pixels=512*28*28)
        
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                self.data.append(json.loads(line))
                
        self.system_prompt = "Ты эксперт по BPMN. Твоя задача — проанализировать диаграмму и создать структурированную таблицу Markdown с шагами алгоритма."

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        
        image_path = os.path.join(self.image_dir, item['file_name'])
        image = Image.open(image_path).convert("RGB")
        
        conversation = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": self.system_prompt},
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": item['text']},
                ],
            },
        ]

        # Подготовка через processor
        text = self.processor.apply_chat_template(
            conversation, tokenize=False, add_generation_prompt=False
        )
        
        image_inputs, video_inputs = process_vision_info(conversation)
        
        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        
        return {
            "input_ids": inputs["input_ids"].squeeze(0),
            "attention_mask": inputs["attention_mask"].squeeze(0),
            "pixel_values": inputs["pixel_values"].squeeze(0),
            "image_grid_thw": inputs["image_grid_thw"].squeeze(0),
            "labels": inputs["input_ids"].squeeze(0)
        }

def collate_fn(batch):
    return {
        "input_ids": torch.stack([x["input_ids"] for x in batch]),
        "attention_mask": torch.stack([x["attention_mask"] for x in batch]),
        "pixel_values": torch.cat([x["pixel_values"] for x in batch]), # Pixel values flatten list
        "image_grid_thw": torch.stack([x["image_grid_thw"] for x in batch]),
        "labels": torch.stack([x["labels"] for x in batch])
    }