import cv2
import json
import numpy as np
from ultralytics import YOLO
import easyocr
import os
import math

# --- НАСТРОЙКИ ---
PATH_TO_BLOCK_MODEL = 'hybrid_model_arrows_blocks/blocks/weights/best.pt'
PATH_TO_ARROW_MODEL = 'hybrid_model_arrows_blocks/arrows/weights/best.pt'

ID_TO_CLASS = {
    0: 'task', 1: 'process_step', 2: 'start_event', 3: 'end_event',
    4: 'intermediate_event', 5: 'timer_event', 6: 'message_event',
    7: 'user_event', 8: 'exclusive_gateway', 9: 'parallel_gateway',
    10: 'inclusive_gateway', 11: 'oval', 12: 'artifact'
}

# Класс для анализа дорожек (тот же, что работал у нас ранее)
class SwimlaneAnalyzer:
    def __init__(self, reader):
        self.reader = reader

    def preprocess_role_crop(self, crop):
        if crop.size == 0: return None
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        upscaled = cv2.resize(gray, None, fx=4.0, fy=4.0, interpolation=cv2.INTER_CUBIC)
        kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]]) # Sharpening
        sharpened = cv2.filter2D(upscaled, -1, kernel)
        _, binary = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        final = cv2.copyMakeBorder(binary, 50, 50, 50, 50, cv2.BORDER_CONSTANT, value=255)
        return final

    def find_lanes(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        H, W = gray.shape
        binary = cv2.adaptiveThreshold(~gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2)

        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (W // 5, 1))
        horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
        
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, H // 4))
        vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
        
        roi_w = int(W * 0.15)
        v_col_sums = np.sum(vertical_lines[:, :roi_w], axis=0)
        
        if np.max(v_col_sums) > 0:
            header_sep_x = np.argmax(v_col_sums)
        else:
            header_sep_x = 0
            
        if header_sep_x < 20: header_sep_x = 100 # Эвристика: если линии нет, берем 100px

        h_row_sums = np.sum(horizontal_lines, axis=1)
        line_indices = np.where(h_row_sums > 255 * (W * 0.4))[0]

        y_coords = [0]
        if len(line_indices) > 0:
            last_y = line_indices[0]
            for y in line_indices:
                if y - last_y > 15: y_coords.append(int(last_y))
                last_y = y
            y_coords.append(int(last_y))
        y_coords.append(H)
        y_coords = sorted(list(set(y_coords)))

        lanes = []
        print(f"-> Анализ {len(y_coords)-1} дорожек...")
        
        for i in range(len(y_coords) - 1):
            y_start = y_coords[i]
            y_end = y_coords[i+1]
            if y_end - y_start < 40: continue 
            
            header_crop = img[y_start:y_end, 0:header_sep_x+10]
            role_name = "Unknown"
            
            if header_crop.size > 0:
                processed = self.preprocess_role_crop(header_crop)
                candidates = []
                try:
                    res = self.reader.readtext(cv2.rotate(processed, cv2.ROTATE_90_CLOCKWISE), detail=0)
                    if res: candidates.append((" ".join(res).strip(), 3))
                except: pass
                try:
                    res = self.reader.readtext(cv2.rotate(processed, cv2.ROTATE_90_COUNTERCLOCKWISE), detail=0)
                    if res: candidates.append((" ".join(res).strip(), 2))
                except: pass
                
                if candidates:
                    role_name = max(candidates, key=lambda x: len(x[0]))[0]

            lanes.append({"role": role_name, "y_min": y_start, "y_max": y_end})

        return lanes, header_sep_x
import cv2
import json
import numpy as np
from ultralytics import YOLO
import easyocr
import os
import math
import torch
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# --- НАСТРОЙКИ ---
PATH_TO_BLOCK_MODEL = 'hybrid_model_arrows_blocks/blocks/weights/best.pt'
PATH_TO_ARROW_MODEL = 'hybrid_model_arrows_blocks/arrows/weights/best.pt'

ID_TO_CLASS = {
    0: 'task', 1: 'process_step', 2: 'start_event', 3: 'end_event',
    4: 'intermediate_event', 5: 'timer_event', 6: 'message_event',
    7: 'user_event', 8: 'exclusive_gateway', 9: 'parallel_gateway',
    10: 'inclusive_gateway', 11: 'oval', 12: 'artifact'
}

# --- КЛАССЫ АНАЛИЗА ИЗОБРАЖЕНИЙ ---

class SwimlaneAnalyzer:
    def __init__(self, reader):
        self.reader = reader

    def preprocess_role_crop(self, crop):
        if crop.size == 0: return None
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        upscaled = cv2.resize(gray, None, fx=4.0, fy=4.0, interpolation=cv2.INTER_CUBIC)
        kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
        sharpened = cv2.filter2D(upscaled, -1, kernel)
        _, binary = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        final = cv2.copyMakeBorder(binary, 50, 50, 50, 50, cv2.BORDER_CONSTANT, value=255)
        return final

    def find_lanes(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        H, W = gray.shape
        binary = cv2.adaptiveThreshold(~gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2)
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (W // 5, 1))
        horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, H // 4))
        vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
        
        roi_w = int(W * 0.15)
        v_col_sums = np.sum(vertical_lines[:, :roi_w], axis=0)
        header_sep_x = np.argmax(v_col_sums) if np.max(v_col_sums) > 0 else 100
        if header_sep_x < 20: header_sep_x = 100

        h_row_sums = np.sum(horizontal_lines, axis=1)
        line_indices = np.where(h_row_sums > 255 * (W * 0.4))[0]
        y_coords = [0]
        if len(line_indices) > 0:
            last_y = line_indices[0]
            for y in line_indices:
                if y - last_y > 15: y_coords.append(int(last_y))
                last_y = y
            y_coords.append(int(last_y))
        y_coords.append(H)
        y_coords = sorted(list(set(y_coords)))

        lanes = []
        for i in range(len(y_coords) - 1):
            y_start, y_end = y_coords[i], y_coords[i+1]
            if y_end - y_start < 40: continue 
            header_crop = img[y_start:y_end, 0:header_sep_x+10]
            role_name = "none"
            if header_crop.size > 0:
                processed = self.preprocess_role_crop(header_crop)
                candidates = []
                for rot in [cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_90_COUNTERCLOCKWISE]:
                    try:
                        res = self.reader.readtext(cv2.rotate(processed, rot), detail=0)
                        if res: candidates.append(" ".join(res).strip())
                    except: pass
                if candidates:
                    role_name = max(candidates, key=len)
            lanes.append({"role": role_name, "y_min": y_start, "y_max": y_end})
        return lanes, header_sep_x

class DiagramParser:
    def __init__(self):
        print("Загрузка CV моделей...")
        self.model_blocks = YOLO(PATH_TO_BLOCK_MODEL)
        self.model_arrows = YOLO(PATH_TO_ARROW_MODEL)
        self.reader = easyocr.Reader(['ru', 'en'], gpu=torch.cuda.is_available()) 
        self.lane_analyzer = SwimlaneAnalyzer(self.reader)

    def enhance_text_image(self, crop):
        if crop.size == 0: return crop
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        upscaled = cv2.resize(gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(upscaled)
        return cv2.copyMakeBorder(enhanced, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)

    def get_closest_node(self, point, nodes, threshold=100):
        min_dist, closest_id = float('inf'), None
        px, py = point
        for node in nodes:
            nx1, ny1, nx2, ny2 = node['bbox']
            dist = math.sqrt((px - (nx1+nx2)/2)**2 + (py - (ny1+ny2)/2)**2)
            node_radius = min(nx2-nx1, ny2-ny1) / 2
            eff_dist = max(0, dist - node_radius)
            if eff_dist < min_dist:
                min_dist, closest_id = eff_dist, node['id']
        return closest_id if min_dist < threshold else None

    def process_image(self, image_path):
        img = cv2.imread(image_path)
        if img is None: return None
        lanes, _ = self.lane_analyzer.find_lanes(img)
        res_b = self.model_blocks.predict(img, conf=0.1, verbose=False)[0]
        nodes = []
        for i, box in enumerate(res_b.boxes):
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            cy = (y1 + y2) // 2
            role = next((l['role'] for l in lanes if l['y_min'] <= cy <= l['y_max']), "none")
            nodes.append({"id": f"n{i+1}", "class": ID_TO_CLASS.get(int(box.cls[0]), "element"),
                          "bbox": [x1, y1, x2, y2], "role": role, "text": ""})

        for n in nodes:
            x1, y1, x2, y2 = n['bbox']
            crop = img[y1+4:y2-4, x1+4:x2-4]
            if crop.size > 0:
                try:
                    res = self.reader.readtext(self.enhance_text_image(crop), detail=0, paragraph=True)
                    n['text'] = " ".join(res).strip()
                except: pass

        res_a = self.model_arrows.predict(img, conf=0.2, verbose=False)[0]
        arrows = []
        for i, box in enumerate(res_a.boxes):
            ax1, ay1, ax2, ay2 = map(int, box.xyxy[0].tolist())
            p_start, p_end = ((ax1, (ay1+ay2)//2), (ax2, (ay1+ay2)//2)) if (ax2-ax1) > (ay2-ay1) else (((ax1+ax2)//2, ay1), ((ax1+ax2)//2, ay2))
            s_id, t_id = self.get_closest_node(p_start, nodes), self.get_closest_node(p_end, nodes)
            if s_id != t_id:
                arrows.append({"id": f"a{i+1}", "source": s_id, "target": t_id})

        return {"file_name": os.path.basename(image_path), "nodes": nodes, "arrows": arrows}

    def save_to_markdown(self, data, output_path):
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        content = f"# BPMN Graph Export File: `{data['file_name']}`\n\n```json\n{json_str}\n```"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

# --- КЛАСС ГЕНЕРАЦИИ ТАБЛИЦЫ (LLM) ---

class LLMTableGenerator:
    def __init__(self, model_id="Qwen/Qwen2.5-3B-Instruct"):
        print(f"Загрузка LLM {model_id}...")
        self.pipe = pipeline(
            "text-generation",
            model=model_id,
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )

    def generate_table(self, graph_data):
        # Оставляем только узлы с текстом
        items = [{"text": n['text'], "role": n['role']} for n in graph_data['nodes'] if n['text'].strip()]
        has_roles = any(i['role'] != "none" for i in items)
        
        prompt = f"""Преобразуй данные в Markdown таблицу. 
Правила:
1. Столбцы: №, Наименование действия{', Роль' if has_roles else ''}.
2. Роль пиши только если она не "none".
3. Выведи только таблицу.

Данные:
{json.dumps(items, ensure_ascii=False)}"""

        messages = [
            {"role": "system", "content": "You are a professional business analyst. Output only markdown tables."},
            {"role": "user", "content": prompt}
        ]
        
        output = self.pipe(messages, max_new_tokens=1024, temperature=0.1)
        return output[0]['generated_text'][-1]['content']

# --- ЗАПУСК ---

if __name__ == "__main__":
    path_to_img = "diagram.png" # Укажите ваше фото
    
    if os.path.exists(path_to_img):
        parser = DiagramParser()
        graph = parser.process_image(path_to_img)
        
        if graph:
            parser.save_to_markdown(graph, "graph_raw.md")
            
            # Генерация таблицы через LLM
            llm = LLMTableGenerator()
            table = llm.generate_table(graph)
            
            with open("final_report.md", "w", encoding="utf-8") as f:
                f.write(f"# Отчет по диаграмме {path_to_img}\n\n{table}")
            
            print("\n--- ГОТОВАЯ ТАБЛИЦА ---")
            print(table)
    else:
        print("Файл изображения не найден.")
class DiagramParser:
    def __init__(self):
        print("Загрузка моделей...")
        self.model_blocks = YOLO(PATH_TO_BLOCK_MODEL)
        self.model_arrows = YOLO(PATH_TO_ARROW_MODEL)
        self.reader = easyocr.Reader(['ru', 'en'], gpu=False) 
        self.lane_analyzer = SwimlaneAnalyzer(self.reader)

    def enhance_text_image(self, crop):
        if crop.size == 0: return crop
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        upscaled = cv2.resize(gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(upscaled)
        final = cv2.copyMakeBorder(enhanced, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
        return final

    def distance(self, p1, p2):
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def get_closest_node(self, point, nodes, threshold=100):
        """Находит ближайший узел к точке (x, y)"""
        min_dist = float('inf')
        closest_id = None
        
        px, py = point
        
        for node in nodes:
            nx1, ny1, nx2, ny2 = node['bbox']
            # Центр узла
            cx = (nx1 + nx2) / 2
            cy = (ny1 + ny2) / 2
            
            # Расстояние от точки до центра узла
            # Можно усложнить и считать расстояние до границ прямоугольника,
            # но для BPMN обычно достаточно центра.
            dist = self.distance((px, py), (cx, cy))
            
            # Учитываем размеры узла (чтобы стрелка могла касаться края)
            # Вычитаем половину ширины/высоты узла из дистанции (приближенно)
            node_radius = min(nx2-nx1, ny2-ny1) / 2
            eff_dist = max(0, dist - node_radius)

            if eff_dist < min_dist:
                min_dist = eff_dist
                closest_id = node['id']

        if min_dist < threshold:
            return closest_id
        return None

    def process_image(self, image_path):
        img = cv2.imread(image_path)
        if img is None: return {"error": "Image not found"}
        H, W = img.shape[:2]
        file_name = os.path.basename(image_path)

        # 1. Lanes
        lanes, _ = self.lane_analyzer.find_lanes(img)

        # 2. Nodes
        res_b = self.model_blocks.predict(img, conf=0.1, iou=0.45, verbose=False)[0]
        nodes = []
        for i, box in enumerate(res_b.boxes):
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            
            cy = (y1 + y2) // 2
            role = "General"
            for lane in lanes:
                if lane['y_min'] <= cy <= lane['y_max']:
                    role = lane['role']
                    break
            
            nodes.append({
                "id": f"n{i+1}",
                "class": ID_TO_CLASS.get(cls_id, "element"),
                "bbox": [x1, y1, x2, y2],
                "role": role,
                "text": "",
                "confidence": round(conf, 2)
            })

        print(f"-> OCR for {len(nodes)} nodes...")
        for n in nodes:
            x1, y1, x2, y2 = n['bbox']
            crop = img[y1+4:y2-4, x1+4:x2-4]
            if crop.size > 0:
                processed = self.enhance_text_image(crop)
                try:
                    res = self.reader.readtext(processed, detail=0, paragraph=True)
                    n['text'] = " ".join(res).strip()
                except: pass

        # 3. Arrows & Graph Building
        print("-> Arrow linking...")
        res_a = self.model_arrows.predict(img, conf=0.2, iou=0.4, verbose=False)[0]
        arrows_data = []
        
        for i, box in enumerate(res_a.boxes):
            ax1, ay1, ax2, ay2 = map(int, box.xyxy[0].tolist())
            w, h = ax2 - ax1, ay2 - ay1
            
            # Определяем точки начала и конца стрелки
            # Эвристика: Стрелка идет слева-направо или сверху-вниз
            if w > h: # Горизонтальная
                p_start = (ax1, (ay1 + ay2) // 2)
                p_end = (ax2, (ay1 + ay2) // 2)
            else: # Вертикальная
                p_start = ((ax1 + ax2) // 2, ay1)
                p_end = ((ax1 + ax2) // 2, ay2)
            
            source_id = self.get_closest_node(p_start, nodes)
            target_id = self.get_closest_node(p_end, nodes)
            
            # Если source и target одинаковые (петля или ошибка), игнорируем
            if source_id == target_id:
                target_id = None 

            arrows_data.append({
                "id": f"a{i+1}",
                "source": source_id,
                "target": target_id,
                "points": [list(p_start), list(p_end)], # Примерный путь
                "bbox": [ax1, ay1, ax2, ay2]
            })

        # Финальный граф
        graph_data = {
            "file_name": file_name,
            "nodes": nodes,
            "arrows": arrows_data
        }
        
        return graph_data

    def save_to_markdown(self, data, output_path):
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        md_content = f"""# BPMN Graph Export File: `{data['file_name']}````json{json_str}"""
    def save_to_markdown(self, data, output_path):
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        # Исправлено форматирование строки и отступы
        md_content = f"# BPMN Graph Export File: `{data['file_name']}`\n\n```json\n{json_str}\n```"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"-> Saved graph to {output_path}")

# --- ТОЧКА ВХОДА ---
if __name__ == "__main__":
    parser = DiagramParser()
    
    # Укажите путь к вашему изображению здесь
    path = "Диаграммы. 2 часть/Picture/5.png" 
    
    if os.path.exists(path):
        graph = parser.process_image(path)
        
        # Сохраняем в MD
        output_file = "graph_result.md"
        parser.save_to_markdown(graph, output_file)
        
        # Вывод в консоль для проверки стрелок
        print("\n--- СВЯЗИ (ARROWS) ---")
        for a in graph['arrows']:
            if a['source'] and a['target']:
                print(f"{a['source']} -> {a['target']}")
            else:
                print(f"Arrow {a['id']} disconnected (Source: {a['source']}, Target: {a['target']})")
    else:
        print(f"Ошибка: Файл '{path}' не найден. Проверьте путь.")