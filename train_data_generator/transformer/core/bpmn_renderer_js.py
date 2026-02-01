"""
Модуль для рендеринга BPMN XML в PNG изображение с использованием bpmn-js.
Использует Node.js скрипт для высококачественного рендеринга.
"""

import os
import subprocess
import tempfile
import json
from pathlib import Path
from PIL import Image
from typing import Dict, Any, Optional


class BPMNRendererJS:
    """Рендерер BPMN диаграмм в PNG с использованием bpmn-js."""
    
    def __init__(self, style: Dict[str, Any]):
        """
        Инициализация рендерера.
        
        Args:
            style: Словарь с параметрами стиля
        """
        self.style = style
        self.colors = style['colors']
        self.geometry = style['geometry']
        
        # Путь к Node.js скрипту
        self.renderer_dir = Path(__file__).parent.parent / 'renderer'
        self.renderer_script = self.renderer_dir / 'bpmn_to_png.js'
        
        # Проверить наличие Node.js
        self._check_nodejs()
        
        # Проверить наличие зависимостей
        self._check_dependencies()
    
    def _check_nodejs(self):
        """Проверка наличия Node.js."""
        try:
            result = subprocess.run(
                ['node', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("Node.js не установлен или недоступен")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            raise RuntimeError(
                "Node.js не найден. Установите Node.js >= 18.0.0 для рендеринга BPMN.\n"
                "Скачать: https://nodejs.org/"
            )
    
    def _check_dependencies(self):
        """Проверка и установка Node.js зависимостей."""
        package_json = self.renderer_dir / 'package.json'
        node_modules = self.renderer_dir / 'node_modules'
        
        if not package_json.exists():
            raise RuntimeError(f"Не найден package.json в {self.renderer_dir}")
        
        # Если node_modules не существует, установить зависимости
        if not node_modules.exists():
            print("Установка Node.js зависимостей для рендеринга BPMN...")
            try:
                result = subprocess.run(
                    ['npm', 'install'],
                    cwd=self.renderer_dir,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 минут на установку
                )
                if result.returncode != 0:
                    raise RuntimeError(
                        f"Ошибка установки зависимостей:\n{result.stderr}"
                    )
                print("Зависимости успешно установлены")
            except subprocess.TimeoutExpired:
                raise RuntimeError("Таймаут при установке зависимостей")
            except FileNotFoundError:
                raise RuntimeError(
                    "npm не найден. Установите Node.js с npm.\n"
                    "Скачать: https://nodejs.org/"
                )
    
    def render(self, bpmn_xml: str, ir_json: Optional[Dict[str, Any]] = None) -> Image.Image:
        """
        Рендеринг BPMN диаграммы в изображение.
        
        Args:
            bpmn_xml: BPMN XML строка
            ir_json: IR JSON с координатами (не используется, для совместимости)
            
        Returns:
            PIL Image объект
        """
        # Создать временные файлы
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bpmn', delete=False, encoding='utf-8') as bpmn_file:
            bpmn_file.write(bpmn_xml)
            bpmn_path = bpmn_file.name
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as png_file:
            png_path = png_file.name
        
        try:
            # Подготовить опции рендеринга
            options = {
                'width': self.style['resolution'],
                'height': self.style['resolution'],
                'backgroundColor': self.colors['background'],
                'scale': 1.0,
                'padding': 20
            }
            
            # Вызвать Node.js скрипт
            result = subprocess.run(
                [
                    'node',
                    str(self.renderer_script),
                    bpmn_path,
                    png_path,
                    json.dumps(options)
                ],
                capture_output=True,
                text=True,
                timeout=60  # 60 секунд на рендеринг
            )
            
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else result.stdout
                raise RuntimeError(f"Ошибка рендеринга BPMN:\n{error_msg}")
            
            # Загрузить PNG изображение
            if not os.path.exists(png_path) or os.path.getsize(png_path) == 0:
                raise RuntimeError("Рендеринг не создал PNG файл")
            
            image = Image.open(png_path)
            
            # Применить дополнительные стилизации если нужно
            image = self._apply_style_adjustments(image)
            
            return image
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Таймаут при рендеринге BPMN (>60 сек)")
        finally:
            # Удалить временные файлы
            try:
                os.unlink(bpmn_path)
            except:
                pass
            try:
                os.unlink(png_path)
            except:
                pass
    
    def _apply_style_adjustments(self, image: Image.Image) -> Image.Image:
        """
        Применение дополнительных стилевых корректировок к изображению.
        
        Args:
            image: Исходное изображение
            
        Returns:
            Скорректированное изображение
        """
        # Здесь можно добавить дополнительные корректировки
        # например, изменение цветовой схемы для темной темы
        
        theme = self.style.get('theme', 'light')
        
        if theme == 'dark':
            # Для темной темы можно инвертировать цвета или применить фильтры
            # Пока оставляем как есть, так как bpmn-js рендерит с правильными цветами
            pass
        
        return image