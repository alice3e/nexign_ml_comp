# dataset.py
import json
import os
from typing import List, Optional

import torch
from torch.utils.data import Dataset
from PIL import Image
from transformers import AutoProcessor

from qwen_vl_utils import process_vision_info

class BPMNDataset(Dataset):
    """
    Универсальный датасет для Qwen-2 / Qwen-3. Гарантирует, что целевой текст
    (labels) начинается с требуемого заголовка таблицы:
      | № | Наименование действия | Роль |
    и использует apply_chat_template(add_generation_prompt=False) везде.
    """
    REQUIRED_HEADER = "| № | Наименование действия | Роль |"

    def __init__(self, jsonl_file: str, image_dir: str, processor_id: str,
                 min_pixels: Optional[int] = 256*28*28,
                 max_pixels: Optional[int] = 512*28*28):
        self.data: List[dict] = []
        self.image_dir = image_dir

        # Загружаем процессор с теми же аргументами, что и в Qwen2-скрипте
        proc_kwargs = {}
        if min_pixels is not None:
            proc_kwargs["min_pixels"] = min_pixels
        if max_pixels is not None:
            proc_kwargs["max_pixels"] = max_pixels
        self.processor = AutoProcessor.from_pretrained(processor_id, **proc_kwargs)

        # Загружаем jsonl
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                self.data.append(json.loads(line))

        # Жёсткая системная инструкция — одинаковая в train и inference
        self.system_prompt = (
            "Ты эксперт по BPMN. Выдавай ответ строго в формате Markdown-таблицы. "
            "Заголовок таблицы должен быть точно: | № | Наименование действия | Роль |. "
            "Никаких дополнительных колонок или других названий заголовков."
        )

    def __len__(self) -> int:
        return len(self.data)

    def _build_conversation(self, image: Image.Image, target_text: str):
        # conversation формируется в том же виде, что и в исходном коде
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
                "content": [{"type": "text", "text": target_text}],
            },
        ]
        return conversation

    def _apply_chat_template(self, conversation):
        # Всегда вызываем apply_chat_template с add_generation_prompt=False
        if hasattr(self.processor, "apply_chat_template"):
            return self.processor.apply_chat_template(conversation, tokenize=False, add_generation_prompt=False)
        # Fallback — конкатенация текстов и маркер [Image]
        parts = []
        for msg in conversation:
            for content in msg.get("content", []):
                if content.get("type") == "text":
                    parts.append(content.get("text", ""))
                elif content.get("type") == "image":
                    parts.append("[Image]")
        return "\n\n".join(parts)

    def __getitem__(self, idx: int):
        item = self.data[idx]
        image_path = os.path.join(self.image_dir, item['file_name'])
        image = Image.open(image_path).convert("RGB")

        # Гарантируем, что таргет начинается с REQUIRED_HEADER
        target = item.get("text", "").lstrip()
        if not target.startswith(self.REQUIRED_HEADER):
            target = self.REQUIRED_HEADER + "\n\n" + target

        conversation = self._build_conversation(image, target)

        # Текстовая часть
        text = self._apply_chat_template(conversation)

        image_inputs, video_inputs = process_vision_info(conversation)

        proc_kwargs = {
            "text": [text],
            "padding": True,
            "return_tensors": "pt",
        }
        if image_inputs is not None:
            proc_kwargs["images"] = image_inputs
        if video_inputs is not None:
            proc_kwargs["videos"] = video_inputs

        inputs = self.processor(**proc_kwargs)

        input_ids = inputs.get("input_ids")
        attention_mask = inputs.get("attention_mask")
        pixel_values = inputs.get("pixel_values")
        image_grid_thw = inputs.get("image_grid_thw")

        if input_ids is None or attention_mask is None:
            raise RuntimeError("Processor не вернул input_ids/attention_mask — проверьте совместимость processor_id.")

        # Нормализуем pixel_values/list -> tensor
        if pixel_values is not None and isinstance(pixel_values, list):
            pixel_values = torch.stack(pixel_values)
        if image_grid_thw is not None and isinstance(image_grid_thw, list):
            image_grid_thw = torch.stack(image_grid_thw)

        return {
            "input_ids": input_ids.squeeze(0),
            "attention_mask": attention_mask.squeeze(0),
            "pixel_values": pixel_values.squeeze(0) if pixel_values is not None else None,
            "image_grid_thw": image_grid_thw.squeeze(0) if image_grid_thw is not None else None,
            "labels": input_ids.squeeze(0).clone(),  # labels = input_ids (в Trainer можно смещать/маскировать)
        }


def collate_fn(batch: List[dict]):
    input_ids = torch.nn.utils.rnn.pad_sequence([x["input_ids"] for x in batch], batch_first=True, padding_value=0)
    attention_mask = torch.nn.utils.rnn.pad_sequence([x["attention_mask"] for x in batch], batch_first=True, padding_value=0)

    pixel_values_list = [x["pixel_values"] for x in batch if x.get("pixel_values") is not None]
    pixel_values = torch.stack(pixel_values_list) if len(pixel_values_list) > 0 else None

    image_grid_list = [x["image_grid_thw"] for x in batch if x.get("image_grid_thw") is not None]
    image_grid_thw = torch.stack(image_grid_list) if len(image_grid_list) > 0 else None

    labels = torch.nn.utils.rnn.pad_sequence([x["labels"] for x in batch], batch_first=True, padding_value=-100)

    out = {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels,
    }
    if pixel_values is not None:
        out["pixel_values"] = pixel_values
    if image_grid_thw is not None:
        out["image_grid_thw"] = image_grid_thw

    return out
