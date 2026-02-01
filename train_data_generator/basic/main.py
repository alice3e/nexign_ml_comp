#!/usr/bin/env python3
"""
Главный скрипт генератора базовых BPMN диаграмм.
Генерирует BPMN XML, текстовые описания, IR JSON и метаданные.
"""

import os
import json
import random
import argparse
from pathlib import Path
from typing import Dict, Any
import yaml

from core import BPMNGenerator, PatternGenerator, TextGenerator, IRGenerator, ScenarioGenerator


class BPMNDatasetGenerator:
    """Генератор датасета BPMN диаграмм."""
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        Инициализация генератора.
        
        Args:
            config_path: Путь к конфигурационному файлу
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.output_dir = Path(self.config['output_dir'])
        self.seed = self.config.get('seed')
        
        # Создать выходные директории
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'bpmn').mkdir(exist_ok=True)
        (self.output_dir / 'descriptions').mkdir(exist_ok=True)
        (self.output_dir / 'ir').mkdir(exist_ok=True)
        (self.output_dir / 'metadata').mkdir(exist_ok=True)
        
        # Инициализация генераторов
        self.bpmn_gen = BPMNGenerator()
        self.ir_gen = IRGenerator()
    
    def generate_dataset(self):
        """Генерация полного датасета."""
        total_samples = self.config['generation']['total_samples']
        lang_dist = self.config['generation']['language_distribution']
        pattern_dist = self.config['generation']['pattern_distribution']
        text_formats = self.config['text_generation']['formats']
        
        print(f"Генерация {total_samples} примеров BPMN диаграмм...")
        
        # Определить количество примеров для каждого языка
        num_ru = int(total_samples * lang_dist['ru'])
        num_en = total_samples - num_ru
        
        sample_id = 0
        
        # Генерация для русского языка
        for i in range(num_ru):
            sample_id += 1
            self._generate_sample(sample_id, 'ru', pattern_dist, text_formats)
            
            if sample_id % 100 == 0:
                print(f"Сгенерировано {sample_id}/{total_samples} примеров...")
        
        # Генерация для английского языка
        for i in range(num_en):
            sample_id += 1
            self._generate_sample(sample_id, 'en', pattern_dist, text_formats)
            
            if sample_id % 100 == 0:
                print(f"Сгенерировано {sample_id}/{total_samples} примеров...")
        
        print(f"Генерация завершена! Всего создано {sample_id} примеров.")
        print(f"Результаты сохранены в: {self.output_dir}")
    
    def _generate_sample(
        self,
        sample_id: int,
        language: str,
        pattern_dist: Dict[str, float],
        text_formats: Dict[str, float]
    ):
        """
        Генерация одного примера.
        
        Args:
            sample_id: ID примера
            language: Язык ('ru' или 'en')
            pattern_dist: Распределение паттернов
            text_formats: Распределение форматов текста
        """
        # Выбрать паттерн
        pattern = random.choices(
            list(pattern_dist.keys()),
            weights=list(pattern_dist.values())
        )[0]
        
        # Выбрать формат текста
        text_format = random.choices(
            list(text_formats.keys()),
            weights=list(text_formats.values())
        )[0]
        
        # Создать seed для этого примера
        if self.seed is not None:
            sample_seed = self.seed + sample_id
        else:
            sample_seed = None
        
        # Генерация графа
        if pattern.startswith('scenario_'):
            # Бизнес-сценарий
            scenario_gen = ScenarioGenerator(language=language, seed=sample_seed)
            domain_dist = self.config['generation']['domain_distribution']
            domain = random.choices(
                list(domain_dist.keys()),
                weights=list(domain_dist.values())
            )[0]
            
            if pattern == 'scenario_linear':
                graph = scenario_gen.generate_linear_scenario(domain)
            elif pattern == 'scenario_xor':
                graph = scenario_gen.generate_xor_scenario(domain)
            elif pattern == 'scenario_parallel':
                graph = scenario_gen.generate_parallel_scenario(domain)
            else:
                raise ValueError(f"Unknown scenario pattern: {pattern}")
        else:
            # Базовый паттерн
            pattern_gen = PatternGenerator(language=language, seed=sample_seed)
            
            if pattern == 'linear':
                num_tasks = random.randint(
                    self.config['generation']['complexity']['min_tasks'],
                    self.config['generation']['complexity']['max_tasks']
                )
                graph = pattern_gen.generate_linear(num_tasks)
            
            elif pattern == 'xor_branch':
                tasks_per_branch = random.randint(1, 3)
                graph = pattern_gen.generate_xor_branch(tasks_per_branch)
            
            elif pattern == 'parallel':
                num_branches = random.randint(2, 3)
                graph = pattern_gen.generate_parallel(num_branches)
            
            elif pattern == 'loop':
                graph = pattern_gen.generate_loop()
            
            elif pattern == 'combined':
                # Для комбинированных паттернов используем XOR с большим количеством задач
                tasks_per_branch = random.randint(2, 4)
                graph = pattern_gen.generate_xor_branch(tasks_per_branch)
            
            else:
                raise ValueError(f"Unknown pattern: {pattern}")
        
        # Генерация BPMN XML
        bpmn_xml = self.bpmn_gen.generate_bpmn(graph)
        
        # Генерация текстового описания
        text_gen = TextGenerator(language=language)
        
        if text_format == 'steps':
            description = text_gen.generate_steps(graph)
        else:  # pseudocode
            description = text_gen.generate_pseudocode(graph)
        
        # Генерация IR JSON
        ir_json = self.ir_gen.generate_ir(graph)
        
        # Генерация метаданных
        metadata = {
            'sample_id': sample_id,
            'language': language,
            'pattern': pattern,
            'text_format': text_format,
            'seed': sample_seed,
            'complexity': {
                'num_nodes': len(graph['nodes']),
                'num_edges': len(graph['edges'])
            },
            'graph_metadata': graph.get('metadata', {})
        }
        
        # Сохранение файлов
        sample_name = f"sample_{sample_id:06d}"
        
        # BPMN XML
        bpmn_path = self.output_dir / 'bpmn' / f"{sample_name}.bpmn"
        with open(bpmn_path, 'w', encoding='utf-8') as f:
            f.write(bpmn_xml)
        
        # Текстовое описание
        desc_path = self.output_dir / 'descriptions' / f"{sample_name}.txt"
        with open(desc_path, 'w', encoding='utf-8') as f:
            f.write(description)
        
        # IR JSON
        ir_path = self.output_dir / 'ir' / f"{sample_name}.json"
        with open(ir_path, 'w', encoding='utf-8') as f:
            f.write(ir_json)
        
        # Метаданные
        meta_path = self.output_dir / 'metadata' / f"{sample_name}_meta.json"
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)


def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(
        description='Генератор базовых BPMN диаграмм для обучения VLM'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Путь к конфигурационному файлу (по умолчанию: config.yaml)'
    )
    
    args = parser.parse_args()
    
    # Создать и запустить генератор
    generator = BPMNDatasetGenerator(config_path=args.config)
    generator.generate_dataset()


if __name__ == '__main__':
    main()