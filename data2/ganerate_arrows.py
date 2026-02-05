import os
import json
import math
import random
from PIL import Image, ImageDraw, ImageFont

# ============================
# НАСТРОЙКИ
# ============================
NUM_IMAGES = 1000  
OUT_DIR = "dataset_arrows_full_path"
IM_DIR = os.path.join(OUT_DIR, "images")
META_DIR = os.path.join(OUT_DIR, "metadata")
CANVAS_SIZE = (640, 640) 

os.makedirs(IM_DIR, exist_ok=True)
os.makedirs(META_DIR, exist_ok=True)

ARROW_COLORS = [(0, 0, 0), (30, 30, 30), (60, 60, 60)] 
DISTRACTOR_COLORS = [(100, 100, 100), (150, 150, 150), (200, 200, 200)]
BG_COLORS = [(255, 255, 255)]

def draw_distractors(draw, w, h):
    """Рисует посторонние предметы, которые НЕ являются стрелками"""
    for _ in range(random.randint(2, 6)):
        shape_type = random.choice(['rect', 'oval', 'line', 'text'])
        color = random.choice(DISTRACTOR_COLORS)
        x1, y1 = random.randint(0, w), random.randint(0, h)
        x2, y2 = random.randint(x1, min(x1+100, w)), random.randint(y1, min(y1+60, h))

        if shape_type == 'rect':
            draw.rectangle([x1, y1, x2, y2], outline=color, width=random.randint(1, 2))
        elif shape_type == 'oval':
            draw.ellipse([x1, y1, x2, y2], outline=color, width=random.randint(1, 2))
        elif shape_type == 'line':
            # Линия БЕЗ наконечника - отличный негативный пример
            draw.line([(x1, y1), (x2, y2)], fill=color, width=random.randint(1, 2))
        elif shape_type == 'text':
            # Имитация текста (просто набор символов)
            chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
            fake_text = "".join(random.choices(chars, k=random.randint(3, 8)))
            draw.text((x1, y1), fake_text, fill=color)

def draw_arrow_full(draw, path, color, width=1, head_size=10):
    """Рисует путь и наконечник"""
    draw.line(path, fill=color, width=width, joint="curve")
    
    p_last = path[-1]
    p_prev = path[-2]
    angle = math.atan2(p_last[1] - p_prev[1], p_last[0] - p_prev[0])
    
    actual_head = head_size if width > 1 else head_size - 2
    
    al, ar = angle + math.pi - 0.45, angle + math.pi + 0.45
    lx = p_last[0] + actual_head * math.cos(al)
    ly = p_last[1] + actual_head * math.sin(al)
    rx = p_last[0] + actual_head * math.cos(ar)
    ry = p_last[1] + actual_head * math.sin(ar)
    
    draw.polygon([p_last, (lx, ly), (rx, ry)], fill=color)

def generate_scene(idx):
    w, h = CANVAS_SIZE
    img = Image.new("RGB", (w, h), random.choice(BG_COLORS))
    d = ImageDraw.Draw(img)
    
    # 1. Сначала рисуем посторонние предметы (на заднем плане)
    draw_distractors(d, w, h)
    
    objects_meta = []
    num_arrows = random.randint(4, 10)

    # 2. Рисуем стрелки (на переднем плане)
    for _ in range(num_arrows):
        p_start = (random.randint(20, w-20), random.randint(20, h-20))
        p_end = (random.randint(20, w-20), random.randint(20, h-20))
        
        if math.hypot(p_start[0]-p_end[0], p_start[1]-p_end[1]) < 30:
            continue

        rand_val = random.random()
        if rand_val < 0.2:
            path = [p_start, p_end]
        elif rand_val < 0.8:
            mid = (p_end[0], p_start[1]) if random.random() > 0.5 else (p_start[0], p_end[1])
            path = [p_start, mid, p_end]
        else:
            m1_x = p_start[0] + (p_end[0] - p_start[0]) * random.uniform(0.3, 0.7)
            path = [p_start, (m1_x, p_start[1]), (m1_x, p_end[1]), p_end]

        current_width = 1 if random.random() < 0.7 else random.randint(2, 3)
        draw_arrow_full(d, path, random.choice(ARROW_COLORS), width=current_width)

        xs, ys = [p[0] for p in path], [p[1] for p in path]
        pad = 10 
        bbox = [
            float(min(xs) - pad), 
            float(min(ys) - pad), 
            float(max(xs) + pad), 
            float(max(ys) + pad)
        ]

        objects_meta.append({
            "bbox": bbox,
            "points": [[float(p[0]), float(p[1])] for p in path],
            "width": current_width
        })

    img.save(f"{IM_DIR}/{idx:06d}.jpg")
    with open(f"{META_DIR}/{idx:06d}.json", "w") as f:
        json.dump({
            "image_id": idx,
            "size": CANVAS_SIZE,
            "arrows": objects_meta
        }, f, indent=2)

if __name__ == "__main__":
    print(f"Генерация датасета с помехами в {OUT_DIR}...")
    for i in range(NUM_IMAGES):
        generate_scene(i)
        if i % 100 == 0: print(f"Сгенерировано: {i}")
    print("Готово!")