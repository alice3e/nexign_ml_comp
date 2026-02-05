import json
import os
import glob
import cv2
import shutil
from sklearn.model_selection import train_test_split


SOURCE_IMAGES = 'data2/dataset_blocks/images'
SOURCE_METADATA = 'data2/dataset_blocks/metadata'
OUTPUT_DIR = 'hybrid_model_arrows_blocks/blocks/dataset_yolo_blocks'

CLASS_MAP = {
    'activity_task': 0,
    'activity_process_step': 1,
    'event_start': 2,
    'event_end': 3,
    'event_intermediate': 4,
    'event_timer': 5,
    'event_message': 6,
    'event_user': 7,
    'gateway_exclusive': 8,
    'gateway_parallel': 9,
    'gateway_empty': 10,
    'oval': 11,
    'artifact': 12
}

def get_detailed_class_name(item):
    
    return item.get('class') 
for split in ['train', 'val']:
    os.makedirs(os.path.join(OUTPUT_DIR, 'images', split), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, 'labels', split), exist_ok=True)

def convert_bbox(bbox, img_w, img_h):
    xmin, ymin, xmax, ymax = bbox
    w = xmax - xmin
    h = ymax - ymin
    cx = xmin + (w / 2)
    cy = ymin + (h / 2)
    
    # Нормализация для YOLO
    return cx / img_w, cy / img_h, w / img_w, h / img_h

def process_dataset(files, split_name):
    for img_path in files:
        filename = os.path.basename(img_path)
        json_name = filename.replace('.png', '.json')
        json_path = os.path.join(SOURCE_METADATA, json_name)

        if not os.path.exists(json_path):
            continue

        img = cv2.imread(img_path)
        if img is None: continue
        h_img, w_img = img.shape[:2]

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except: continue
        
        yolo_lines = []
        for item in data:
            if item is None: continue # На всякий случай
            
            bbox = item.get('bbox')
            detailed_name = get_detailed_class_name(item)
            
            # Теперь detailed_name будет 'event_timer', 'activity_task' и т.д.
            if detailed_name not in CLASS_MAP:
                print(f"Warning: Unknown class {detailed_name} in {filename}")
                continue
                
            cls_id = CLASS_MAP[detailed_name]
            nx, ny, nw, nh = convert_bbox(bbox, w_img, h_img)
            yolo_lines.append(f"{cls_id} {nx:.6f} {ny:.6f} {nw:.6f} {nh:.6f}")

        if yolo_lines:
            shutil.copy(img_path, os.path.join(OUTPUT_DIR, 'images', split_name, filename))
            txt_name = os.path.splitext(filename)[0] + '.txt'
            with open(os.path.join(OUTPUT_DIR, 'labels', split_name, txt_name), 'w') as out_f:
                out_f.write('\n'.join(yolo_lines))

# --- ЗАПУСК ---
image_files = glob.glob(os.path.join(SOURCE_IMAGES, '*.png'))
print(f"Найдено изображений: {len(image_files)}")

if len(image_files) > 0:
    train_files, val_files = train_test_split(image_files, test_size=0.2, random_state=42)
    process_dataset(train_files, 'train')
    process_dataset(val_files, 'val')
    print(f"Готово! Данные сохранены в: {OUTPUT_DIR}")
else:
    print("Ошибка: Изображения не найдены. Проверь путь SOURCE_IMAGES.")