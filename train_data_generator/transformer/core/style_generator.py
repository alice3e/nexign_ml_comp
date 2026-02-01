"""
Модуль для генерации случайных стилей рендеринга BPMN диаграмм.
"""

import random
from typing import Dict, Any, Tuple


class StyleGenerator:
    """Генератор случайных стилей для BPMN диаграмм."""
    
    def __init__(self, config: Dict[str, Any], seed: int = None):
        """
        Инициализация генератора стилей.
        
        Args:
            config: Конфигурация из config.yaml
            seed: Seed для генератора случайных чисел
        """
        self.config = config
        self.rng = random.Random(seed)
    
    def generate_style(self) -> Dict[str, Any]:
        """
        Генерация случайного стиля.
        
        Returns:
            Словарь с параметрами стиля
        """
        # Выбор темы
        themes = self.config['rendering']['themes']
        theme_weights = self.config['rendering']['theme_weights']
        theme = self.rng.choices(
            themes,
            weights=[theme_weights[t] for t in themes]
        )[0]
        
        # Выбор цветовой палитры для темы
        palette = self.config['color_palettes'][theme]
        colors = {
            'background': self.rng.choice(palette['background']),
            'task_fill': self.rng.choice(palette['task_fill']),
            'task_stroke': self.rng.choice(palette['task_stroke']),
            'gateway_fill': self.rng.choice(palette['gateway_fill']),
            'gateway_stroke': self.rng.choice(palette['gateway_stroke']),
            'event_fill': self.rng.choice(palette['event_fill']),
            'event_stroke': self.rng.choice(palette['event_stroke']),
            'flow_stroke': self.rng.choice(palette['flow_stroke']),
            'text_color': self.rng.choice(palette['text_color'])
        }
        
        # Выбор шрифта
        font_family = self.rng.choice(self.config['fonts']['available'])
        font_sizes = {
            'task_name': self.rng.choice(self.config['fonts']['task_name_size']),
            'gateway_name': self.rng.choice(self.config['fonts']['gateway_name_size']),
            'event_name': self.rng.choice(self.config['fonts']['event_name_size']),
            'flow_label': self.rng.choice(self.config['fonts']['flow_label_size'])
        }
        
        # Геометрические параметры
        geometry = {
            'task_stroke_width': self.rng.choice(self.config['geometry']['task_stroke_width']),
            'gateway_stroke_width': self.rng.choice(self.config['geometry']['gateway_stroke_width']),
            'event_stroke_width': self.rng.choice(self.config['geometry']['event_stroke_width']),
            'flow_stroke_width': self.rng.choice(self.config['geometry']['flow_stroke_width']),
            'task_corner_radius': self.rng.choice(self.config['geometry']['task_corner_radius']),
            'arrow_size': self.rng.choice(self.config['geometry']['arrow_size']),
            'text_padding': self.rng.choice(self.config['geometry']['text_padding']),
            'line_spacing': self.rng.choice(self.config['geometry']['line_spacing'])
        }
        
        # Разрешение
        resolution = self.rng.randint(
            self.config['rendering']['min_resolution'],
            self.config['rendering']['max_resolution']
        )
        
        return {
            'theme': theme,
            'colors': colors,
            'font_family': font_family,
            'font_sizes': font_sizes,
            'geometry': geometry,
            'resolution': resolution
        }
    
    def generate_augmentation_params(self) -> Dict[str, Any]:
        """
        Генерация параметров аугментации.
        
        Returns:
            Словарь с параметрами аугментации
        """
        aug_config = self.config['augmentation']
        aug_probs = self.config['augmentation_probabilities']
        
        params = {}
        
        # Label offset
        if aug_config['label_offset']['enabled'] and self.rng.random() < aug_probs['label_offset']:
            params['label_offset'] = {
                'x': self.rng.uniform(-aug_config['label_offset']['max_x'], 
                                     aug_config['label_offset']['max_x']),
                'y': self.rng.uniform(-aug_config['label_offset']['max_y'], 
                                     aug_config['label_offset']['max_y'])
            }
        
        # Rotation
        if aug_config['rotation']['enabled'] and self.rng.random() < aug_probs['rotation']:
            params['rotation'] = self.rng.uniform(
                aug_config['rotation']['min_angle'],
                aug_config['rotation']['max_angle']
            )
        
        # Zoom and pan
        if aug_config['zoom_pan']['enabled'] and self.rng.random() < aug_probs['zoom_pan']:
            params['zoom'] = self.rng.uniform(*aug_config['zoom_pan']['zoom_range'])
            params['pan'] = {
                'x': self.rng.uniform(*aug_config['zoom_pan']['pan_range']),
                'y': self.rng.uniform(*aug_config['zoom_pan']['pan_range'])
            }
        
        # JPEG artifacts
        if aug_config['jpeg_artifacts']['enabled'] and self.rng.random() < aug_probs['jpeg_artifacts']:
            params['jpeg_quality'] = self.rng.randint(*aug_config['jpeg_artifacts']['quality_range'])
        
        # Gaussian blur
        if aug_config['gaussian_blur']['enabled'] and self.rng.random() < aug_probs['gaussian_blur']:
            kernel = self.rng.choice(aug_config['gaussian_blur']['kernel_size'])
            if kernel > 0:
                params['gaussian_blur'] = {
                    'kernel_size': kernel,
                    'sigma': self.rng.choice(aug_config['gaussian_blur']['sigma'])
                }
        
        # Noise
        if aug_config['noise']['enabled'] and self.rng.random() < aug_probs['noise']:
            noise_level = self.rng.choice(aug_config['noise']['noise_level'])
            if noise_level > 0:
                params['noise_level'] = noise_level
        
        # Brightness and contrast
        if aug_config['brightness_contrast']['enabled'] and self.rng.random() < aug_probs['brightness_contrast']:
            params['brightness'] = self.rng.uniform(*aug_config['brightness_contrast']['brightness_range'])
            params['contrast'] = self.rng.uniform(*aug_config['brightness_contrast']['contrast_range'])
        
        # Perspective distortion
        if aug_config['perspective']['enabled'] and self.rng.random() < aug_probs['perspective']:
            params['perspective_distortion'] = aug_config['perspective']['max_distortion']
        
        return params
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """
        Конвертация HEX цвета в RGB.
        
        Args:
            hex_color: Цвет в формате #RRGGBB
            
        Returns:
            Кортеж (R, G, B)
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))