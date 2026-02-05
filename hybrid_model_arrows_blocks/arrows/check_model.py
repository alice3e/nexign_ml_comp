import cv2
from ultralytics import YOLO

# 1. Загрузка вашей обученной Pose-модели
model = YOLO('hybrid_model_arrows_blocks/arrows/weights/best.pt')

# 2. Выполнение предсказания
img_path = '/Users/lubimaya/Desktop/programming/nexign_project/Диаграммы. 2 часть/Picture/17.png'
results = model.predict(source=img_path, conf=0.4)

# 3. Загрузка картинки для рисования
img = cv2.imread(img_path)

for r in results:
    # Проверяем, нашла ли модель ключевые точки
    if r.keypoints is not None:
        # r.keypoints.xy - это тензор с координатами [N, 3, 2]
        # где N - кол-во стрелок, 3 - точки (старт, изгиб, конец), 2 - (x, y)
        all_kpts = r.keypoints.xy.cpu().numpy()

        for kpts in all_kpts:
            # Преобразуем в целые числа для OpenCV
            p1 = tuple(kpts[0].astype(int)) # Начало
            p2 = tuple(kpts[1].astype(int)) # Излом (мидл)
            p3 = tuple(kpts[2].astype(int)) # Конец

            # Рисуем ломаную линию: p1 -> p2 -> p3
            # Синий цвет для самой линии
            cv2.line(img, p1, p2, (255, 0, 0), 2)
            cv2.line(img, p2, p3, (255, 0, 0), 2)

            # Опционально: помечаем точки разными цветами, чтобы проверить логику
            cv2.circle(img, p1, 4, (0, 255, 0), -1)  # Зеленый - Старт
            cv2.circle(img, p2, 4, (0, 255, 255), -1)# Желтый - Излом
            cv2.circle(img, p3, 5, (0, 0, 255), -1)  # Красный - Конец (наконечник)

# 4. Сохранение и показ
cv2.imwrite('/Users/lubimaya/Desktop/programming/nexign_project/Диаграммы. 2 часть/Picture/1.png', img)
cv2.imshow('Result', img)
cv2.waitKey(0)