'''import os
import random
import json
import graphviz
from tqdm import tqdm

# === НАСТРОЙКИ ===
OUTPUT_DIR = "data"
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
METADATA_FILE = os.path.join(OUTPUT_DIR, "metadata.jsonl")
NUM_SAMPLES = 50 

os.makedirs(IMAGES_DIR, exist_ok=True)

# === СЦЕНАРИИ ===
# (Оставляем те же, они хорошие)
SCENARIOS = {
    "hr_hiring": {
        "roles": ["HR-менеджер", "Кандидат", "Техлид", "СБ"],
        "start": ["Получение резюме", "Отклик на сайте"],
        "tasks": ["Скрининг резюме", "Назначение интервью", "Техническое интервью", "Запрос документов", "Подготовка оффера"],
        "conditions": ["Кандидат подходит?", "Проверка СБ пройдена?", "Оффер принят?"],
        "end": ["Отказ отправлен", "Кандидат оформлен"]
    },
    "procurement": {
        "roles": ["Закупщик", "Поставщик", "Бухгалтер", "Склад"],
        "start": ["Создание заявки", "Сигнал о нехватке"],
        "tasks": ["Запрос КП", "Сравнение цен", "Согласование бюджета", "Оплата счета", "Приемка товара"],
        "conditions": ["В рамках бюджета?", "Товар в наличии?", "Брак есть?"],
        "end": ["Закупка отменена", "Товар на складе"]
    },
    "dev_process": {
        "roles": ["Разработчик", "QA", "Product Owner", "DevOps"],
        "start": ["Создание тикета", "Баг-репорт"],
        "tasks": ["Написание кода", "Code Review", "Автотесты", "Деплой на стейдж", "Обновление доки"],
        "conditions": ["Тесты зеленые?", "Review пройден?", "Есть блокеры?"],
        "end": ["Релиз в прод", "Возврат в бэклог"]
    },
     "pizza_delivery": {
        "roles": ["Клиент", "Оператор", "Повар", "Курьер"],
        "start": ["Звонок в пиццерию", "Заказ в приложении"],
        "tasks": ["Подтверждение заказа", "Приготовление теста", "Добавление начинки", "Выпекание", "Доставка"],
        "conditions": ["Оплата прошла?", "Адрес корректен?", "Клиент на связи?"],
        "end": ["Пицца доставлена", "Заказ аннулирован"]
    }
}

class TableBPMNGenerator:
    def __init__(self):
        self.node_counter = 0
        self.steps_log = [] # Здесь будем хранить шаги для таблицы
    
    def _get_id(self):
        self.node_counter += 1
        return f"n{self.node_counter}"

    def _log_step(self, action, role):
        """Записывает шаг в лог для будущей таблицы"""
        self.steps_log.append({
            "action": action,
            "role": role
        })

    def _generate_markdown_table(self):
        """Генерирует Markdown таблицу из лога"""
        md = "| № | Наименование действия | Роль |\n"
        md += "|---|---|---|\n"
        for idx, step in enumerate(self.steps_log, 1):
            md += f"| {idx} | {step['action']} | {step['role']} |\n"
        return md

    def generate(self, filename):
        self.node_counter = 0
        self.steps_log = [] # Очищаем лог перед новой генерацией
        
        scenario_key = random.choice(list(SCENARIOS.keys()))
        scenario = SCENARIOS[scenario_key]
        active_roles = random.sample(scenario["roles"], k=random.randint(2, 3))
        
        # Инициализация графа
        dot = graphviz.Digraph('BPMN', format='png')
        dot.attr(rankdir='LR', splines='ortho', nodesep='0.6', ranksep='0.8')
        dot.attr('node', fontname='Arial', fontsize='10', style='filled', fillcolor='white')
        
        lane_nodes = {role: [] for role in active_roles}
        
        # --- 1. START ---
        current_role = active_roles[0]
        start_id = self._get_id()
        start_text = random.choice(scenario["start"])
        
        lane_nodes[current_role].append((start_id, "start", start_text))
        # Логируем действие
        self._log_step(start_text, current_role)
        
        current_id = start_id
        
        # --- 2. PROCESS ---
        steps_left = random.randint(4, 7)
        
        while steps_left > 0:
            steps_left -= 1
            node_type = random.choices(["task", "gateway", "parallel"], weights=[0.6, 0.25, 0.15])[0]
            
            # Смена роли
            if random.random() < 0.35:
                new_role = random.choice(active_roles)
                if new_role != current_role:
                    current_role = new_role

            if node_type == "task":
                task_text = random.choice(scenario["tasks"])
                next_id = self._get_id()
                
                lane_nodes[current_role].append((next_id, "task", task_text))
                dot.edge(current_id, next_id)
                
                self._log_step(task_text, current_role)
                current_id = next_id
            
            elif node_type == "gateway": # Ветвление
                cond_text = random.choice(scenario["conditions"])
                gw_id = self._get_id()
                
                lane_nodes[current_role].append((gw_id, "gateway", cond_text)) # Текст условия внутри ромба? Или рядом?
                # В BPMN текст часто пишут над ромбом, но для простоты OCR напишем внутрь или рядом
                # Graphviz позволяет label.
                
                dot.edge(current_id, gw_id)
                self._log_step(f"Проверка: {cond_text}", current_role)
                
                # Ветки
                yes_id = self._get_id()
                no_id = self._get_id()
                merge_id = self._get_id()
                
                task_yes = random.choice(scenario["tasks"])
                task_no = random.choice(scenario["tasks"])
                
                lane_nodes[current_role].append((yes_id, "task", task_yes))
                lane_nodes[current_role].append((no_id, "task", task_no))
                lane_nodes[current_role].append((merge_id, "gateway", "X"))
                
                dot.edge(gw_id, yes_id, label="Да")
                dot.edge(gw_id, no_id, label="Нет")
                dot.edge(yes_id, merge_id)
                dot.edge(no_id, merge_id)
                
                # Логируем ветки
                self._log_step(f"Если Да: {task_yes}", current_role)
                self._log_step(f"Если Нет: {task_no}", current_role)
                
                current_id = merge_id
                
            elif node_type == "parallel": # Параллельность
                split_id = self._get_id()
                lane_nodes[current_role].append((split_id, "gateway", "+"))
                dot.edge(current_id, split_id)
                
                task_1 = random.choice(scenario["tasks"])
                task_2 = random.choice(scenario["tasks"])
                
                id_1 = self._get_id()
                id_2 = self._get_id()
                join_id = self._get_id()
                
                lane_nodes[current_role].append((id_1, "task", task_1))
                lane_nodes[current_role].append((id_2, "task", task_2))
                lane_nodes[current_role].append((join_id, "gateway", "+"))
                
                dot.edge(split_id, id_1)
                dot.edge(split_id, id_2)
                dot.edge(id_1, join_id)
                dot.edge(id_2, join_id)
                
                self._log_step(f"Параллельно: {task_1}", current_role)
                self._log_step(f"Параллельно: {task_2}", current_role)
                
                current_id = join_id

        # --- 3. END ---
        end_id = self._get_id()
        end_text = random.choice(scenario["end"])
        lane_nodes[current_role].append((end_id, "end", end_text))
        dot.edge(current_id, end_id)
        
        self._log_step(end_text, current_role)

        # Отрисовка
        for i, role in enumerate(active_roles):
            with dot.subgraph(name=f'cluster_{i}') as c:
                c.attr(label=role, style='filled', color='#EEEEEE')
                for nid, ntype, nlabel in lane_nodes[role]:
                    if ntype == 'start':
                        c.node(nid, label=nlabel, shape='circle', width='0.8', style='filled', fillcolor='#DFFFE0', fontsize='8')
                    elif ntype == 'end':
                        c.node(nid, label=nlabel, shape='doublecircle', width='0.8', style='filled', fillcolor='#FFD0D0', fontsize='8')
                    elif ntype == 'gateway':
                        # Если это условие, пишем текст, если мердж - символ
                        lbl = nlabel if len(nlabel) < 3 else "?" # Упрощение для визуализации
                        c.node(nid, label=lbl, shape='diamond', style='filled', fillcolor='#FFFFCC', width='0.6', height='0.6')
                        # Если текст длинный (вопрос), добавим его как xlabel (внешняя подпись)
                        if len(nlabel) > 3:
                             c.node(nid, xlabel=nlabel)
                    else:
                        c.node(nid, label=nlabel, shape='box', style='rounded,filled', fillcolor='white', width='1.5')

        # Рендер
        out_path = os.path.join(IMAGES_DIR, filename)
        dot.render(out_path, cleanup=True)
        
        # Возвращаем таблицу вместо текста
        return f"{filename}.png", self._generate_markdown_table()

def main():
    print(f"Генерация {NUM_SAMPLES} примеров с табличной разметкой...")
    
    # Очистка старого
    if os.path.exists(METADATA_FILE):
        os.remove(METADATA_FILE)
        
    gen = TableBPMNGenerator()
    metadata = []
    
    for i in tqdm(range(NUM_SAMPLES)):
        fname = f"bpmn_table_{i:03d}"
        try:
            img, txt = gen.generate(fname)
            metadata.append({"file_name": img, "text": txt})
        except Exception as e:
            print(f"Error: {e}")
            
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        for m in metadata:
            f.write(json.dumps(m, ensure_ascii=False) + '\n')
            
    print("Готово! Проверь metadata.jsonl - там теперь markdown таблицы.")

if __name__ == "__main__":
    main()'''


'''import os
import random
import json
import re
import graphviz
from tqdm import tqdm

# === НАСТРОЙКИ ===
OUTPUT_DIR = "data"
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
ANNOTATIONS_FILE = os.path.join(OUTPUT_DIR, "matadata.jsonl")
NUM_SAMPLES = 50 
DPI = 100  # Важно фиксировать DPI для точного пересчета координат

os.makedirs(IMAGES_DIR, exist_ok=True)

# === СЦЕНАРИИ (Те же самые) ===
SCENARIOS = {
    "hr_hiring": {
        "roles": ["HR-менеджер", "Кандидат", "Техлид", "СБ"],
        "start": ["Получение резюме", "Отклик на сайте"],
        "tasks": ["Скрининг резюме", "Назначение интервью", "Техническое интервью", "Запрос документов", "Подготовка оффера"],
        "conditions": ["Кандидат подходит?", "Проверка СБ пройдена?", "Оффер принят?"],
        "end": ["Отказ отправлен", "Кандидат оформлен"]
    },
    "procurement": {
        "roles": ["Закупщик", "Поставщик", "Бухгалтер", "Склад"],
        "start": ["Создание заявки", "Сигнал о нехватке"],
        "tasks": ["Запрос КП", "Сравнение цен", "Согласование бюджета", "Оплата счета", "Приемка товара"],
        "conditions": ["В рамках бюджета?", "Товар в наличии?", "Брак есть?"],
        "end": ["Закупка отменена", "Товар на складе"]
    },
    "pizza_delivery": {
        "roles": ["Клиент", "Оператор", "Повар", "Курьер"],
        "start": ["Звонок в пиццерию", "Заказ в приложении"],
        "tasks": ["Подтверждение заказа", "Приготовление теста", "Добавление начинки", "Выпекание", "Доставка"],
        "conditions": ["Оплата прошла?", "Адрес корректен?", "Клиент на связи?"],
        "end": ["Пицца доставлена", "Заказ аннулирован"]
    }
}

class LabeledBPMNGenerator:
    def __init__(self):
        self.node_counter = 0
        self.steps_log = []
    
    def _get_id(self):
        self.node_counter += 1
        return f"n{self.node_counter}"

    def _log_step(self, action, role):
        self.steps_log.append({"action": action, "role": role})

    def _generate_markdown_table(self):
        md = "| № | Наименование действия | Роль |\n|---|---|---|\n"
        for idx, step in enumerate(self.steps_log, 1):
            md += f"| {idx} | {step['action']} | {step['role']} |\n"
        return md

    def _parse_graphviz_coord(self, pos_str, height_px):
        """
        Преобразует координаты Graphviz (точки, origin bottom-left)
        в координаты изображения (пиксели, origin top-left).
        pos_str: "x,y" (центр объекта)
        """
        if not pos_str: return 0, 0
        x, y = map(float, pos_str.split(','))
        
        # Graphviz считает в дюймах/пунктах (72 points per inch), но мы рендерим с DPI=100
        # Масштабный коэффициент: render_dpi / 72.0
        scale = DPI / 72.0
        
        x_px = x * scale
        y_px_inverted = y * scale
        
        # Инвертируем Y (так как в картинках Y растет вниз)
        y_px = height_px - y_px_inverted
        return x_px, y_px

    def _parse_bb_polygon(self, pos_str, width_inch, height_inch, img_height):
        """Считает BBox [xmin, ymin, xmax, ymax]"""
        cx, cy = self._parse_graphviz_coord(pos_str, img_height)
        
        w_px = float(width_inch) * DPI
        h_px = float(height_inch) * DPI
        
        x1 = cx - (w_px / 2)
        y1 = cy - (h_px / 2)
        x2 = cx + (w_px / 2)
        y2 = cy + (h_px / 2)
        
        return [int(x1), int(y1), int(x2), int(y2)]

    def generate(self, filename_base):
        self.node_counter = 0
        self.steps_log = []
        
        scenario_key = random.choice(list(SCENARIOS.keys()))
        scenario = SCENARIOS[scenario_key]
        active_roles = random.sample(scenario["roles"], k=random.randint(2, 3))
        
        # Настройка Graphviz
        dot = graphviz.Digraph('BPMN', format='png')
        dot.attr(dpi=str(DPI)) # Фиксируем DPI
        dot.attr(rankdir='LR', splines='ortho', nodesep='0.6', ranksep='0.8')
        dot.attr('node', fontname='Arial', fontsize='10', style='filled', fillcolor='white')
        
        # Структуры для графа
        lane_nodes = {role: [] for role in active_roles}
        edges = [] # Сохраняем логические связи (source_id, target_id)
        
        # --- ГЕНЕРАЦИЯ ЛОГИКИ (упрощенная копия из вашего кода) ---
        current_role = active_roles[0]
        start_id = self._get_id()
        start_text = random.choice(scenario["start"])
        lane_nodes[current_role].append((start_id, "start", start_text))
        self._log_step(start_text, current_role)
        current_id = start_id
        
        steps_left = random.randint(3, 5)
        while steps_left > 0:
            steps_left -= 1
            node_type = random.choices(["task", "gateway"], weights=[0.7, 0.3])[0]
            
            if random.random() < 0.3: current_role = random.choice(active_roles)

            if node_type == "task":
                task_text = random.choice(scenario["tasks"])
                next_id = self._get_id()
                lane_nodes[current_role].append((next_id, "task", task_text))
                edges.append((current_id, next_id, ""))
                self._log_step(task_text, current_role)
                current_id = next_id
            
            elif node_type == "gateway":
                cond_text = random.choice(scenario["conditions"])
                gw_id = self._get_id()
                lane_nodes[current_role].append((gw_id, "gateway", cond_text))
                edges.append((current_id, gw_id, ""))
                self._log_step(f"Условие: {cond_text}", current_role)
                
                yes_id = self._get_id()
                no_id = self._get_id()
                merge_id = self._get_id()
                
                task_yes = random.choice(scenario["tasks"])
                task_no = random.choice(scenario["tasks"])
                
                lane_nodes[current_role].append((yes_id, "task", task_yes))
                lane_nodes[current_role].append((no_id, "task", task_no))
                lane_nodes[current_role].append((merge_id, "gateway", "X"))
                
                edges.append((gw_id, yes_id, "Да"))
                edges.append((gw_id, no_id, "Нет"))
                edges.append((yes_id, merge_id, ""))
                edges.append((no_id, merge_id, ""))
                
                self._log_step(f"Да: {task_yes}", current_role)
                self._log_step(f"Нет: {task_no}", current_role)
                current_id = merge_id
        
        end_id = self._get_id()
        end_text = random.choice(scenario["end"])
        lane_nodes[current_role].append((end_id, "end", end_text))
        edges.append((current_id, end_id, ""))
        self._log_step(end_text, current_role)

        # --- ОТРИСОВКА В GRAPHVIZ ---
        # Нам нужно сохранить маппинг node_id -> текст/тип для парсинга JSON позже
        node_metadata = {}

        for i, role in enumerate(active_roles):
            with dot.subgraph(name=f'cluster_{i}') as c:
                c.attr(label=role, style='filled', color='#EEEEEE')
                for nid, ntype, nlabel in lane_nodes[role]:
                    node_metadata[nid] = {"type": ntype, "text": nlabel, "role": role}
                    
                    if ntype == 'start':
                        c.node(nid, label=nlabel, shape='circle', style='filled', fillcolor='#DFFFE0')
                    elif ntype == 'end':
                        c.node(nid, label=nlabel, shape='doublecircle', style='filled', fillcolor='#FFD0D0')
                    elif ntype == 'gateway':
                        # Обработка длинного текста для условий
                        lbl = nlabel if len(nlabel) < 4 else "?"
                        attr = {'label': lbl, 'shape': 'diamond', 'style': 'filled', 'fillcolor': '#FFFFCC'}
                        if len(nlabel) >= 4: attr['xlabel'] = nlabel
                        c.node(nid, **attr)
                    else:
                        c.node(nid, label=nlabel, shape='box', style='rounded,filled', fillcolor='white')

        for src, dst, lbl in edges:
            dot.edge(src, dst, label=lbl)

        # --- 1. ПОЛУЧЕНИЕ LAYOUT JSON (КООРДИНАТЫ) ---
        # Генерируем JSON описание графа от движка dot
        json_layout_str = dot.pipe(format='json').decode('utf-8')
        layout_data = json.loads(json_layout_str)
        
        # Получаем размеры всего изображения из layout
        # bb = "0,0,width,height" (в пунктах)
        bb = layout_data.get('bb', '0,0,0,0').split(',')
        total_h_pts = float(bb[3])
        
        # Реальные размеры картинки в пикселях
        img_width = int(float(bb[2]) * (DPI / 72.0))
        img_height = int(float(bb[3]) * (DPI / 72.0))

        # --- 2. СБОР ANNOTATIONS ---
        objects = []
        
        # Проходим по всем объектам в JSON layout
        for obj in layout_data.get('objects', []):
            name = obj.get('name', '')
            
            # Пропускаем кластеры (дорожки) и служебные узлы
            if name not in node_metadata:
                continue
                
            meta = node_metadata[name]
            
            # Получаем BBox
            # pos format: "x,y" (center)
            pos = obj.get('pos', '0,0')
            w_inch = obj.get('width', '0')
            h_inch = obj.get('height', '0')
            
            bbox = self._parse_bb_polygon(pos, w_inch, h_inch, img_height)
            
            obj_entry = {
                "id": name,
                "class": meta['type'], # task, gateway, start, end
                "text": meta['text'],
                "role": meta['role'],
                "bbox": bbox, # [x_min, y_min, x_max, y_max]
                "confidence": 1.0 # Это Ground Truth
            }
            
            # Если есть xlabel (внешняя подпись), можно добавить её координаты (в 'lp'), 
            # но пока ограничимся основным bbox фигуры для детекции.
            
            objects.append(obj_entry)

        # Сбор стрелок (Edges) - это сложно для детекции, но полезно для графа
        arrows = []
        for edge in layout_data.get('edges', []):
            # Graphviz возвращает "pos" как набор точек сплайна "e,x,y x,y x,y..."
            # Мы можем сохранить source и target
            head = edge.get('head')
            tail = edge.get('tail')
            
            # Пример парсинга сплайна можно добавить, если нужно рисовать маски стрелок
            # но пока оставим логическую связь
            arrows.append({
                "source": tail,
                "target": head,
                # "spline": edge.get('pos') # Можно раскомментировать, если нужно
            })

        # --- 3. РЕНДЕР КАРТИНКИ ---
        filename_png = f"{filename_base}.png"
        out_path = os.path.join(IMAGES_DIR, filename_base) # graphviz добавит .png сам
        dot.render(out_path, cleanup=True)
        
        # Формируем итоговую запись
        annotation = {
            "file_name": filename_png,
            "image_size": [img_width, img_height],
            "text": self._generate_markdown_table(),
            "objects": objects,
            "arrows": arrows
        }
        
        return annotation

def main():
    print(f"Генерация {NUM_SAMPLES} примеров с BBox и JSON разметкой...")
    if os.path.exists(ANNOTATIONS_FILE): os.remove(ANNOTATIONS_FILE)
        
    gen = LabeledBPMNGenerator()
    
    with open(ANNOTATIONS_FILE, 'w', encoding='utf-8') as f:
        for i in tqdm(range(NUM_SAMPLES)):
            fname = f"bpmn_train_{i:03d}"
            try:
                data = gen.generate(fname)
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
            except Exception as e:
                print(f"Error on {fname}: {e}")
                # import traceback; traceback.print_exc()

    print(f"Готово! Данные в {OUTPUT_DIR}")

if __name__ == "__main__":
    main()'''

import os
import random
import json
import graphviz
from tqdm import tqdm
import xml.etree.ElementTree as ET
from PIL import Image
import io
import re

# === НАСТРОЙКИ ===
OUTPUT_DIR = "data"
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
METADATA_FILE = os.path.join(OUTPUT_DIR, "metadata.jsonl")
NUM_SAMPLES = 50

os.makedirs(IMAGES_DIR, exist_ok=True)

# === СЦЕНАРИИ ===
SCENARIOS = {
    "hr_hiring": {
        "roles": ["HR-менеджер", "Кандидат", "Техлид", "СБ"],
        "start": ["Получение резюме", "Отклик на сайте"],
        "tasks": ["Скрининг резюме", "Назначение интервью", "Техническое интервью", "Запрос документов", "Подготовка оффера"],
        "conditions": ["Кандидат подходит?", "Проверка СБ пройдена?", "Оффер принят?"],
        "end": ["Отказ отправлен", "Кандидат оформлен"]
    },
    "procurement": {
        "roles": ["Закупщик", "Поставщик", "Бухгалтер", "Склад"],
        "start": ["Создание заявки", "Сигнал о нехватке"],
        "tasks": ["Запрос КП", "Сравнение цен", "Согласование бюджета", "Оплата счета", "Приемка товара"],
        "conditions": ["В рамках бюджета?", "Товар в наличии?", "Брак есть?"],
        "end": ["Закупка отменена", "Товар на складе"]
    },
    "dev_process": {
        "roles": ["Разработчик", "QA", "Product Owner", "DevOps"],
        "start": ["Создание тикета", "Баг-репорт"],
        "tasks": ["Написание кода", "Code Review", "Автотесты", "Деплой на стейдж", "Обновление доки"],
        "conditions": ["Тесты зеленые?", "Review пройден?", "Есть блокеры?"],
        "end": ["Релиз в прод", "Возврат в бэклог"]
    },
     "pizza_delivery": {
        "roles": ["Клиент", "Оператор", "Повар", "Курьер"],
        "start": ["Звонок в пиццерию", "Заказ в приложении"],
        "tasks": ["Подтверждение заказа", "Приготовление теста", "Добавление начинки", "Выпекание", "Доставка"],
        "conditions": ["Оплата прошла?", "Адрес корректен?", "Клиент на связи?"],
        "end": ["Пицца доставлена", "Заказ аннулирован"]
    }
}

import os
import random
import json
import re
import graphviz
from tqdm import tqdm

# === НАСТРОЙКИ ===
OUTPUT_DIR = "data"
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
ANNOTATIONS_FILE = os.path.join(OUTPUT_DIR, "metadata.jsonl")
NUM_SAMPLES = 50 
DPI = 100  # Важно фиксировать DPI для точного пересчета координат

os.makedirs(IMAGES_DIR, exist_ok=True)

# === СЦЕНАРИИ (Те же самые) ===
SCENARIOS = {
    "hr_hiring": {
        "roles": ["HR-менеджер", "Кандидат", "Техлид", "СБ"],
        "start": ["Получение резюме", "Отклик на сайте"],
        "tasks": ["Скрининг резюме", "Назначение интервью", "Техническое интервью", "Запрос документов", "Подготовка оффера"],
        "conditions": ["Кандидат подходит?", "Проверка СБ пройдена?", "Оффер принят?"],
        "end": ["Отказ отправлен", "Кандидат оформлен"]
    },
    "procurement": {
        "roles": ["Закупщик", "Поставщик", "Бухгалтер", "Склад"],
        "start": ["Создание заявки", "Сигнал о нехватке"],
        "tasks": ["Запрос КП", "Сравнение цен", "Согласование бюджета", "Оплата счета", "Приемка товара"],
        "conditions": ["В рамках бюджета?", "Товар в наличии?", "Брак есть?"],
        "end": ["Закупка отменена", "Товар на складе"]
    },
    "pizza_delivery": {
        "roles": ["Клиент", "Оператор", "Повар", "Курьер"],
        "start": ["Звонок в пиццерию", "Заказ в приложении"],
        "tasks": ["Подтверждение заказа", "Приготовление теста", "Добавление начинки", "Выпекание", "Доставка"],
        "conditions": ["Оплата прошла?", "Адрес корректен?", "Клиент на связи?"],
        "end": ["Пицца доставлена", "Заказ аннулирован"]
    }
}

class LabeledBPMNGenerator:
    def __init__(self):
        self.node_counter = 0
        self.steps_log = []

    # ---- id / logging ----
    def _get_id(self):
        self.node_counter += 1
        return f"n{self.node_counter}"

    def _log_step(self, action, role):
        self.steps_log.append({"action": action, "role": role})

    def _generate_markdown_table(self):
        md = "| № | Наименование действия | Роль |\n|---|---|---|\n"
        for i, s in enumerate(self.steps_log, 1):
            md += f"| {i} | {s['action']} | {s['role']} |\n"
        return md

    # ---- graphviz units -> pixels ----
    def _gv_point_to_px(self, x_pt, y_pt, img_h_px):
        scale = DPI / 72.0
        x_px = float(x_pt) * scale
        y_px = float(y_pt) * scale
        # invert Y
        return x_px, img_h_px - y_px

    def _parse_bb_from_layout(self, pos_str, w_inch, h_inch, img_h_px):
        if not pos_str:
            cx, cy = 0.0, 0.0
        else:
            parts = pos_str.split(',')
            cx, cy = float(parts[0]), float(parts[1])
        cx_px, cy_px = self._gv_point_to_px(cx, cy, img_h_px)
        w_px = float(w_inch) * DPI
        h_px = float(h_inch) * DPI
        x1 = cx_px - w_px / 2.0
        y1 = cy_px - h_px / 2.0
        x2 = cx_px + w_px / 2.0
        y2 = cy_px + h_px / 2.0
        return [int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))]

    # ---- helpers ----
    def _centroid(self, bbox):
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    def _extract_point_pairs_from_edge_pos(self, pos_str, img_h_px):
        """Parse Graphviz edge 'pos' string into list of (x_px,y_px)."""
        if not pos_str:
            return []
        import re
        nums = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", pos_str)
        pts = []
        for i in range(0, len(nums) - 1, 2):
            try:
                x = float(nums[i])
                y = float(nums[i + 1])
            except:
                continue
            x_px, y_px = self._gv_point_to_px(x, y, img_h_px)
            pts.append((x_px, y_px))
        return pts

    # ---- main generator ----
    def generate(self, filename_base):
        # reset
        self.node_counter = 0
        self.steps_log = []

        # pick scenario / roles
        scenario_key = random.choice(list(SCENARIOS.keys()))
        scenario = SCENARIOS[scenario_key]
        active_roles = random.sample(scenario["roles"], k=random.randint(2, min(3, len(scenario["roles"]))))

        # prepare graphviz
        dot = graphviz.Digraph('BPMN', format='png')
        dot.attr(dpi=str(DPI))
        dot.attr(rankdir='LR', splines='ortho', nodesep='0.6', ranksep='0.8')
        dot.attr('node', fontname='Arial', fontsize='10', style='filled', fillcolor='white')

        # structures
        lane_nodes = {role: [] for role in active_roles}
        edges_created = []   # logical edges (src_id, dst_id)
        node_metadata = {}

        # --- build simple process ---
        current_role = active_roles[0]
        start_id = self._get_id()
        start_text = random.choice(scenario["start"])
        lane_nodes[current_role].append((start_id, "start", start_text))
        self._log_step(start_text, current_role)
        current_id = start_id

        steps_left = random.randint(3, 5)
        while steps_left > 0:
            steps_left -= 1
            if random.random() < 0.3:
                current_role = random.choice(active_roles)
            task_text = random.choice(scenario["tasks"])
            next_id = self._get_id()
            lane_nodes[current_role].append((next_id, "task", task_text))
            edges_created.append((current_id, next_id))
            self._log_step(task_text, current_role)
            current_id = next_id

        end_id = self._get_id()
        end_text = random.choice(scenario["end"])
        lane_nodes[current_role].append((end_id, "end", end_text))
        edges_created.append((current_id, end_id))
        self._log_step(end_text, current_role)

        # --- draw nodes ---
        for i, role in enumerate(active_roles):
            with dot.subgraph(name=f'cluster_{i}') as c:
                c.attr(label=role, style='filled', color='#EEEEEE')
                for nid, ntype, nlabel in lane_nodes[role]:
                    node_metadata[nid] = {"type": ntype, "text": nlabel, "role": role}
                    if ntype == 'start':
                        c.node(nid, label=nlabel, shape='circle', style='filled', fillcolor='#DFFFE0')
                    elif ntype == 'end':
                        c.node(nid, label=nlabel, shape='doublecircle', style='filled', fillcolor='#FFD0D0')
                    else:
                        c.node(nid, label=nlabel, shape='box', style='rounded,filled', fillcolor='white')

        # add logical edges
        for src, dst in edges_created:
            dot.edge(src, dst)

        # --- layout JSON ---
        json_layout_str = dot.pipe(format='json').decode('utf-8')
        layout_data = json.loads(json_layout_str)

        bb = layout_data.get('bb', '0,0,0,0').split(',')
        img_width = int(float(bb[2]) * (DPI / 72.0))
        img_height = int(float(bb[3]) * (DPI / 72.0))

        # --- objects from layout ---
        objects = []
        for obj in layout_data.get('objects', []):
            name = obj.get('name', '')
            if name not in node_metadata:
                continue
            meta = node_metadata[name]
            pos = obj.get('pos', '0,0')
            w_inch = obj.get('width', '0')
            h_inch = obj.get('height', '0')
            bbox = self._parse_bb_from_layout(pos, w_inch, h_inch, img_height)
            objects.append({
                "id": name,
                "class": meta['type'],
                "text": meta['text'],
                "role": meta['role'],
                "bbox": bbox,
                "confidence": 1.0
            })

        obj_by_id = {o['id']: o for o in objects}

        # ---- arrows with coords (try real spline; fallback -> orth polyline from centers) ----
        arrows = []
        # Pre-index layout edges by base tail/head for faster lookup
        layout_edges = layout_data.get('edges', [])
        indexed_edges = {}
        for e in layout_edges:
            tail = e.get('tail')
            head = e.get('head')
            if tail is None or head is None:
                continue
            tail_base = str(tail).split(':')[0]
            head_base = str(head).split(':')[0]
            indexed_edges.setdefault((tail_base, head_base), []).append(e)

        for src_id, tgt_id in edges_created:
            edge_coords = []

            # 1) try exact match in layout edges (strip ports)
            matches = indexed_edges.get((src_id, tgt_id), [])
            if matches:
                # prefer first match that yields non-empty pos parse
                for e in matches:
                    pts = self._extract_point_pairs_from_edge_pos(e.get('pos', ''), img_height)
                    if pts:
                        edge_coords = [[int(round(x)), int(round(y))] for x, y in pts]
                        break

            # 2) if not found via exact match, try reverse: sometimes head/tail swapped in JSON (rare)
            if not edge_coords:
                matches_rev = indexed_edges.get((tgt_id, src_id), [])
                for e in matches_rev:
                    pts = self._extract_point_pairs_from_edge_pos(e.get('pos', ''), img_height)
                    if pts:
                        # if swapped, reverse points to match logical direction
                        pts = list(reversed(pts))
                        edge_coords = [[int(round(x)), int(round(y))] for x, y in pts]
                        break

            # 3) fallback: construct orthogonal polyline using bbox centers
            if not edge_coords:
                s_obj = obj_by_id.get(src_id)
                t_obj = obj_by_id.get(tgt_id)
                if s_obj and t_obj:
                    sx, sy = self._centroid(s_obj['bbox'])
                    tx, ty = self._centroid(t_obj['bbox'])
                    # construct orthogonal L-shape (src_center -> (sx, ty) -> tgt_center)
                    p1 = (int(round(sx)), int(round(sy)))
                    p2 = (int(round(sx)), int(round(ty)))
                    p3 = (int(round(tx)), int(round(ty)))
                    edge_coords = [list(p1), list(p2), list(p3)]
                else:
                    # last-resort: empty or try any partial match by text
                    edge_coords = []

            arrows.append({
                "source": src_id,
                "target": tgt_id,
                "points": edge_coords
            })

        # --- render png on disk ---
        out_path = os.path.join(IMAGES_DIR, filename_base)
        dot.render(out_path, cleanup=True)

        # --- final annotation ---
        annotation = {
            "file_name": f"{filename_base}.png",
            "image_size": [img_width, img_height],
            "text": self._generate_markdown_table(),
            "objects": objects,
            "arrows": arrows
        }
        return annotation


def main():
    print(f"Генерация {NUM_SAMPLES} примеров с BBox и JSON разметкой...")
    if os.path.exists(ANNOTATIONS_FILE): os.remove(ANNOTATIONS_FILE)
        
    gen = LabeledBPMNGenerator()
    
    with open(ANNOTATIONS_FILE, 'w', encoding='utf-8') as f:
        for i in tqdm(range(NUM_SAMPLES)):
            fname = f"bpmn_train_{i:03d}"
            try:
                data = gen.generate(fname)
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
            except Exception as e:
                print(f"Error on {fname}: {e}")
                # import traceback; traceback.print_exc()

    print(f"Готово! Данные в {OUTPUT_DIR}")

if __name__ == "__main__":
    main()