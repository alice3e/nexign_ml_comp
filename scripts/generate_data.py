import os
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
    main()