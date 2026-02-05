'''import json
import os
import glob
import cv2
import shutil
import numpy as np
from sklearn.model_selection import train_test_split

# --- КОНФИГУРАЦИЯ ---
SOURCE_IMAGES = 'data2/dataset_arrows/images'
SOURCE_METADATA = 'data2/dataset_arrows/metadata'
OUTPUT_DIR = 'hybrid_model_arrows_blocks/arrows/dataset_yolo'

for split in ['train', 'val']:
    os.makedirs(os.path.join(OUTPUT_DIR, 'images', split), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, 'labels', split), exist_ok=True)

# 1. Жесткий ограничитель: YOLO не принимает ничего за пределами [0, 1]
def clamp_norm(val):
    return float(max(0.0, min(1.0, val)))

def normalize(val, max_val):
    if max_val <= 0: return 0.0
    return clamp_norm(val / max_val)



def create_yolo_label(arrow_data, img_w, img_h):
    points = arrow_data.get('points', [])
    if not points:
        return None

    if 'start' in arrow_data and 'end' in arrow_data:
        p_start = arrow_data['start']
        p_end = arrow_data['end']
    else:
        p_start = points[0]
        p_end = points[-1]

    all_x = [p['x'] for p in points]
    all_y = [p['y'] for p in points]
    
    # Считаем BBox
    pad = 2 # Уменьшил паддинг, чтобы меньше вылезало за края
    min_x = min(all_x) - pad
    max_x = max(all_x) + pad
    min_y = min(all_y) - pad
    max_y = max(all_y) + pad

    # Центрирование и нормализация с обязательным зажимом (clamping)
    box_w = (max_x - min_x)
    box_h = (max_y - min_y)
    cx = min_x + (box_w / 2)
    cy = min_y + (box_h / 2)

    n_cx = normalize(cx, img_w)
    n_cy = normalize(cy, img_h)
    n_w = normalize(box_w, img_w)
    n_h = normalize(box_h, img_h)

    # Ключевые точки: x, y, visibility
    # visibility: 2.0 - видимая, 1.0 - скрытая, 0.0 - нет точки
    kpts = []
    
    # Start Point
    kpts.append(normalize(p_start['x'], img_w))
    kpts.append(normalize(p_start['y'], img_h))
    kpts.append(2.0) 

    # End Point
    kpts.append(normalize(p_end['x'], img_w))
    kpts.append(normalize(p_end['y'], img_h))
    kpts.append(2.0) 

    # Формируем строку строго по формату YOLO Pose
    # class_id x_c y_c w h k1_x k1_y k1_v k2_x k2_y k2_v
    label_line = f"0 {n_cx:.6f} {n_cy:.6f} {n_w:.6f} {n_h:.6f} " + " ".join([f"{x:.6f}" for x in kpts])
    return label_line

# --- ОСНОВНОЙ ЦИКЛ ---
image_files = glob.glob(os.path.join(SOURCE_IMAGES, '*.png'))
print(f"Найдено изображений: {len(image_files)}")

# Очистка старых данных, если есть (чтобы не было путаницы)
if os.path.exists(OUTPUT_DIR):
    print("Очистка старой папки dataset_yolo...")
    # shutil.rmtree(OUTPUT_DIR) # Раскомментируй, если хочешь полную очистку

train_files, val_files = train_test_split(image_files, test_size=0.2, random_state=42)

def process_dataset(files, split_name):
    count = 0
    for img_path in files:
        filename = os.path.basename(img_path)
        json_name = filename.replace('.png', '.json')
        json_path = os.path.join(SOURCE_METADATA, json_name)

        if not os.path.exists(json_path):
            continue

        img = cv2.imread(img_path)
        if img is None: continue
        h, w = img.shape[:2]

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        yolo_lines = []
        if 'edges' in data: # Mermaid формат
            for edge in data['edges']:
                line = create_yolo_label(edge, w, h)
                if line: yolo_lines.append(line)
        elif 'points' in data: # Одиночная стрелка
             line = create_yolo_label(data, w, h)
             if line: yolo_lines.append(line)

        if yolo_lines:
            shutil.copy(img_path, os.path.join(OUTPUT_DIR, 'images', split_name, filename))
            txt_name = filename.replace('.png', '.txt')
            with open(os.path.join(OUTPUT_DIR, 'labels', split_name, txt_name), 'w') as out_f:
                out_f.write('\n'.join(yolo_lines))
            count += 1
    print(f"Обработано в {split_name}: {count} файлов")

process_dataset(train_files, 'train')
process_dataset(val_files, 'val')'''


import os
import json
import glob
import shutil
from sklearn.model_selection import train_test_split
import cv2

# ============= Настройки =============
# Убедись, что SOURCE_DIR совпадает с папкой из нового генератора
SOURCE_DIR = 'data2/dataset_arrows' 
OUTPUT_DIR = 'hybrid_model_arrows_blocks/arrows/dataset_yolo_arrows' 

CLASS_ARROW = 0 

def xyxy2yolo(x1, y1, x2, y2, w_img, h_img):
    cx = (x1 + x2) / 2.0 / w_img
    cy = (y1 + y2) / 2.0 / h_img
    bw = (x2 - x1) / w_img
    bh = (y2 - y1) / h_img
    return [cx, cy, bw, bh]

def process_pose_dataset():
    images = glob.glob(os.path.join(SOURCE_DIR, 'images', '*.jpg'))
    if not images:
        print(f"Ошибка: Не найдено картинок в {SOURCE_DIR}")
        return

    train_imgs, val_imgs = train_test_split(images, test_size=0.2, random_state=42)

    for split_name, split_imgs in [('train', train_imgs), ('val', val_imgs)]:
        save_img_dir = os.path.join(OUTPUT_DIR, 'images', split_name)
        save_lbl_dir = os.path.join(OUTPUT_DIR, 'labels', split_name)
        os.makedirs(save_img_dir, exist_ok=True)
        os.makedirs(save_lbl_dir, exist_ok=True)
        
        print(f"Конвертация POSE {split_name}: {len(split_imgs)} файлов...")
        
        for img_path in split_imgs:
            shutil.copy(img_path, save_img_dir)
            
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            json_path = os.path.join(SOURCE_DIR, 'metadata', base_name + '.json')
            
            img = cv2.imread(img_path)
            h_img, w_img = img.shape[:2]
            yolo_lines = []
            
            if os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    data = json.load(f)
                    
                for obj in data.get('arrows', []):
                    # 1. BBox (Берем из метаданных и нормализуем)
                    x1, y1, x2, y2 = obj['bbox']
                    bbox_yolo = xyxy2yolo(x1, y1, x2, y2, w_img, h_img)
                    
                    # 2. Точки (Приведение к 3-м точкам)
                    # ... внутри цикла по стрелкам ...
                    # 2. Точки (Приведение к 3-м точкам)
                    pts = obj['points'] 

                    if len(pts) < 2:
                        continue 

                    # Гарантированно берем 3 точки для Pose [3, 3]
                    p_start = pts[0]
                    p_end = pts[-1]
                    p_mid = pts[len(pts) // 2] 

                    final_points = [p_start, p_mid, p_end]

                    # 3. Нормализация Keypoints (ОСТАВЛЯЕМ ТОЛЬКО ЭТОТ БЛОК)
                    kpts_yolo = []
                    for p in final_points:
                        # Эта проверка важна: она «понимает» и [x, y], и {'x': x, 'y': y}
                        px, py = (p['x'], p['y']) if isinstance(p, dict) else (p[0], p[1])
                        kpts_yolo.extend([px / w_img, py / h_img, 2.0]) 
                    
                    # 4. Сборка строки: ID(0) + BBox(4) + Keypoints(9) = 14 значений
                    line = [0] + bbox_yolo + kpts_yolo
                    yolo_lines.append(" ".join(f"{v:.6f}" for v in line))

            with open(os.path.join(save_lbl_dir, base_name + '.txt'), 'w') as f:
                f.write('\n'.join(yolo_lines))

    # Создаем YAML для Pose Estimation с 3-мя точками
    yaml_path = os.path.join(OUTPUT_DIR, 'dataset.yaml')
    yaml_content = f"""
path: {os.path.abspath(OUTPUT_DIR)}
train: images/train
val: images/val

# Настройки ключевых точек: теперь их 3 (старт, изгиб/центр, конец)
kpt_shape: [3, 3]  
names:
  0: arrow
"""
    with open(yaml_path, 'w') as f:
        f.write(yaml_content.strip())
    
    print(f"\n✅ Датасет (3 точки) готов в {OUTPUT_DIR}")

if __name__ == "__main__":
    process_pose_dataset()