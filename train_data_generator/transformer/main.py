#!/usr/bin/env python3
"""
Главный скрипт трансформера BPMN → PNG.
Преобразует BPMN XML диаграммы в PNG изображения с различными стилями и аугментациями.
"""

import os
import json
import argparse
import shutil
from pathlib import Path
from typing import Dict, Any
import yaml

from core import BPMNRendererJS, StyleGenerator, ImageAugmentor, BPMNParser


class BPMNTransformer:
    """Трансформер BPMN XML → PNG."""
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        Инициализация трансформера.
        
        Args:
            config_path: Путь к конфигурационному файлу
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.input_dir = Path(self.config['input_dir'])
        self.output_dir = Path(self.config['output_dir'])
        
        # Создать выходную директорию
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def transform_dataset(self):
        """Трансформация всего датасета."""
        # Найти все BPMN файлы
        bpmn_dir = self.input_dir / 'bpmn'
        if not bpmn_dir.exists():
            print(f"Ошибка: директория {bpmn_dir} не найдена")
            return
        
        bpmn_files = sorted(bpmn_dir.glob('*.bpmn'))
        total_files = len(bpmn_files)
        
        print(f"Найдено {total_files} BPMN файлов для трансформации...")
        
        for idx, bpmn_file in enumerate(bpmn_files, 1):
            sample_name = bpmn_file.stem
            print(f"[{idx}/{total_files}] Обработка {sample_name}...")
            
            try:
                self._transform_sample(sample_name)
            except Exception as e:
                print(f"  Ошибка при обработке {sample_name}: {e}")
                continue
            
            if idx % 100 == 0:
                print(f"Обработано {idx}/{total_files} файлов...")
        
        print(f"Трансформация завершена! Обработано {total_files} файлов.")
        print(f"Результаты сохранены в: {self.output_dir}")
    
    def _transform_sample(self, sample_name: str):
        """
        Трансформация одного примера.
        
        Args:
            sample_name: Имя примера (без расширения)
        """
        # Пути к входным файлам
        bpmn_path = self.input_dir / 'bpmn' / f"{sample_name}.bpmn"
        ir_path = self.input_dir / 'ir' / f"{sample_name}.json"
        desc_path = self.input_dir / 'descriptions' / f"{sample_name}.txt"
        # Для LLM-gen описания в .md формате
        desc_md_path = self.input_dir / 'descriptions' / f"{sample_name}.md"
        meta_path = self.input_dir / 'metadata' / f"{sample_name}_meta.json"
        
        # Проверка существования BPMN файла (обязательно)
        if not bpmn_path.exists():
            raise FileNotFoundError(f"Не найден BPMN файл для {sample_name}")
        
        # Чтение BPMN
        with open(bpmn_path, 'r', encoding='utf-8') as f:
            bpmn_xml = f.read()
        
        # Чтение IR если есть (для basic генератора), иначе None (для LLM-gen)
        ir_json = None
        if ir_path.exists():
            with open(ir_path, 'r', encoding='utf-8') as f:
                ir_json = json.load(f)
        
        # Извлечь seed из метаданных если есть
        seed = None
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                seed = metadata.get('seed')
        
        # Если IR нет (LLM-gen), парсим BPMN XML для извлечения координат
        if ir_json is None:
            parser = BPMNParser()
            ir_json = parser.parse(bpmn_xml)
        
        # Генерация стиля
        style_gen = StyleGenerator(self.config, seed=seed)
        style = style_gen.generate_style()
        aug_params = style_gen.generate_augmentation_params()
        
        # Рендеринг BPMN в изображение с использованием bpmn-js (Playwright)
        renderer = BPMNRendererJS(style)
        image = renderer.render(bpmn_xml, ir_json)
        
        # Применение аугментаций
        if aug_params:
            augmentor = ImageAugmentor(aug_params)
            image = augmentor.augment(image)
        
        # Создание выходной директории для примера
        if self.config['file_organization']['separate_dirs']:
            sample_id = int(sample_name.split('_')[1])
            output_sample_dir = self.output_dir / self.config['file_organization']['dir_name_format'].format(id=sample_id)
            output_sample_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_sample_dir = self.output_dir
        
        # Сохранение PNG
        png_path = output_sample_dir / f"{sample_name}.png"
        image.save(png_path, 'PNG')
        
        # Копирование BPMN файла
        bpmn_output_path = output_sample_dir / f"{sample_name}.bpmn"
        shutil.copy2(bpmn_path, bpmn_output_path)
        
        # Копирование описания если есть (.txt для basic, .md для LLM-gen)
        if desc_path.exists():
            desc_output_path = output_sample_dir / f"{sample_name}.txt"
            shutil.copy2(desc_path, desc_output_path)
        elif desc_md_path.exists():
            desc_output_path = output_sample_dir / f"{sample_name}.md"
            shutil.copy2(desc_md_path, desc_output_path)
        
        # Копирование IR если есть (только для basic генератора)
        if ir_json is not None and ir_path.exists():
            ir_output_path = output_sample_dir / f"{sample_name}_ir.json"
            shutil.copy2(ir_path, ir_output_path)
        
        # Копирование метаданных если есть
        if meta_path.exists():
            meta_output_path = output_sample_dir / f"{sample_name}_meta.json"
            shutil.copy2(meta_path, meta_output_path)
        
        # Сохранение параметров рендеринга
        render_params = {
            'style': {
                'theme': style['theme'],
                'resolution': style['resolution'],
                'font_family': style['font_family'],
                'colors': style['colors'],
                'geometry': style['geometry']
            },
            'augmentation': aug_params
        }
        
        render_params_path = output_sample_dir / f"{sample_name}_render.json"
        with open(render_params_path, 'w', encoding='utf-8') as f:
            json.dump(render_params, f, ensure_ascii=False, indent=2)


def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(
        description='Трансформер BPMN XML → PNG с стилизацией и аугментацией'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Путь к конфигурационному файлу (по умолчанию: config.yaml)'
    )
    
    args = parser.parse_args()
    
    # Создать и запустить трансформер
    transformer = BPMNTransformer(config_path=args.config)
    transformer.transform_dataset()


if __name__ == '__main__':
    main()