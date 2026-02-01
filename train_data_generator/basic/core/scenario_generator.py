"""
Генератор бизнес-сценариев для создания реалистичных BPMN диаграмм.
"""

import random
from typing import Dict, List, Any, Optional
from data.business_scenarios import BUSINESS_SCENARIOS


class ScenarioGenerator:
    """Генератор реалистичных бизнес-сценариев."""
    
    def __init__(self, language: str = 'ru', seed: Optional[int] = None):
        """
        Инициализация генератора сценариев.
        
        Args:
            language: Язык ('ru' или 'en')
            seed: Seed для генератора случайных чисел
        """
        self.language = language
        self.rng = random.Random(seed)
        self.scenarios = BUSINESS_SCENARIOS[language]
        self.node_counter = 0
        self.edge_counter = 0
    
    def _generate_node_id(self) -> str:
        """Генерация уникального ID для узла."""
        self.node_counter += 1
        return f"node_{self.node_counter}"
    
    def _generate_edge_id(self) -> str:
        """Генерация уникального ID для связи."""
        self.edge_counter += 1
        return f"edge_{self.edge_counter}"
    
    def generate_linear_scenario(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Генерация линейного сценария из бизнес-процесса.
        
        Args:
            domain: Домен (finance/logistics/hr/it) или None для случайного
            
        Returns:
            Словарь с узлами и связями
        """
        # Выбрать домен
        if domain is None:
            domain = self.rng.choice(list(self.scenarios.keys()))
        
        # Выбрать процесс
        process = self.rng.choice(self.scenarios[domain]['processes'])
        steps = process['steps']
        
        nodes = []
        edges = []
        
        # Start Event
        start_id = self._generate_node_id()
        nodes.append({
            'id': start_id,
            'type': 'StartEvent',
            'name': 'Start' if self.language == 'en' else 'Старт',
            'x': 100,
            'y': 100,
            'width': 36,
            'height': 36
        })
        
        prev_id = start_id
        x_offset = 100
        
        # Tasks из сценария
        for step in steps:
            task_id = self._generate_node_id()
            x_offset += 150
            nodes.append({
                'id': task_id,
                'type': 'Task',
                'name': step,
                'x': x_offset,
                'y': 82,
                'width': 100,
                'height': 80
            })
            
            edges.append({
                'id': self._generate_edge_id(),
                'source': prev_id,
                'target': task_id,
                'name': ''
            })
            
            prev_id = task_id
        
        # End Event
        end_id = self._generate_node_id()
        x_offset += 150
        nodes.append({
            'id': end_id,
            'type': 'EndEvent',
            'name': 'End' if self.language == 'en' else 'Конец',
            'x': x_offset,
            'y': 100,
            'width': 36,
            'height': 36
        })
        
        edges.append({
            'id': self._generate_edge_id(),
            'source': prev_id,
            'target': end_id,
            'name': ''
        })
        
        return {
            'pattern': 'scenario_linear',
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'domain': domain,
                'process_name': process['name'],
                'language': self.language
            }
        }
    
    def generate_xor_scenario(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Генерация XOR сценария с условным ветвлением.
        
        Args:
            domain: Домен или None для случайного
            
        Returns:
            Словарь с узлами и связями
        """
        # Выбрать домен и процесс
        if domain is None:
            domain = self.rng.choice(list(self.scenarios.keys()))
        
        process = self.rng.choice(self.scenarios[domain]['processes'])
        steps = process['steps']
        conditions = process['conditions']
        branches = process['branches']
        
        nodes = []
        edges = []
        
        # Start Event
        start_id = self._generate_node_id()
        nodes.append({
            'id': start_id,
            'type': 'StartEvent',
            'name': 'Start' if self.language == 'en' else 'Старт',
            'x': 100,
            'y': 200,
            'width': 36,
            'height': 36
        })
        
        # Первые задачи (до ветвления)
        prev_id = start_id
        x_offset = 100
        num_before = min(2, len(steps) - 2)
        
        for i in range(num_before):
            task_id = self._generate_node_id()
            x_offset += 150
            nodes.append({
                'id': task_id,
                'type': 'Task',
                'name': steps[i],
                'x': x_offset,
                'y': 182,
                'width': 100,
                'height': 80
            })
            
            edges.append({
                'id': self._generate_edge_id(),
                'source': prev_id,
                'target': task_id,
                'name': ''
            })
            
            prev_id = task_id
        
        # XOR Split
        xor_split_id = self._generate_node_id()
        x_offset += 150
        condition = self.rng.choice(conditions)
        nodes.append({
            'id': xor_split_id,
            'type': 'ExclusiveGateway',
            'name': condition,
            'x': x_offset,
            'y': 197,
            'width': 50,
            'height': 50
        })
        
        edges.append({
            'id': self._generate_edge_id(),
            'source': prev_id,
            'target': xor_split_id,
            'name': ''
        })
        
        # Ветки
        yes_label = self.rng.choice(branches['yes'])
        no_label = self.rng.choice(branches['no'])
        
        # Верхняя ветка (Yes)
        x_offset += 150
        y_top = 100
        remaining_steps = steps[num_before:]
        num_yes_tasks = min(2, len(remaining_steps))
        
        yes_tasks = []
        for i in range(num_yes_tasks):
            task_id = self._generate_node_id()
            nodes.append({
                'id': task_id,
                'type': 'Task',
                'name': remaining_steps[i] if i < len(remaining_steps) else f"Task {i+1}",
                'x': x_offset + (i * 150),
                'y': y_top - 18,
                'width': 100,
                'height': 80
            })
            yes_tasks.append(task_id)
        
        # Связь от split к первой задаче yes
        edges.append({
            'id': self._generate_edge_id(),
            'source': xor_split_id,
            'target': yes_tasks[0],
            'name': yes_label
        })
        
        # Связи между задачами yes
        for i in range(len(yes_tasks) - 1):
            edges.append({
                'id': self._generate_edge_id(),
                'source': yes_tasks[i],
                'target': yes_tasks[i + 1],
                'name': ''
            })
        
        # Нижняя ветка (No)
        y_bottom = 300
        num_no_tasks = min(2, len(remaining_steps) - num_yes_tasks)
        
        no_tasks = []
        for i in range(num_no_tasks):
            task_id = self._generate_node_id()
            step_idx = num_yes_tasks + i
            nodes.append({
                'id': task_id,
                'type': 'Task',
                'name': remaining_steps[step_idx] if step_idx < len(remaining_steps) else f"Alternative Task {i+1}",
                'x': x_offset + (i * 150),
                'y': y_bottom - 18,
                'width': 100,
                'height': 80
            })
            no_tasks.append(task_id)
        
        # Связь от split к первой задаче no
        edges.append({
            'id': self._generate_edge_id(),
            'source': xor_split_id,
            'target': no_tasks[0],
            'name': no_label
        })
        
        # Связи между задачами no
        for i in range(len(no_tasks) - 1):
            edges.append({
                'id': self._generate_edge_id(),
                'source': no_tasks[i],
                'target': no_tasks[i + 1],
                'name': ''
            })
        
        # XOR Join
        join_x = x_offset + max(len(yes_tasks), len(no_tasks)) * 150
        xor_join_id = self._generate_node_id()
        nodes.append({
            'id': xor_join_id,
            'type': 'ExclusiveGateway',
            'name': '',
            'x': join_x,
            'y': 197,
            'width': 50,
            'height': 50
        })
        
        edges.append({
            'id': self._generate_edge_id(),
            'source': yes_tasks[-1],
            'target': xor_join_id,
            'name': ''
        })
        
        edges.append({
            'id': self._generate_edge_id(),
            'source': no_tasks[-1],
            'target': xor_join_id,
            'name': ''
        })
        
        # End Event
        end_id = self._generate_node_id()
        nodes.append({
            'id': end_id,
            'type': 'EndEvent',
            'name': 'End' if self.language == 'en' else 'Конец',
            'x': join_x + 150,
            'y': 200,
            'width': 36,
            'height': 36
        })
        
        edges.append({
            'id': self._generate_edge_id(),
            'source': xor_join_id,
            'target': end_id,
            'name': ''
        })
        
        return {
            'pattern': 'scenario_xor',
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'domain': domain,
                'process_name': process['name'],
                'condition': condition,
                'language': self.language
            }
        }
    
    def generate_parallel_scenario(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Генерация параллельного сценария.
        
        Args:
            domain: Домен или None для случайного
            
        Returns:
            Словарь с узлами и связями
        """
        # Выбрать домен и процесс
        if domain is None:
            domain = self.rng.choice(list(self.scenarios.keys()))
        
        process = self.rng.choice(self.scenarios[domain]['processes'])
        steps = process['steps']
        
        nodes = []
        edges = []
        
        # Start Event
        start_id = self._generate_node_id()
        nodes.append({
            'id': start_id,
            'type': 'StartEvent',
            'name': 'Start' if self.language == 'en' else 'Старт',
            'x': 100,
            'y': 200,
            'width': 36,
            'height': 36
        })
        
        # Задача перед split
        task_before_id = self._generate_node_id()
        nodes.append({
            'id': task_before_id,
            'type': 'Task',
            'name': steps[0] if steps else "Initial Task",
            'x': 200,
            'y': 182,
            'width': 100,
            'height': 80
        })
        
        edges.append({
            'id': self._generate_edge_id(),
            'source': start_id,
            'target': task_before_id,
            'name': ''
        })
        
        # AND Split
        and_split_id = self._generate_node_id()
        nodes.append({
            'id': and_split_id,
            'type': 'ParallelGateway',
            'name': '',
            'x': 350,
            'y': 197,
            'width': 50,
            'height': 50
        })
        
        edges.append({
            'id': self._generate_edge_id(),
            'source': task_before_id,
            'target': and_split_id,
            'name': ''
        })
        
        # Параллельные ветки (2-3 ветки)
        num_branches = min(3, len(steps) - 1)
        branch_tasks = []
        y_start = 100
        y_step = 150
        
        for i in range(num_branches):
            task_id = self._generate_node_id()
            y_pos = y_start + (i * y_step)
            step_idx = i + 1
            
            nodes.append({
                'id': task_id,
                'type': 'Task',
                'name': steps[step_idx] if step_idx < len(steps) else f"Parallel Task {i+1}",
                'x': 500,
                'y': y_pos - 18,
                'width': 100,
                'height': 80
            })
            
            edges.append({
                'id': self._generate_edge_id(),
                'source': and_split_id,
                'target': task_id,
                'name': ''
            })
            
            branch_tasks.append(task_id)
        
        # AND Join
        and_join_id = self._generate_node_id()
        nodes.append({
            'id': and_join_id,
            'type': 'ParallelGateway',
            'name': '',
            'x': 650,
            'y': 197,
            'width': 50,
            'height': 50
        })
        
        for task_id in branch_tasks:
            edges.append({
                'id': self._generate_edge_id(),
                'source': task_id,
                'target': and_join_id,
                'name': ''
            })
        
        # Задача после join
        if len(steps) > num_branches + 1:
            task_after_id = self._generate_node_id()
            nodes.append({
                'id': task_after_id,
                'type': 'Task',
                'name': steps[num_branches + 1],
                'x': 750,
                'y': 182,
                'width': 100,
                'height': 80
            })
            
            edges.append({
                'id': self._generate_edge_id(),
                'source': and_join_id,
                'target': task_after_id,
                'name': ''
            })
            
            prev_id = task_after_id
            x_end = 900
        else:
            prev_id = and_join_id
            x_end = 750
        
        # End Event
        end_id = self._generate_node_id()
        nodes.append({
            'id': end_id,
            'type': 'EndEvent',
            'name': 'End' if self.language == 'en' else 'Конец',
            'x': x_end,
            'y': 200,
            'width': 36,
            'height': 36
        })
        
        edges.append({
            'id': self._generate_edge_id(),
            'source': prev_id,
            'target': end_id,
            'name': ''
        })
        
        return {
            'pattern': 'scenario_parallel',
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'domain': domain,
                'process_name': process['name'],
                'num_branches': num_branches,
                'language': self.language
            }
        }