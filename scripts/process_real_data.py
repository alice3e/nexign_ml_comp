import os
import shutil
import zipfile
import tarfile
from pathlib import Path
from tqdm import tqdm
from PIL import Image
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

# Конфигурация
RAW_DIR = Path("raw_data")
OUTPUT_DIR = Path("data/real_images")
TEMP_EXTRACT_DIR = Path("temp_extracted")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Поддерживаемые форматы изображений
VALID_IMAGES = {'.png', '.jpg', '.jpeg', '.bmp'}
# Форматы, которые попробуем конвертировать
CONVERTIBLE_IMAGES = {'.svg'}
# Архивы
ARCHIVES = {'.zip', '.tar', '.gz'}

def extract_archives(root_dir):
    """Рекурсивно ищет и распаковывает архивы"""
    print("🔍 Сканирование и распаковка архивов...")
    # Превращаем в список, чтобы не ломать итератор при добавлении новых файлов
    archives = [p for p in root_dir.rglob("*") if p.suffix.lower() in ARCHIVES]
    
    for archive_path in tqdm(archives):
        try:
            extract_path = TEMP_EXTRACT_DIR / archive_path.stem
            extract_path.mkdir(parents=True, exist_ok=True)
            
            if archive_path.suffix.lower() == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
            elif archive_path.suffix.lower() in ['.tar', '.gz']:
                with tarfile.open(archive_path) as tar:
                    tar.extractall(extract_path)
            
            # После распаковки запускаем поиск снова внутри распакованного (рекурсия для вложенных zip)
            # Но для простоты пока оставим один уровень
        except Exception as e:
            print(f" Ошибка распаковки {archive_path}: {e}")

def convert_svg_to_png(svg_path, output_path):
    try:
        drawing = svg2rlg(str(svg_path))
        renderPM.drawToFile(drawing, str(output_path), fmt="PNG")
        return True
    except Exception as e:
        # print(f"Не удалось конвертировать SVG {svg_path.name}")
        return False

def process_files():
    print("Сбор и обработка изображений...")
    
    # Ищем файлы и в raw_data, и во временно распакованных
    search_dirs = [RAW_DIR, TEMP_EXTRACT_DIR]
    
    counter = 0
    
    for source_dir in search_dirs:
        if not source_dir.exists(): continue
        
        for file_path in tqdm(list(source_dir.rglob("*"))):
            if file_path.is_dir(): continue
            
            ext = file_path.suffix.lower()
            target_name = f"real_{counter:04d}.png"
            target_path = OUTPUT_DIR / target_name
            
            processed = False
            
            # 1. Если это обычная картинка -> копируем и конвертируем в PNG
            if ext in VALID_IMAGES:
                try:
                    with Image.open(file_path) as img:
                        img = img.convert("RGB") # Убираем прозрачность, приводим к стандарту
                        img.save(target_path, "PNG")
                        processed = True
                except Exception as e:
                    pass
            
            # 2. Если это SVG -> конвертируем
            elif ext in CONVERTIBLE_IMAGES:
                processed = convert_svg_to_png(file_path, target_path)
            
            if processed:
                counter += 1

    print(f"Готово! Обработано изображений: {counter}")
    print(f"📂 Результат в папке: {OUTPUT_DIR}")
    
    # Чистим временные файлы
    if TEMP_EXTRACT_DIR.exists():
        shutil.rmtree(TEMP_EXTRACT_DIR)

if __name__ == "__main__":
    # 1. Сначала распакуем zip-архивы
    extract_archives(RAW_DIR)
    # 2. Потом соберем все картинки
    process_files()
    
    print("\n ВНИМАНИЕ:")
    print("Файлы .bpmn, .drawio, .puml, .vsdx НЕ были обработаны.")
    print("Их нужно экспортировать в PNG вручную через Draw.io или Camunda Modeler,")
    print("так как Python не может отрисовать их без внешнего графического движка.")