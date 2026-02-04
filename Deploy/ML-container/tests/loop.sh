#!/bin/bash

# Директория, где лежат изображения и куда будут сохраняться JSON-ответы
DIR="."

# Цикл по номерам от 1 до 9
for i in {1..9}; do
    # Путь к изображению
    IMAGE_FILE="$DIR/$i.png"
    
    # Проверяем, существует ли файл изображения
    if [ ! -f "$IMAGE_FILE" ]; then
        echo "Файл $IMAGE_FILE не найден, пропускаем..."
        continue
    fi

    # Отправляем запрос с изображением и сохраняем ответ в переменную
    RESPONSE=$(curl -s -X POST "http://localhost:8002/infer" -F "file=@$IMAGE_FILE")
    
    # Путь для сохранения JSON-ответа
    JSON_FILE="$DIR/$i.json"
    
    # Сохраняем ответ в JSON-файл
    echo "$RESPONSE" > "$JSON_FILE"
    
    # Уведомление о завершении обработки файла
    echo "Обработано изображение $i.jpg, ответ сохранён в $JSON_FILE"
done

echo "Все изображения обработаны."
