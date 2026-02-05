import os
from ultralytics import YOLO

def train():
    
    model = YOLO('yolov8n.pt') 

    model.train(
        data='/Users/lubimaya/Desktop/programming/nexign_project/hybrid_model_arrows_blocks/arrows/dataset.yaml',
        epochs=150,          # Уменьшено
        patience=30,         # Ранняя остановка
        imgsz=1024,          
        batch=4,            
        workers=0,           
        device='mps',
        amp=False,           
        
        # Регуляризация против переобучения
        lr0=0.001,           
        lrf=0.01,           
        weight_decay=0.01,   
        label_smoothing=0.1,
        warmup_epochs=3.0,  
        
        # Аугментация (mosaic очень важен для мелких блоков)
        mosaic=1.0,          
        mixup=0.2,           
        degrees=10.0,         
        scale=0.5,           
        fliplr=0.5,          
        
        plots=True,
        save=True,
        project='hybrid_model_arrows_blocks/blocks',
        name='train_v10_stable'
    )
    
    print("\n🎯 ПРОВЕРКА ЛУЧШЕЙ МОДЕЛИ...")
    results = model.val()
    print(f"mAP50: {results.box.map50:.4f}")

if __name__ == '__main__':
    train()