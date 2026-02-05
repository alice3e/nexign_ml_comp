import cv2
import json
import numpy as np
from ultralytics import YOLO
import easyocr
import os
import math
import torch

class SwimlaneAnalyzer:
    def __init__(self, reader):
        self.reader = reader

    def preprocess_role_crop(self, crop):
        if crop.size == 0: return None
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        upscaled = cv2.resize(gray, None, fx=4.0, fy=4.0, interpolation=cv2.INTER_CUBIC)
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
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
    def __init__(self, blocks_path, arrows_path):
        self.id_to_class = {
            0: 'task', 1: 'process_step', 2: 'start_event', 3: 'end_event',
            4: 'intermediate_event', 5: 'timer_event', 6: 'message_event',
            7: 'user_event', 8: 'exclusive_gateway', 9: 'parallel_gateway',
            10: 'inclusive_gateway', 11: 'oval', 12: 'artifact'
        }
        self.model_blocks = YOLO(blocks_path)
        self.model_arrows = YOLO(arrows_path)
        # Инициализируем EasyOCR (gpu=True если есть NVIDIA)
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
            x1, y1, x2, y2 = node['bbox']
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            dist = math.sqrt((px - cx)**2 + (py - cy)**2)
            node_radius = min(x2 - x1, y2 - y1) / 2
            eff_dist = max(0, dist - node_radius)
            if eff_dist < min_dist:
                min_dist, closest_id = eff_dist, node['id']
        return closest_id if min_dist < threshold else None

    def process_image(self, image_path):
        img = cv2.imread(image_path)
        if img is None: return None
        
        # 1. Поиск дорожек (Roles)
        lanes, _ = self.lane_analyzer.find_lanes(img)

        # 2. Детекция блоков
        res_b = self.model_blocks.predict(img, conf=0.1, verbose=False)[0]
        nodes = []
        for i, box in enumerate(res_b.boxes):
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            cy = (y1 + y2) // 2
            role = next((l['role'] for l in lanes if l['y_min'] <= cy <= l['y_max']), "General")
            
            nodes.append({
                "id": f"n{i+1}",
                "class": self.id_to_class.get(int(box.cls[0]), "element"),
                "bbox": [x1, y1, x2, y2],
                "role": role,
                "text": ""
            })

        # 3. OCR для текста внутри блоков
        for n in nodes:
            x1, y1, x2, y2 = n['bbox']
            crop = img[y1+4:y2-4, x1+4:x2-4]
            if crop.size > 0:
                try:
                    enhanced = self.enhance_text_image(crop)
                    res = self.reader.readtext(enhanced, detail=0, paragraph=True)
                    n['text'] = " ".join(res).strip()
                except: pass

        # 4. Детекция стрелок и построение связей
        res_a = self.model_arrows.predict(img, conf=0.2, verbose=False)[0]
        arrows = []
        for i, box in enumerate(res_a.boxes):
            ax1, ay1, ax2, ay2 = map(int, box.xyxy[0].tolist())
            # Определяем направление (горизонтальное/вертикальное)
            if (ax2 - ax1) > (ay2 - ay1):
                p_start, p_end = (ax1, (ay1 + ay2) // 2), (ax2, (ay1 + ay2) // 2)
            else:
                p_start, p_end = ((ax1 + ax2) // 2, ay1), ((ax1 + ax2) // 2, ay2)
            
            s_id = self.get_closest_node(p_start, nodes)
            t_id = self.get_closest_node(p_end, nodes)
            if s_id and t_id and s_id != t_id:
                arrows.append({"id": f"a{i+1}", "source": s_id, "target": t_id})

        return {
            "file_name": os.path.basename(image_path),
            "nodes": nodes,
            "arrows": arrows
        }