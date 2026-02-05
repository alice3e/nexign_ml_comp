import random
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
from pathlib import Path
import uuid
import subprocess
import tempfile

class BPMNGenerator:
    def __init__(self):
        self.namespaces = {
            'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
            'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
            'dc': 'http://www.omg.org/spec/DD/20100524/DC',
            'di': 'http://www.omg.org/spec/DD/20100524/DI'
        }
        
        for prefix, uri in self.namespaces.items():
            ET.register_namespace(prefix, uri)
    
    def generate_process(self, scenario_name, scenario_data, variant=0):
        """Генерирует BPMN процесс и метаданные для одного сценария"""
        
        # Случайный выбор элементов для вариативности
        start_event = random.choice(scenario_data['start'])
        end_event = random.choice(scenario_data['end'])
        
        # Выбираем случайное подмножество задач
        tasks = scenario_data.get('tasks', [])
        if isinstance(tasks[0], dict):
            task_names = [t['name'] for t in tasks]
        else:
            task_names = tasks
            
        num_tasks = random.randint(3, min(7, len(task_names)))
        selected_task_names = random.sample(task_names, num_tasks)
        
        # Создаем элементы процесса
        process_id = f"Process_{scenario_name}_{variant}"
        
        # Создаем корневой элемент
        root = ET.Element('definitions')
        root.set('xmlns:bpmn', self.namespaces['bpmn'])
        root.set('xmlns:bpmndi', self.namespaces['bpmndi'])
        root.set('xmlns:dc', self.namespaces['dc'])
        root.set('xmlns:di', self.namespaces['di'])
        
        # Создаем процесс
        process = ET.SubElement(root, 'process')
        process.set('id', process_id)
        process.set('isExecutable', 'false')
        
        # Создаем элементы и сохраняем информацию для разметки
        elements = []
        flows = []
        
        # Стартовое событие
        start_id = f"StartEvent_{uuid.uuid4().hex[:8]}"
        start_elem = ET.SubElement(process, 'startEvent')
        start_elem.set('id', start_id)
        start_elem.set('name', start_event)
        
        elements.append({
            'id': start_id,
            'name': start_event,
            'type': 'startEvent',
            'role': random.choice(scenario_data['roles'])
        })
        
        # Добавляем задачи
        task_elements = []
        for i, task_name in enumerate(selected_task_names):
            task_id = f"Task_{uuid.uuid4().hex[:8]}"
            task_elem = ET.SubElement(process, 'task')
            task_elem.set('id', task_id)
            task_elem.set('name', task_name)
            
            task_role = random.choice(scenario_data['roles'])
            
            elements.append({
                'id': task_id,
                'name': task_name,
                'type': 'task',
                'role': task_role
            })
            task_elements.append(task_id)
        
        # Конечное событие
        end_id = f"EndEvent_{uuid.uuid4().hex[:8]}"
        end_elem = ET.SubElement(process, 'endEvent')
        end_elem.set('id', end_id)
        end_elem.set('name', end_event)
        
        elements.append({
            'id': end_id,
            'name': end_event,
            'type': 'endEvent',
            'role': random.choice(scenario_data['roles'])
        })
        
        # Создаем последовательности (потоки)
        all_elements = [start_id] + task_elements + [end_id]
        
        for i in range(len(all_elements) - 1):
            flow_id = f"Flow_{uuid.uuid4().hex[:8]}"
            flow = ET.SubElement(process, 'sequenceFlow')
            flow.set('id', flow_id)
            flow.set('sourceRef', all_elements[i])
            flow.set('targetRef', all_elements[i + 1])
            
            flows.append({
                'id': flow_id,
                'source': all_elements[i],
                'target': all_elements[i + 1]
            })
        
        # Генерируем метаданные
        metadata = self._generate_metadata(scenario_name, variant, elements, flows)
        
        return root, metadata
    
    def _generate_metadata(self, scenario_name, variant, elements, flows):
        """Генерирует метаданные в требуемом формате"""
        
        # Определяем размер изображения
        num_elements = len(elements)
        image_width = 100 + num_elements * 250
        image_height = 300
        
        # Генерируем текстовое представление
        text_lines = ["| № | Наименование действия | Роль |"]
        text_lines.append("|---|---|---|")
        
        for i, element in enumerate(elements):
            if element['role']:  # Пропускаем элементы без ролей
                text_lines.append(f"| {i+1} | {element['name']} | {element['role']} |")
        
        text = "\n".join(text_lines)
        
        # Генерируем объекты с bounding boxes
        objects = []
        for i, element in enumerate(elements):
            # Расчет bounding box на основе примерных координат
            if element['type'] in ['startEvent', 'endEvent']:
                width, height = 36, 36
            elif element['type'] == 'gateway':
                width, height = 50, 50
            else:
                width, height = 150, 80
            
            x = 100 + i * 200
            y = 100
            
            # Конвертируем типы BPMN в ваши классы
            if element['type'] == 'startEvent':
                class_name = 'start'
            elif element['type'] == 'endEvent':
                class_name = 'end'
            elif element['type'] == 'gateway':
                class_name = 'gateway'
            else:
                class_name = 'task'
            
            objects.append({
                "id": f"n{i+1}",
                "class": class_name,
                "text": element['name'],
                "role": element['role'] if element['role'] else "",
                "bbox": [x, y, x + width, y + height],
                "confidence": 1.0
            })
        
        # Генерируем стрелки
        arrows = []
        for i in range(len(elements) - 1):
            source_obj = objects[i]
            target_obj = objects[i + 1]
            
            source_center_x = (source_obj['bbox'][0] + source_obj['bbox'][2]) / 2
            source_center_y = (source_obj['bbox'][1] + source_obj['bbox'][3]) / 2
            target_center_x = (target_obj['bbox'][0] + target_obj['bbox'][2]) / 2
            target_center_y = (target_obj['bbox'][1] + target_obj['bbox'][3]) / 2
            
            arrows.append({
                "source": source_obj['id'],
                "target": target_obj['id'],
                "points": [
                    [source_center_x, source_center_y],
                    [target_center_x, target_center_y]
                ]
            })
        
        # Формируем финальную структуру метаданных
        metadata = {
            "file_name": f"bpmn_{scenario_name}_{variant:03d}.png",
            "image_size": [int(image_width), int(image_height)],
            "text": text,
            "objects": objects,
            "arrows": arrows
        }
        
        return metadata
    
    def save_bpmn(self, root, filename):
        """Сохраняет BPMN XML в файл"""
        
        # Преобразуем XML в красивую строку
        xml_str = ET.tostring(root, encoding='unicode')
        
        # Парсим для красивого форматирования
        parsed = minidom.parseString(xml_str)
        pretty_xml = parsed.toprettyxml(indent="  ")
        
        # Убираем пустые строки
        pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
    
    def convert_to_png(self, bpmn_file, png_file):
        """Конвертирует BPMN XML в PNG используя graphviz"""
        try:
            print(f"Конвертирую {bpmn_file} в {png_file} с помощью graphviz")
            
            import graphviz
            import xml.etree.ElementTree as ET
            
            # Парсим BPMN XML
            tree = ET.parse(bpmn_file)
            root = tree.getroot()
            
            # Определяем namespace
            ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}
            
            # Создаем граф graphviz
            dot = graphviz.Digraph(
                comment='BPMN Diagram', 
                format='png',
                graph_attr={'rankdir': 'LR', 'splines': 'line'},
                node_attr={'style': 'filled', 'fontname': 'Arial'},
                edge_attr={'fontname': 'Arial'}
            )
            
            # Собираем все элементы
            elements = {}
            
            # Находим все элементы
            for elem_type in ['startEvent', 'endEvent', 'task', 'exclusiveGateway']:
                for elem in root.findall(f'.//bpmn:{elem_type}', ns):
                    elem_id = elem.get('id')
                    elem_name = elem.get('name', elem_id)
                    elements[elem_id] = {
                        'type': elem_type,
                        'name': elem_name,
                        'label': elem_name
                    }
            
            # Добавляем элементы в граф
            for elem_id, elem_data in elements.items():
                if elem_data['type'] == 'startEvent':
                    dot.node(elem_id, label='●', shape='circle', 
                            style='filled', fillcolor='#4CAF50', fontsize='20')
                elif elem_data['type'] == 'endEvent':
                    dot.node(elem_id, label='●', shape='circle', 
                            style='filled', fillcolor='#F44336', fontsize='20')
                elif elem_data['type'] == 'exclusiveGateway':
                    dot.node(elem_id, label='', shape='diamond', 
                            style='filled', fillcolor='#FFC107', width='0.8', height='0.8')
                else:  # task
                    dot.node(elem_id, label=elem_data['label'], shape='box',
                            style='rounded,filled', fillcolor='#E3F2FD',
                            width='1.5', height='0.8')
            
            # Находим все sequenceFlow (связи)
            for flow in root.findall('.//bpmn:sequenceFlow', ns):
                source_ref = flow.get('sourceRef')
                target_ref = flow.get('targetRef')
                
                if source_ref in elements and target_ref in elements:
                    dot.edge(source_ref, target_ref, arrowhead='normal')
            
            # Сохраняем в файл (без расширения .png в названии)
            output_base = png_file.replace('.png', '')
            dot.render(filename=output_base, cleanup=True, format='png')
            
            # Проверяем результат
            if os.path.exists(png_file) and os.path.getsize(png_file) > 0:
                print(f"✅ Успешно создано: {png_file} ({os.path.getsize(png_file)} байт)")
                return True
            else:
                print(f"❌ Файл не создан: {png_file}")
                return False
                
        except ImportError:
            print("❌ graphviz не установлен. Установите: uv add graphviz")
            return False
        except Exception as e:
            print(f"❌ Ошибка при конвертации: {e}")
            import traceback
            traceback.print_exc()
            
            # Пробуем альтернативный метод через npx
            return self._convert_with_npx_backup(bpmn_file, png_file)
    
    def _convert_with_npx_backup(self, bpmn_file, png_file):
        """Резервный метод: использует npx если graphviz не сработал"""
        try:
            print(f"Пробую резервный метод npx для {bpmn_file}")
            
            # Используем npx для запуска bpmn-js-cli
            cmd = ['npx', 'bpmn-js-cli@latest', 'render', bpmn_file, '-o', png_file]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                if os.path.exists(png_file) and os.path.getsize(png_file) > 0:
                    print(f"✅ Успешно создано через npx: {png_file}")
                    return True
                else:
                    print(f"❌ npx создал пустой файл: {png_file}")
            else:
                print(f"❌ Ошибка npx: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Ошибка npx: {e}")
        
        # Если все методы не сработали, создаем простую схему через PIL
        return self._create_simple_bpmn_image(bpmn_file, png_file)
    
    def _create_simple_bpmn_image(self, bpmn_file, png_file):
        """Создает простую BPMN схему через PIL"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Читаем BPMN файл чтобы понять структуру
            import xml.etree.ElementTree as ET
            tree = ET.parse(bpmn_file)
            root = tree.getroot()
            ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}
            
            # Собираем элементы
            elements = []
            for elem in root.findall('.//bpmn:*', ns):
                elem_type = elem.tag.split('}')[-1]
                elem_name = elem.get('name', elem_type)
                if elem_type in ['startEvent', 'endEvent', 'task']:
                    elements.append({
                        'type': elem_type,
                        'name': elem_name
                    })
            
            # Создаем изображение
            width = 800
            height = 400
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            
            # Рисуем элементы
            x_spacing = width // (len(elements) + 1)
            y = height // 2
            
            for i, elem in enumerate(elements):
                x = (i + 1) * x_spacing
                
                # Рисуем элемент
                if elem['type'] == 'startEvent':
                    # Зеленый круг
                    draw.ellipse([x-20, y-20, x+20, y+20], fill='green', outline='black')
                elif elem['type'] == 'endEvent':
                    # Красный круг
                    draw.ellipse([x-20, y-20, x+20, y+20], fill='red', outline='black')
                else:  # task
                    # Синий прямоугольник
                    draw.rectangle([x-50, y-30, x+50, y+30], fill='lightblue', outline='black')
                    # Текст
                    draw.text((x-40, y-10), elem['name'], fill='black')
                
                # Соединяем стрелками
                if i > 0:
                    draw.line([prev_x+20, y, x-20, y], fill='black', width=2)
                    # Стрелка
                    draw.polygon([x-25, y-5, x-25, y+5, x-15, y], fill='black')
                
                prev_x = x
            
            # Сохраняем
            img.save(png_file)
            print(f"✓ Создана простая схема: {png_file}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка создания простой схемы: {e}")
            return False

# Ваши сценарии
SCENARIOS = {
    "hr_hiring": {
        "roles": ["HR-менеджер", "Кандидат", "Техлид", "СБ"],
        "start": ["Получение резюме", "Отклик на сайте"],
        "tasks": ["Скрининг резюме", "Назначение интервью", "Техническое интервью", "Запрос документов", "Подготовка оффера"],
        "end": ["Отказ отправлен", "Кандидат оформлен"]
    },
    "procurement": {
        "roles": ["Закупщик", "Поставщик", "Бухгалтер", "Склад"],
        "start": ["Создание заявки", "Сигнал о нехватке"],
        "tasks": ["Запрос КП", "Сравнение цен", "Согласование бюджета", "Оплата счета", "Приемка товара"],
        "end": ["Закупка отменена", "Товар на складе"]
    },
    "pizza_delivery": {
        "roles": ["Клиент", "Оператор", "Повар", "Курьер"],
        "start": ["Звонок в пиццерию", "Заказ в приложении"],
        "tasks": ["Подтверждение заказа", "Приготовление теста", "Добавление начинки", "Выпекание", "Доставка"],
        "end": ["Пицца доставлена", "Заказ аннулирован"]
    }
}

def generate_all_scenarios(scenarios, num_variants=5):
    """Генерирует несколько вариантов для каждого сценария"""
    
    generator = BPMNGenerator()
    all_metadata = []
    
    # Создаем директории для выходных файлов
    Path("bpmn_xml").mkdir(exist_ok=True)
    Path("bpmn_png").mkdir(exist_ok=True)
    Path("metadata").mkdir(exist_ok=True)
    
    successful = 0
    failed = 0
    
    for scenario_name, scenario_data in scenarios.items():
        print(f"\nГенерация сценария: {scenario_name}")
        
        for variant in range(num_variants):
            print(f"  Вариант {variant + 1}/{num_variants}")
            
            # Генерируем BPMN и метаданные
            root, metadata = generator.generate_process(scenario_name, scenario_data, variant)
            
            # Сохраняем BPMN XML
            bpmn_filename = f"bpmn_xml/{scenario_name}_{variant:03d}.bpmn"
            generator.save_bpmn(root, bpmn_filename)
            
            # Конвертируем в PNG
            png_filename = f"bpmn_png/{scenario_name}_{variant:03d}.png"
            
            if generator.convert_to_png(bpmn_filename, png_filename):
                # Сохраняем метаданные только если PNG успешно создан
                metadata_filename = f"metadata/{scenario_name}_{variant:03d}.json"
                with open(metadata_filename, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                
                all_metadata.append(metadata)
                successful += 1
                print(f"  ✅ Успешно создан вариант {variant}")
            else:
                print(f"  ❌ Не удалось создать вариант {variant}")
                # Удаляем BPMN файл, если PNG не создан
                if os.path.exists(bpmn_filename):
                    os.remove(bpmn_filename)
                failed += 1
    
    # Сохраняем все метаданные в один файл
    if all_metadata:
        with open("metadata/all_metadata.json", 'w', encoding='utf-8') as f:
            json.dump(all_metadata, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*50}")
    print(f"ИТОГ:")
    print(f"✅ Успешно создано: {successful} диаграмм")
    print(f"❌ Не удалось создать: {failed} диаграмм")
    if successful > 0:
        print(f"📁 XML файлы: bpmn_xml/")
        print(f"🖼️  PNG файлы: bpmn_png/") 
        print(f"📊 Метаданные: metadata/")
    print(f"{'='*50}")

# Тестовый запуск
if __name__ == "__main__":
    print("Начинаем генерацию BPMN диаграмм...")
    generate_all_scenarios(SCENARIOS, num_variants=3)