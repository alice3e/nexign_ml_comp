"""
Модуль для рендеринга BPMN XML в PNG изображение.
"""

from lxml import etree
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, List, Tuple
import math


class BPMNRenderer:
    """Рендерер BPMN диаграмм в PNG."""
    
    def __init__(self, style: Dict[str, Any]):
        """
        Инициализация рендерера.
        
        Args:
            style: Словарь с параметрами стиля
        """
        self.style = style
        self.colors = style['colors']
        self.geometry = style['geometry']
        self.font_sizes = style['font_sizes']
        
        # Использование встроенного шрифта PIL с поддержкой Unicode
        # Попробуем найти системные шрифты с поддержкой кириллицы
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
        ]
        
        font_loaded = False
        for font_path in font_paths:
            try:
                self.font_task = ImageFont.truetype(font_path, self.font_sizes['task_name'])
                self.font_gateway = ImageFont.truetype(font_path, self.font_sizes['gateway_name'])
                self.font_event = ImageFont.truetype(font_path, self.font_sizes['event_name'])
                self.font_flow = ImageFont.truetype(font_path, self.font_sizes['flow_label'])
                font_loaded = True
                break
            except:
                continue
        
        if not font_loaded:
            # Fallback на дефолтный шрифт PIL
            self.font_task = ImageFont.load_default()
            self.font_gateway = ImageFont.load_default()
            self.font_event = ImageFont.load_default()
            self.font_flow = ImageFont.load_default()
    
    def render(self, bpmn_xml: str, ir_json: Dict[str, Any]) -> Image.Image:
        """
        Рендеринг BPMN диаграммы в изображение.
        
        Args:
            bpmn_xml: BPMN XML строка
            ir_json: IR JSON с координатами
            
        Returns:
            PIL Image объект
        """
        # Парсинг IR для получения координат
        nodes = ir_json['graph']['nodes']
        edges = ir_json['graph']['edges']
        
        # Вычисление размеров canvas
        canvas_width, canvas_height = self._calculate_canvas_size(nodes)
        
        # Масштабирование под целевое разрешение
        scale = self._calculate_scale(canvas_width, canvas_height)
        
        # Создание изображения
        img = Image.new('RGB', 
                       (int(canvas_width * scale), int(canvas_height * scale)),
                       self._hex_to_rgb(self.colors['background']))
        draw = ImageDraw.Draw(img)
        
        # Рендеринг связей (сначала, чтобы они были под узлами)
        for edge in edges:
            self._draw_edge(draw, edge, nodes, scale)
        
        # Рендеринг узлов
        for node in nodes:
            self._draw_node(draw, node, scale)
        
        return img
    
    def _calculate_canvas_size(self, nodes: List[Dict[str, Any]]) -> Tuple[int, int]:
        """Вычисление размеров canvas."""
        if not nodes:
            return 800, 600
        
        max_x = max(node['coordinates']['x'] + node['coordinates']['width'] for node in nodes)
        max_y = max(node['coordinates']['y'] + node['coordinates']['height'] for node in nodes)
        
        # Добавить отступы
        padding = 50
        return int(max_x + padding), int(max_y + padding)
    
    def _calculate_scale(self, width: int, height: int) -> float:
        """Вычисление масштаба для целевого разрешения."""
        target_resolution = self.style['resolution']
        max_dimension = max(width, height)
        
        if max_dimension == 0:
            return 1.0
        
        return target_resolution / max_dimension
    
    def _draw_node(self, draw: ImageDraw.ImageDraw, node: Dict[str, Any], scale: float):
        """Рендеринг узла."""
        node_type = node['type']
        coords = node['coordinates']
        
        x = coords['x'] * scale
        y = coords['y'] * scale
        width = coords['width'] * scale
        height = coords['height'] * scale
        
        if node_type == 'Task':
            self._draw_task(draw, x, y, width, height, node['name'])
        elif node_type == 'StartEvent':
            self._draw_start_event(draw, x, y, width, height, node['name'])
        elif node_type == 'EndEvent':
            self._draw_end_event(draw, x, y, width, height, node['name'])
        elif node_type == 'ExclusiveGateway':
            self._draw_exclusive_gateway(draw, x, y, width, height, node['name'])
        elif node_type == 'ParallelGateway':
            self._draw_parallel_gateway(draw, x, y, width, height, node['name'])
    
    def _draw_task(self, draw: ImageDraw.ImageDraw, x: float, y: float,
                   width: float, height: float, name: str):
        """Рендеринг Task."""
        # Прямоугольник с скругленными углами (BPMN стандарт)
        radius = self.geometry['task_corner_radius']
        
        fill_color = self._hex_to_rgb(self.colors['task_fill'])
        stroke_color = self._hex_to_rgb(self.colors['task_stroke'])
        stroke_width = int(self.geometry['task_stroke_width'])
        
        # Рисуем прямоугольник со скругленными углами
        draw.rounded_rectangle(
            [x, y, x + width, y + height],
            radius=radius,
            fill=fill_color,
            outline=stroke_color,
            width=stroke_width
        )
        
        # Текст с переносом строк и масштабированием
        if name:
            self._draw_text_wrapped(draw, name, x, y, width, height,
                                   self.font_task, self.colors['text_color'])
    
    def _draw_start_event(self, draw: ImageDraw.ImageDraw, x: float, y: float,
                         width: float, height: float, name: str):
        """Рендеринг Start Event."""
        cx = x + width / 2
        cy = y + height / 2
        radius = min(width, height) / 2
        
        fill_color = self._hex_to_rgb(self.colors['event_fill'])
        stroke_color = self._hex_to_rgb(self.colors['event_stroke'])
        stroke_width = int(self.geometry['event_stroke_width'])
        
        # Круг
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=fill_color,
            outline=stroke_color,
            width=stroke_width
        )
        
        # Текст под кругом
        if name:
            text_y = y + height + 5
            self._draw_text_centered(draw, name, x, text_y, width, 20,
                                    self.font_event, self.colors['text_color'])
    
    def _draw_end_event(self, draw: ImageDraw.ImageDraw, x: float, y: float,
                       width: float, height: float, name: str):
        """Рендеринг End Event с двойной обводкой (BPMN стандарт)."""
        cx = x + width / 2
        cy = y + height / 2
        radius = min(width, height) / 2
        
        fill_color = self._hex_to_rgb(self.colors['event_fill'])
        stroke_color = self._hex_to_rgb(self.colors['event_stroke'])
        stroke_width = int(self.geometry['event_stroke_width'])
        
        # Внешний круг (BPMN стандарт - двойная обводка)
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=fill_color,
            outline=stroke_color,
            width=stroke_width
        )
        
        # Внутренний круг (создает эффект двойной обводки)
        inner_radius = radius - stroke_width * 2
        if inner_radius > 0:
            draw.ellipse(
                [cx - inner_radius, cy - inner_radius, cx + inner_radius, cy + inner_radius],
                fill=fill_color,
                outline=stroke_color,
                width=stroke_width
            )
        
        # Текст под кругом
        if name:
            text_y = y + height + 5
            self._draw_text_centered(draw, name, x, text_y, width, 20,
                                    self.font_event, self.colors['text_color'])
    
    def _draw_exclusive_gateway(self, draw: ImageDraw.ImageDraw, x: float, y: float,
                               width: float, height: float, name: str):
        """Рендеринг Exclusive Gateway (ромб с X)."""
        cx = x + width / 2
        cy = y + height / 2
        
        fill_color = self._hex_to_rgb(self.colors['gateway_fill'])
        stroke_color = self._hex_to_rgb(self.colors['gateway_stroke'])
        stroke_width = int(self.geometry['gateway_stroke_width'])
        
        # Ромб
        points = [
            (cx, y),           # верх
            (x + width, cy),   # право
            (cx, y + height),  # низ
            (x, cy)            # лево
        ]
        
        draw.polygon(points, fill=fill_color, outline=stroke_color)
        
        # X внутри
        margin = width * 0.3
        draw.line([x + margin, y + margin, x + width - margin, y + height - margin],
                 fill=stroke_color, width=stroke_width)
        draw.line([x + width - margin, y + margin, x + margin, y + height - margin],
                 fill=stroke_color, width=stroke_width)
        
        # Текст
        if name:
            text_y = y + height + 5
            self._draw_text_centered(draw, name, x, text_y, width, 20,
                                    self.font_gateway, self.colors['text_color'])
    
    def _draw_parallel_gateway(self, draw: ImageDraw.ImageDraw, x: float, y: float,
                              width: float, height: float, name: str):
        """Рендеринг Parallel Gateway (ромб с +)."""
        cx = x + width / 2
        cy = y + height / 2
        
        fill_color = self._hex_to_rgb(self.colors['gateway_fill'])
        stroke_color = self._hex_to_rgb(self.colors['gateway_stroke'])
        stroke_width = int(self.geometry['gateway_stroke_width'])
        
        # Ромб
        points = [
            (cx, y),
            (x + width, cy),
            (cx, y + height),
            (x, cy)
        ]
        
        draw.polygon(points, fill=fill_color, outline=stroke_color)
        
        # + внутри
        margin = width * 0.3
        # Вертикальная линия
        draw.line([cx, y + margin, cx, y + height - margin],
                 fill=stroke_color, width=stroke_width)
        # Горизонтальная линия
        draw.line([x + margin, cy, x + width - margin, cy],
                 fill=stroke_color, width=stroke_width)
        
        # Текст
        if name:
            text_y = y + height + 5
            self._draw_text_centered(draw, name, x, text_y, width, 20,
                                    self.font_gateway, self.colors['text_color'])
    
    def _draw_edge(self, draw: ImageDraw.ImageDraw, edge: Dict[str, Any],
                   nodes: List[Dict[str, Any]], scale: float):
        """Рендеринг связи (sequence flow)."""
        # Найти узлы источника и цели
        source_node = next(n for n in nodes if n['id'] == edge['source'])
        target_node = next(n for n in nodes if n['id'] == edge['target'])
        
        # Вычислить центры узлов
        source_coords = source_node['coordinates']
        target_coords = target_node['coordinates']
        
        x1 = (source_coords['x'] + source_coords['width'] / 2) * scale
        y1 = (source_coords['y'] + source_coords['height'] / 2) * scale
        x2 = (target_coords['x'] + target_coords['width'] / 2) * scale
        y2 = (target_coords['y'] + target_coords['height'] / 2) * scale
        
        stroke_color = self._hex_to_rgb(self.colors['flow_stroke'])
        stroke_width = int(self.geometry['flow_stroke_width'])
        
        # Линия
        draw.line([x1, y1, x2, y2], fill=stroke_color, width=stroke_width)
        
        # Стрелка
        self._draw_arrow(draw, x1, y1, x2, y2, stroke_color)
        
        # Метка на стрелке с фоном
        if edge.get('label'):
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            
            # Получить размер текста
            bbox = draw.textbbox((0, 0), edge['label'], font=self.font_flow)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Добавить отступы
            padding = 3
            bg_x1 = mid_x - text_width / 2 - padding
            bg_y1 = mid_y - text_height / 2 - padding
            bg_x2 = mid_x + text_width / 2 + padding
            bg_y2 = mid_y + text_height / 2 + padding
            
            # Нарисовать фон для текста (цвет фона диаграммы)
            bg_color = self._hex_to_rgb(self.colors['background'])
            draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], fill=bg_color)
            
            # Нарисовать текст
            text_x = mid_x - text_width / 2
            text_y = mid_y - text_height / 2
            draw.text((text_x, text_y), edge['label'],
                     fill=self._hex_to_rgb(self.colors['text_color']),
                     font=self.font_flow)
    
    def _draw_arrow(self, draw: ImageDraw.ImageDraw, x1: float, y1: float,
                   x2: float, y2: float, color: Tuple[int, int, int]):
        """Рисование стрелки на конце линии."""
        arrow_size = self.geometry['arrow_size']
        
        # Вычислить угол
        angle = math.atan2(y2 - y1, x2 - x1)
        
        # Точки стрелки
        arrow_angle = math.pi / 6  # 30 градусов
        
        p1_x = x2 - arrow_size * math.cos(angle - arrow_angle)
        p1_y = y2 - arrow_size * math.sin(angle - arrow_angle)
        
        p2_x = x2 - arrow_size * math.cos(angle + arrow_angle)
        p2_y = y2 - arrow_size * math.sin(angle + arrow_angle)
        
        # Рисуем стрелку
        draw.polygon([(x2, y2), (p1_x, p1_y), (p2_x, p2_y)], fill=color)
    
    def _draw_text_wrapped(self, draw: ImageDraw.ImageDraw, text: str,
                          x: float, y: float, width: float, height: float,
                          font: ImageFont.ImageFont, color: str):
        """Рисование текста с переносом строк и оптимальным масштабированием."""
        padding = self.geometry['text_padding']
        available_width = width - (2 * padding)
        available_height = height - (2 * padding)
        
        # Целевой размер текста: 40-90% от высоты блока
        min_text_height = available_height * 0.4
        max_text_height = available_height * 0.9
        
        # Начальный размер шрифта
        current_font = font
        optimal_font = font
        
        # Попытка найти оптимальный размер шрифта
        for font_path in [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "C:\\Windows\\Fonts\\arial.ttf"
        ]:
            try:
                # Начинаем с размера, который займет ~60% высоты
                target_size = int(available_height * 0.6 / self.geometry['line_spacing'])
                target_size = max(8, min(target_size, 72))  # Ограничение 8-72px
                
                test_font = ImageFont.truetype(font_path, target_size)
                
                # Разбить текст на строки с этим шрифтом
                words = text.split()
                lines = []
                current_line = []
                
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    bbox = draw.textbbox((0, 0), test_line, font=test_font)
                    line_width = bbox[2] - bbox[0]
                    
                    if line_width <= available_width:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                            current_line = [word]
                        else:
                            lines.append(word)
                
                if current_line:
                    lines.append(' '.join(current_line))
                
                # Проверить высоту
                line_height = target_size * self.geometry['line_spacing']
                total_height = len(lines) * line_height
                
                # Если текст слишком большой, уменьшить
                if total_height > max_text_height:
                    scale_factor = max_text_height / total_height
                    target_size = int(target_size * scale_factor * 0.95)
                    target_size = max(8, target_size)
                    test_font = ImageFont.truetype(font_path, target_size)
                
                # Если текст слишком маленький, увеличить
                elif total_height < min_text_height:
                    scale_factor = min_text_height / total_height
                    target_size = int(target_size * scale_factor * 0.95)
                    target_size = min(target_size, 72)
                    test_font = ImageFont.truetype(font_path, target_size)
                
                optimal_font = test_font
                break
            except:
                continue
        
        # Финальная разбивка текста с оптимальным шрифтом
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=optimal_font)
            line_width = bbox[2] - bbox[0]
            
            if line_width <= available_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Получить размер шрифта
        try:
            font_size = optimal_font.size
        except:
            font_size = 12  # fallback
        
        line_height = font_size * self.geometry['line_spacing']
        total_text_height = len(lines) * line_height
        start_y = y + (height - total_text_height) / 2
        
        # Рисовать строки
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=optimal_font)
            line_width = bbox[2] - bbox[0]
            text_x = x + (width - line_width) / 2
            text_y = start_y + (i * line_height)
            
            draw.text((text_x, text_y), line, fill=self._hex_to_rgb(color), font=optimal_font)
    
    def _draw_text_centered(self, draw: ImageDraw.ImageDraw, text: str,
                           x: float, y: float, width: float, height: float,
                           font: ImageFont.ImageFont, color: str):
        """Рисование текста по центру области (для коротких текстов)."""
        # Получить размер текста
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Вычислить позицию
        text_x = x + (width - text_width) / 2
        text_y = y + (height - text_height) / 2
        
        # Рисовать текст
        draw.text((text_x, text_y), text, fill=self._hex_to_rgb(color), font=font)
    
    def _draw_text(self, draw: ImageDraw.ImageDraw, text: str,
                  x: float, y: float, font: ImageFont.ImageFont, color: str):
        """Рисование текста в указанной позиции."""
        draw.text((x, y), text, fill=self._hex_to_rgb(color), font=font)
    
    @staticmethod
    def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Конвертация HEX в RGB."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))