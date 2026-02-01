"""
Модуль для аугментации изображений BPMN диаграмм.
Применяет различные трансформации для увеличения разнообразия датасета.
"""

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
import cv2
from typing import Dict, Any
import io


class ImageAugmentor:
    """Аугментатор изображений BPMN диаграмм."""
    
    def __init__(self, augmentation_params: Dict[str, Any]):
        """
        Инициализация аугментатора.
        
        Args:
            augmentation_params: Параметры аугментации
        """
        self.params = augmentation_params
    
    def augment(self, image: Image.Image) -> Image.Image:
        """
        Применение аугментаций к изображению.
        
        Args:
            image: Исходное изображение
            
        Returns:
            Аугментированное изображение
        """
        img = image.copy()
        
        # Применяем аугментации в определенном порядке
        
        # 1. Zoom and pan (до поворота)
        if 'zoom' in self.params:
            img = self._apply_zoom_pan(img)
        
        # 2. Rotation
        if 'rotation' in self.params:
            img = self._apply_rotation(img)
        
        # 3. Perspective distortion
        if 'perspective_distortion' in self.params:
            img = self._apply_perspective(img)
        
        # 4. Brightness and contrast
        if 'brightness' in self.params or 'contrast' in self.params:
            img = self._apply_brightness_contrast(img)
        
        # 5. Gaussian blur
        if 'gaussian_blur' in self.params:
            img = self._apply_gaussian_blur(img)
        
        # 6. Noise
        if 'noise_level' in self.params:
            img = self._apply_noise(img)
        
        # 7. JPEG artifacts (последним, т.к. это compression)
        if 'jpeg_quality' in self.params:
            img = self._apply_jpeg_artifacts(img)
        
        return img
    
    def _apply_rotation(self, image: Image.Image) -> Image.Image:
        """Применение поворота."""
        angle = self.params['rotation']
        return image.rotate(angle, expand=True, fillcolor='white')
    
    def _apply_zoom_pan(self, image: Image.Image) -> Image.Image:
        """Применение зума и панорамирования."""
        zoom = self.params['zoom']
        pan_x = self.params['pan']['x']
        pan_y = self.params['pan']['y']
        
        width, height = image.size
        
        # Новые размеры после зума
        new_width = int(width * zoom)
        new_height = int(height * zoom)
        
        # Ресайз с зумом
        img_zoomed = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Создать новое изображение исходного размера
        result = Image.new('RGB', (width, height), 'white')
        
        # Вычислить позицию вставки с учетом панорамирования
        paste_x = int((width - new_width) / 2 + pan_x)
        paste_y = int((height - new_height) / 2 + pan_y)
        
        # Вставить зумированное изображение
        result.paste(img_zoomed, (paste_x, paste_y))
        
        return result
    
    def _apply_gaussian_blur(self, image: Image.Image) -> Image.Image:
        """Применение гауссова размытия."""
        kernel_size = self.params['gaussian_blur']['kernel_size']
        sigma = self.params['gaussian_blur']['sigma']
        
        # Конвертация в numpy для использования OpenCV
        img_array = np.array(image)
        
        # Применение гауссова размытия
        blurred = cv2.GaussianBlur(img_array, (kernel_size, kernel_size), sigma)
        
        return Image.fromarray(blurred)
    
    def _apply_noise(self, image: Image.Image) -> Image.Image:
        """Применение шума."""
        noise_level = self.params['noise_level']
        
        # Конвертация в numpy
        img_array = np.array(image).astype(np.float32)
        
        # Генерация гауссова шума
        noise = np.random.normal(0, noise_level, img_array.shape)
        
        # Добавление шума
        noisy = img_array + noise
        
        # Клиппинг значений
        noisy = np.clip(noisy, 0, 255).astype(np.uint8)
        
        return Image.fromarray(noisy)
    
    def _apply_brightness_contrast(self, image: Image.Image) -> Image.Image:
        """Применение изменения яркости и контраста."""
        img = image
        
        if 'brightness' in self.params:
            brightness = self.params['brightness']
            # Brightness в PIL: 0 = черный, 1 = оригинал, >1 = ярче
            # Конвертируем из диапазона [-20, 20] в множитель
            brightness_factor = 1.0 + (brightness / 100.0)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness_factor)
        
        if 'contrast' in self.params:
            contrast = self.params['contrast']
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast)
        
        return img
    
    def _apply_jpeg_artifacts(self, image: Image.Image) -> Image.Image:
        """Применение JPEG артефактов через сжатие."""
        quality = self.params['jpeg_quality']
        
        # Сохранить в буфер с JPEG сжатием
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=quality)
        buffer.seek(0)
        
        # Загрузить обратно
        return Image.open(buffer)
    
    def _apply_perspective(self, image: Image.Image) -> Image.Image:
        """Применение перспективной дисторсии."""
        max_distortion = self.params['perspective_distortion']
        
        # Конвертация в numpy
        img_array = np.array(image)
        height, width = img_array.shape[:2]
        
        # Исходные точки (углы изображения)
        src_points = np.float32([
            [0, 0],
            [width - 1, 0],
            [width - 1, height - 1],
            [0, height - 1]
        ])
        
        # Целевые точки со случайным смещением
        max_offset = int(min(width, height) * max_distortion)
        
        dst_points = np.float32([
            [np.random.randint(-max_offset, max_offset), 
             np.random.randint(-max_offset, max_offset)],
            [width - 1 + np.random.randint(-max_offset, max_offset), 
             np.random.randint(-max_offset, max_offset)],
            [width - 1 + np.random.randint(-max_offset, max_offset), 
             height - 1 + np.random.randint(-max_offset, max_offset)],
            [np.random.randint(-max_offset, max_offset), 
             height - 1 + np.random.randint(-max_offset, max_offset)]
        ])
        
        # Вычисление матрицы перспективного преобразования
        matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        
        # Применение преобразования
        result = cv2.warpPerspective(img_array, matrix, (width, height),
                                     borderMode=cv2.BORDER_CONSTANT,
                                     borderValue=(255, 255, 255))
        
        return Image.fromarray(result)