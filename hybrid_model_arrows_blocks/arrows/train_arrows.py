import os
from ultralytics import YOLO

DATASET_YAML = '/Users/lubimaya/Desktop/programming/nexign_project/hybrid_model_arrows_blocks/arrows/dataset.yaml'
PROJECT_NAME = 'runs/arrow_pose_3pts'
EXP_NAME = 'stable_v3_small_model' # Поменяли имя для новой попытки

def train_model():
    # Заменяем 'n' на 's' (Small). Она чуть тяжелее, но на порядок лучше ловит паттерны.
    model = YOLO('yolov8s-pose.pt') 
    os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
    results = model.train(
        data=DATASET_YAML,
        epochs=50,           # 40 эпох мало для 's' модели, лучше поставить 100 с patience
        patience=20,          # Если 20 эпох не улучшается — остановимся сами
        imgsz=640,            
        batch=16,             
        
        # --- ГЕОМЕТРИЯ (Важно для стрелок) ---
        #mosaic=0.5,           # Верни мозаику! Для стрелок она полезна, чтобы видеть их под разным углом
        mixup=0.1,            # Добавим немного смешивания для обобщения
        
        # --- ОПТИМИЗАЦИЯ ---
        lr0=0.01,             # Для AdamW 0.001 может быть слишком медленным стартом
        optimizer='AdamW',
        weight_decay=0.0005,
        
        project=PROJECT_NAME,
        name=EXP_NAME,
        
        # Параметры Pose (Keypoints)
        pose=12.0,            # Увеличиваем важность попадания в ключевые точки
        kobj=1.0,             
        
        # СИСТЕМНЫЕ
        device='mps',
        plots=True            
    )
    
    print("\n--- Валидация модели ---")
    model.val()
    
    return results

if __name__ == '__main__':
    train_model()