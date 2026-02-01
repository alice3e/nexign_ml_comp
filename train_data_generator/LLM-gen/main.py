#!/usr/bin/env python3
"""
Главный скрипт LLM генератора BPMN диаграмм.
Обрабатывает промпты из директории и генерирует BPMN XML и описания.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List
import yaml

from core import ElizaClient, ResponseParser


class BPMNLLMGenerator:
    """Генератор BPMN диаграмм с использованием LLM."""
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        Инициализация генератора.
        
        Args:
            config_path: Путь к конфигурационному файлу
        """
        # Загрузка конфигурации
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # Настройка логирования
        self._setup_logging()
        
        # Инициализация путей
        self.output_dir = Path(self.config['output_dir'])
        self.prompts_dir = Path(self.config['prompts_dir'])
        
        # Создание выходных директорий
        self._create_output_dirs()
        
        # Загрузка системного промпта
        self.system_prompt = self._load_system_prompt()
        
        # Инициализация клиента и парсера
        api_config = self.config['api']
        self.client = ElizaClient(
            model=api_config['model'],
            temperature=api_config['temperature'],
            max_tokens=api_config['max_tokens'],
            timeout=api_config['timeout']
        )
        self.parser = ResponseParser()
        
        self.logger.info("BPMNLLMGenerator инициализирован")
    
    def _setup_logging(self):
        """Настройка логирования."""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_file = log_config.get('log_file', 'llm_generator.log')
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _create_output_dirs(self):
        """Создание выходных директорий."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'bpmn').mkdir(exist_ok=True)
        (self.output_dir / 'descriptions').mkdir(exist_ok=True)
        (self.output_dir / 'metadata').mkdir(exist_ok=True)
        (self.output_dir / 'raw_responses').mkdir(exist_ok=True)
        
        self.logger.info(f"Выходные директории созданы в: {self.output_dir}")
    
    def _load_system_prompt(self) -> str:
        """
        Загрузка системного промпта.
        
        Returns:
            Текст системного промпта
        """
        system_prompt_path = Path('system_prompt.md')
        if not system_prompt_path.exists():
            raise FileNotFoundError(
                f"Системный промпт не найден: {system_prompt_path}"
            )
        
        with open(system_prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()
        
        self.logger.info("Системный промпт загружен")
        return system_prompt
    
    def _load_prompts(self) -> List[Path]:
        """
        Загрузка списка промптов из директории.
        
        Returns:
            Список путей к файлам промптов
        """
        if not self.prompts_dir.exists():
            raise FileNotFoundError(
                f"Директория с промптами не найдена: {self.prompts_dir}"
            )
        
        prompt_files = sorted(self.prompts_dir.glob('*.md'))
        
        if not prompt_files:
            raise ValueError(
                f"Не найдено промптов в директории: {self.prompts_dir}"
            )
        
        self.logger.info(f"Найдено {len(prompt_files)} промптов")
        return prompt_files
    
    def _generate_sample_id(self, prompt_file: Path) -> str:
        """
        Генерация ID для примера на основе имени файла промпта.
        
        Args:
            prompt_file: Путь к файлу промпта
        
        Returns:
            ID примера
        """
        # Извлекаем номер из имени файла (например, prompt_001_... -> 001)
        filename = prompt_file.stem
        parts = filename.split('_')
        
        if len(parts) >= 2 and parts[1].isdigit():
            return f"llm_{parts[1]}"
        else:
            # Если не удалось извлечь номер, используем имя файла
            return f"llm_{filename}"
    
    def generate_from_prompt(self, prompt_file: Path) -> Dict[str, Any]:
        """
        Генерация BPMN диаграммы из одного промпта.
        
        Args:
            prompt_file: Путь к файлу с промптом
        
        Returns:
            Словарь с результатами генерации
        """
        sample_id = self._generate_sample_id(prompt_file)
        
        self.logger.info(f"Обработка промпта: {prompt_file.name} (ID: {sample_id})")
        
        # Загрузка промпта
        with open(prompt_file, 'r', encoding='utf-8') as f:
            user_prompt = f.read()
        
        try:
            # Генерация ответа от модели
            self.logger.info("Отправка запроса в LLM...")
            response_text = self.client.generate_bpmn(user_prompt, self.system_prompt)
            
            # Сохранение сырого ответа
            raw_response_path = self.output_dir / 'raw_responses' / f"{sample_id}_raw.txt"
            with open(raw_response_path, 'w', encoding='utf-8') as f:
                f.write(response_text)
            self.logger.info(f"Сырой ответ сохранен: {raw_response_path}")
            
            # Парсинг ответа
            self.logger.info("Парсинг ответа модели...")
            bpmn_xml, description_md = self.parser.parse_response(response_text)
            
            if not bpmn_xml:
                self.logger.error(f"Не удалось извлечь BPMN XML из ответа для {sample_id}")
                return {
                    'sample_id': sample_id,
                    'status': 'failed',
                    'error': 'Failed to extract BPMN XML'
                }
            
            if not description_md:
                self.logger.warning(f"Не удалось извлечь описание из ответа для {sample_id}")
                description_md = "# Описание недоступно\n\nОписание не было извлечено из ответа модели."
            
            # Исправление XML если необходимо
            if self.config['validation']['auto_fix']:
                bpmn_xml = self.parser.fix_common_xml_issues(bpmn_xml)
            
            # Валидация BPMN
            if self.config['validation']['check_bpmn_validity']:
                if not self.parser.validate_bpmn(bpmn_xml):
                    self.logger.warning(f"BPMN XML не прошел валидацию для {sample_id}")
            
            # Сохранение файлов
            # 1. BPMN XML
            bpmn_path = self.output_dir / 'bpmn' / f"{sample_id}.bpmn"
            with open(bpmn_path, 'w', encoding='utf-8') as f:
                f.write(bpmn_xml)
            self.logger.info(f"BPMN XML сохранен: {bpmn_path}")
            
            # 2. Текстовое описание
            desc_path = self.output_dir / 'descriptions' / f"{sample_id}.md"
            with open(desc_path, 'w', encoding='utf-8') as f:
                f.write(description_md)
            self.logger.info(f"Описание сохранено: {desc_path}")
            
            # 3. Метаданные
            metadata = {
                'sample_id': sample_id,
                'prompt_file': str(prompt_file),
                'model': self.config['api']['model'],
                'temperature': self.config['api']['temperature'],
                'max_tokens': self.config['api']['max_tokens'],
                'bpmn_file': str(bpmn_path),
                'description_file': str(desc_path),
                'raw_response_file': str(raw_response_path),
                'status': 'success'
            }
            
            meta_path = self.output_dir / 'metadata' / f"{sample_id}_meta.json"
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Метаданные сохранены: {meta_path}")
            
            return metadata
        
        except Exception as e:
            self.logger.error(f"Ошибка при обработке {prompt_file.name}: {e}", exc_info=True)
            return {
                'sample_id': sample_id,
                'prompt_file': str(prompt_file),
                'status': 'failed',
                'error': str(e)
            }
    
    def generate_all(self) -> List[Dict[str, Any]]:
        """
        Генерация BPMN диаграмм для всех промптов.
        
        Returns:
            Список результатов генерации
        """
        prompt_files = self._load_prompts()
        results = []
        
        self.logger.info(f"Начало генерации для {len(prompt_files)} промптов")
        
        for i, prompt_file in enumerate(prompt_files, 1):
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Обработка {i}/{len(prompt_files)}: {prompt_file.name}")
            self.logger.info(f"{'='*60}")
            
            result = self.generate_from_prompt(prompt_file)
            results.append(result)
            
            # В последовательном режиме делаем паузу между запросами
            if self.config['generation']['sequential_mode'] and i < len(prompt_files):
                self.logger.info("Ожидание перед следующим запросом...")
                import time
                time.sleep(2)  # Пауза 2 секунды между запросами
        
        # Сохранение сводного отчета
        self._save_summary(results)
        
        return results
    
    def _save_summary(self, results: List[Dict[str, Any]]):
        """
        Сохранение сводного отчета о генерации.
        
        Args:
            results: Список результатов генерации
        """
        summary = {
            'total': len(results),
            'successful': sum(1 for r in results if r['status'] == 'success'),
            'failed': sum(1 for r in results if r['status'] == 'failed'),
            'results': results
        }
        
        summary_path = self.output_dir / 'generation_summary.json'
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info("СВОДКА ГЕНЕРАЦИИ")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"Всего промптов: {summary['total']}")
        self.logger.info(f"Успешно: {summary['successful']}")
        self.logger.info(f"Ошибок: {summary['failed']}")
        self.logger.info(f"Сводный отчет сохранен: {summary_path}")
        self.logger.info(f"{'='*60}\n")


def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(
        description='LLM генератор BPMN диаграмм'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Путь к конфигурационному файлу (по умолчанию: config.yaml)'
    )
    parser.add_argument(
        '--prompt',
        type=str,
        help='Путь к конкретному промпту (если не указан, обрабатываются все)'
    )
    
    args = parser.parse_args()
    
    try:
        # Создание и запуск генератора
        generator = BPMNLLMGenerator(config_path=args.config)
        
        if args.prompt:
            # Обработка одного промпта
            prompt_path = Path(args.prompt)
            if not prompt_path.exists():
                print(f"ОШИБКА: Файл промпта не найден: {prompt_path}")
                sys.exit(1)
            
            result = generator.generate_from_prompt(prompt_path)
            
            if result['status'] == 'success':
                print(f"\n✓ Успешно сгенерирована диаграмма: {result['sample_id']}")
                print(f"  BPMN: {result['bpmn_file']}")
                print(f"  Описание: {result['description_file']}")
            else:
                print(f"\n✗ Ошибка генерации: {result.get('error', 'Unknown error')}")
                sys.exit(1)
        else:
            # Обработка всех промптов
            results = generator.generate_all()
            
            # Вывод результатов
            successful = sum(1 for r in results if r['status'] == 'success')
            print(f"\n{'='*60}")
            print(f"Генерация завершена!")
            print(f"Успешно: {successful}/{len(results)}")
            print(f"Результаты сохранены в: {generator.output_dir}")
            print(f"{'='*60}\n")
    
    except Exception as e:
        print(f"\nОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()