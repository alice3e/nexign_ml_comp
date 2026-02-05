"""import random
import json
import os
from PIL import Image, ImageDraw, ImageFont

try:
    from faker import Faker
    fake = Faker("ru_RU") 
except ImportError:
    fake = None

CLASS_MAP = {
    'activity_task': 0, 'activity_process_step': 1, 'event_start': 2,
    'event_end': 3, 'event_intermediate': 4, 'event_timer': 5,
    'event_message': 6, 'event_user': 7, 'gateway_exclusive': 8,
    'gateway_parallel': 9, 'gateway_empty': 10, 'oval': 11, 'artifact': 12
}

class DiagramSynthesizer:
    def __init__(self, width=640, height=640):
        self.W, self.H = width, height
        self.bg_color = (255, 255, 255)
        self.colors = [(0, 0, 0), (34, 139, 34), (210, 105, 30), (70, 130, 180), (220, 20, 60)]
        self.font = self._load_font()
        self.sizes = {
            'event': (50, 70), 'gateway': (60, 80), 'task': (120, 200, 60, 100),
            'doc': (50, 70, 70, 90), 'step': (120, 220, 60, 100), 'oval': (100, 180, 50, 80)
        }
        self.occupied_boxes = []

    def _load_font(self, size=14):
        path = "/Users/lubimaya/Desktop/programming/nexign_project/data2/arial.ttf"
        return ImageFont.truetype(path, size) if os.path.exists(path) else ImageFont.load_default()

    def _get_random_dims(self, key):
        is_mini = random.choice([True, False])
        scale = 2.5 if is_mini else 1.0
        d = self.sizes[key]
        if len(d) == 2:
            val = int(random.randint(d[0], d[1]) / scale)
            return val, val
        return int(random.randint(d[0], d[1]) / scale), int(random.randint(d[2], d[3]) / scale)

    def _check_overlap(self, new_box, padding=10):
        for bx in self.occupied_boxes:
            if not (new_box[2]+padding < bx[0] or new_box[0]-padding > bx[2] or 
                    new_box[3]+padding < bx[1] or new_box[1]-padding > bx[3]):
                return True
        return False

    def _draw_inner_icon(self, draw, cx, cy, size, icon_type, color):
        s = size // 3
        lw = 2 if size > 35 else 1
        if icon_type == 'plus':
            draw.line([(cx-s, cy), (cx+s, cy)], fill=color, width=lw)
            draw.line([(cx, cy-s), (cx, cy+s)], fill=color, width=lw)
        elif icon_type == 'cross':
            draw.line([(cx-s, cy-s), (cx+s, cy+s)], fill=color, width=lw)
            draw.line([(cx-s, cy+s), (cx+s, cy-s)], fill=color, width=lw)

    def _event_logic(self, draw, bbox, color):
        st = random.choice(['start', 'end', 'intermediate', 'timer', 'message', 'user'])
        draw.ellipse(bbox, outline=color, width=2)
        return {"class": f"event_{st}"}

    def _task_logic(self, draw, bbox, color):
        draw.rounded_rectangle(bbox, radius=8, outline=color, width=2)
        return {"class": "activity_task"}

    def _gateway_logic(self, draw, bbox, color):
        st = random.choice(['exclusive', 'parallel', 'empty'])
        x1, y1, x2, y2 = bbox
        cx, cy = (x1+x2)//2, (y1+y2)//2
        draw.polygon([(cx, y1), (x2, cy), (cx, y2), (x1, cy)], outline=color, width=2)
        if st == 'exclusive': self._draw_inner_icon(draw, cx, cy, x2-x1, 'cross', color)
        if st == 'parallel': self._draw_inner_icon(draw, cx, cy, x2-x1, 'plus', color)
        return {"class": f"gateway_{st}"}

    def _doc_logic(self, draw, bbox, color):
        draw.rectangle(bbox, outline=color, width=2)
        return {"class": "artifact"}

    def _step_logic(self, draw, bbox, color):
        draw.polygon([(bbox[0],bbox[1]), (bbox[2]-10,bbox[1]), (bbox[2],(bbox[1]+bbox[3])/2), (bbox[2]-10,bbox[3]), (bbox[0],bbox[3])], outline=color, width=2)
        return {"class": "activity_process_step"}

    def _oval_logic(self, draw, bbox, color):
        draw.ellipse(bbox, outline=color, width=2)
        return {"class": "oval"}

    def _place_shape(self, draw, key, logic_func):
        w, h = self._get_random_dims(key)
        for _ in range(50):
            x, y = random.randint(5, self.W-w-5), random.randint(5, self.H-h-5)
            bbox = [x, y, x+w, y+h]
            if not self._check_overlap(bbox):
                self.occupied_boxes.append(bbox)
                res = logic_func(draw, bbox, random.choice(self.colors))
                return {"class": res["class"], "bbox": bbox}
        return None

    def generate_image(self, num_elements=8):
        img = Image.new("RGB", (self.W, self.H), self.bg_color)
        draw = ImageDraw.Draw(img)
        self.occupied_boxes, meta = [], []
        funcs = [('event', self._event_logic), ('gateway', self._gateway_logic), 
                 ('task', self._task_logic), ('doc', self._doc_logic), 
                 ('step', self._step_logic), ('oval', self._oval_logic)]
        
        while len(meta) < num_elements:
            key, fn = random.choice(funcs)
            data = self._place_shape(draw, key, fn)
            if data: meta.append(data)
        return img, meta

if __name__ == "__main__":
    synth = DiagramSynthesizer()
    for i in range(1000):
        img, meta = synth.generate_image(random.randint(6, 10))
        img.save(f"data2/dataset_blocks/images/bpmn_final_{i}.png")
        with open(f"data2/dataset_blocks/metadata/bpmn_final_{i}.json", "w") as f:
            json.dump(meta, f)
    print("Генерация v8 завершена. Теперь все классы имеют полные имена.")"""

"""andz"""

import random
import json
import os
import math
from PIL import Image, ImageDraw, ImageFont

try:
    from faker import Faker
    fake = Faker("ru_RU") 
except ImportError:
    fake = None

CLASS_MAP = {
    'activity_task': 0, 'activity_process_step': 1, 'event_start': 2,
    'event_end': 3, 'event_intermediate': 4, 'event_timer': 5,
    'event_message': 6, 'event_user': 7, 'gateway_exclusive': 8,
    'gateway_parallel': 9, 'gateway_empty': 10, 'oval': 11, 'artifact': 12
}

class DiagramSynthesizer:
    def __init__(self, width=1024, height=1024):
        self.W, self.H = width, height
        self.bg_color = (255, 255, 255)
        self.colors = [(0, 0, 0), (40, 40, 40), (80, 80, 80)] 
        self.font = self._load_font(12)
        self.sizes = {
            'event': (35, 55), 
            'gateway': (45, 65), 
            'task': (120, 200, 60, 100),
            'artifact': (40, 70, 50, 80), 
            'step': (110, 190, 60, 90), 
            'oval': (90, 160, 50, 80)
        }
        self.occupied_boxes = []

    def _load_font(self, size=12):
        # Замените путь на актуальный для вашей системы
        path = "/System/Library/Fonts/Cache/Arial.ttf" 
        if not os.path.exists(path):
            path = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        return ImageFont.truetype(path, size) if os.path.exists(path) else ImageFont.load_default()

    def _get_random_dims(self, key):
        d = self.sizes[key]
        if len(d) == 2:
            val = random.randint(d[0], d[1])
            return val, val
        return random.randint(d[0], d[1]), random.randint(d[2], d[3])

    def _check_overlap(self, new_box, padding=15):
        for bx in self.occupied_boxes:
            if not (new_box[2]+padding < bx[0] or new_box[0]-padding > bx[2] or 
                    new_box[3]+padding < bx[1] or new_box[1]-padding > bx[3]):
                return True
        return False

    # --- ВСПОМОГАТЕЛЬНЫЕ РИСОВАЛКИ ИКОНОК ---
    def _draw_icon_timer(self, draw, bbox, color):
        x1, y1, x2, y2 = bbox
        cx, cy = (x1+x2)/2, (y1+y2)/2
        r = (x2-x1)/3
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=color, width=1)
        draw.line([cx, cy, cx, cy-r+3], fill=color, width=1)
        draw.line([cx, cy, cx+r-3, cy], fill=color, width=1)

    def _draw_icon_message(self, draw, bbox, color):
        x1, y1, x2, y2 = bbox
        w, h = (x2-x1)/2, (y2-y1)/3
        cx, cy = (x1+x2)/2, (y1+y2)/2
        draw.rectangle([cx-w/2, cy-h/2, cx+w/2, cy+h/2], outline=color, width=1)
        draw.line([cx-w/2, cy-h/2, cx, cy, cx+w/2, cy-h/2], fill=color, width=1)

    def _draw_icon_user(self, draw, bbox, color):
        x1, y1, x2, y2 = bbox
        cx, cy = (x1+x2)/2, (y1+y2)/2
        r = (x2-x1)/6
        draw.ellipse([cx-r, cy-r-5, cx+r, cy-r+5], outline=color, width=1)
        draw.arc([cx-r-5, cy, cx+r+5, cy+15], 180, 0, fill=color, width=1)

    def _draw_icon_cross(self, draw, bbox, color):
        x1, y1, x2, y2 = bbox
        cx, cy = (x1+x2)/2, (y1+y2)/2
        s = 8
        draw.line([cx-s, cy-s, cx+s, cy+s], fill=color, width=2)
        draw.line([cx+s, cy-s, cx-s, cy+s], fill=color, width=2)

    def _draw_icon_plus(self, draw, bbox, color):
        x1, y1, x2, y2 = bbox
        cx, cy = (x1+x2)/2, (y1+y2)/2
        s = 8
        draw.line([cx-s, cy, cx+s, cy], fill=color, width=2)
        draw.line([cx, cy-s, cx, cy+s], fill=color, width=2)

    # --- ЛОГИКА КЛАССОВ ---
    def _event_logic(self, draw, bbox, color):
        types = ['start', 'end', 'intermediate', 'timer', 'message', 'user']
        st = random.choice(types)
        width = 3 if st == 'end' else 1
        draw.ellipse(bbox, outline=color, width=width)
        
        if st == 'intermediate':
            draw.ellipse([bbox[0]+3, bbox[1]+3, bbox[2]-3, bbox[3]-3], outline=color, width=1)
        elif st == 'timer': self._draw_icon_timer(draw, bbox, color)
        elif st == 'message': self._draw_icon_message(draw, bbox, color)
        elif st == 'user': self._draw_icon_user(draw, bbox, color)
        
        return {"class": f"event_{st}"}

    def _gateway_logic(self, draw, bbox, color):
        st = random.choice(['exclusive', 'parallel', 'empty'])
        x1, y1, x2, y2 = bbox
        cx, cy = (x1+x2)//2, (y1+y2)//2
        pts = [(cx, y1), (x2, cy), (cx, y2), (x1, cy)]
        draw.polygon(pts, outline=color, width=2)
        
        if st == 'exclusive': self._draw_icon_cross(draw, bbox, color)
        elif st == 'parallel': self._draw_icon_plus(draw, bbox, color)
        
        return {"class": f"gateway_{st}"}

    def _task_logic(self, draw, bbox, color, fill=None):
        draw.rounded_rectangle(bbox, radius=8, outline=color, width=2, fill=fill)
        return {"class": "activity_task"}

    def _oval_logic(self, draw, bbox, color):
        # Пунктирный эллипс (имитация артефакта аннотации)
        for angle in range(0, 360, 15):
            start = math.radians(angle)
            end = math.radians(angle + 7)
            draw.arc(bbox, start=math.degrees(start), end=math.degrees(end), fill=color, width=1)
        return {"class": "oval"}

    def _artifact_logic(self, draw, bbox, color):
        # Иконка документа (лист с загнутым углом)
        x1, y1, x2, y2 = bbox
        corner = 10
        pts = [(x1, y1), (x2-corner, y1), (x2, y1+corner), (x2, y2), (x1, y2)]
        draw.polygon(pts, outline=color, width=1)
        draw.line([(x2-corner, y1), (x2-corner, y1+corner), (x2, y1+corner)], fill=color, width=1)
        return {"class": "artifact"}

    def _place_shape(self, draw, key, logic_func):
        w, h = self._get_random_dims(key)
        for _ in range(50):
            x, y = random.randint(50, self.W-w-50), random.randint(50, self.H-h-50)
            bbox = [x, y, x+w, y+h]
            if not self._check_overlap(bbox):
                self.occupied_boxes.append(bbox)
                
                # --- ЛОГИКА ЦВЕТОВ ---
                color = random.choice(self.colors)
                fill = None
                
                rnd = random.random()
                if rnd < 0.2: # Зеленый контур
                    color = (34, 139, 34)
                elif rnd < 0.25 and key in ['task', 'step']: # Случайный цвет заливки
                    fill = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
                elif rnd < 0.30: # Инверсия (белое на темном)
                    draw.rectangle(bbox, fill=(30, 30, 30))
                    color = (255, 255, 255)

                res = logic_func(draw, bbox, color)
                if fill and 'fill' in res: pass # placeholder
                
                if fake and random.random() > 0.4:
                    txt = fake.sentence(nb_words=random.randint(1, 3))
                    draw.text((x+10, y+h//2.5), txt[:w//8], fill=color, font=self.font)
                
                return {"class": res["class"], "bbox": bbox}
        return None

    def generate_image(self, num_elements=15):
        img = Image.new("RGB", (self.W, self.H), self.bg_color)
        draw = ImageDraw.Draw(img)
        self.occupied_boxes, meta = [], []
        
        funcs = [
            ('event', self._event_logic), ('gateway', self._gateway_logic), 
            ('task', self._task_logic), ('oval', self._oval_logic),
            ('artifact', self._artifact_logic)
        ]
        
        while len(meta) < num_elements:
            key, fn = random.choice(funcs)
            data = self._place_shape(draw, key, fn)
            if data: meta.append(data)
            
        return img, meta

if __name__ == "__main__":
    out_img = "data2/dataset_blocks/images"
    out_meta = "data2/dataset_blocks/metadata"
    os.makedirs(out_img, exist_ok=True)
    os.makedirs(out_meta, exist_ok=True)

    synth = DiagramSynthesizer()
    for i in range(1000):
        img, meta = synth.generate_image(random.randint(10, 18))
        name = f"bpmn_v10_{i}"
        img.save(f"{out_img}/{name}.png")
        with open(f"{out_meta}/{name}.json", "w") as f:
            json.dump(meta, f)
    print("Генерация v10 (детализированная) завершена.")