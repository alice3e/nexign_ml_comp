"""
Модуль для генерации паттернов BPMN графов.
Реализует базовые паттерны: линейный, XOR ветвление, параллельность, циклы.
"""

import random
from typing import Dict, List, Any, Tuple
from data.dictionaries import (
    ACTIONS, OBJECTS, CONDITIONS, BRANCH_LABELS,
    LOOP_LABELS, TASK_TEMPLATES
)


class PatternGenerator:
    """Генератор паттернов BPMN графов."""
    
    def __init__(self, language: str = 'ru', seed: int = None):
        """
        Инициализация генератора паттернов.
        
        Args:
            language: Язык генерации ('ru' или 'en')
            seed: Seed для генератора случайных чисел
        """
        self.language = language
        self.rng = random.Random(seed)
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
    
    def _generate_task_name(self) -> str:
        """Генерация имени задачи."""
        action = self.rng.choice(ACTIONS[self.language])
        obj = self.rng.choice(OBJECTS[self.language])
        template = self.rng.choice(TASK_TEMPLATES[self.language])
        return template.format(action=action, object=obj)
    
    def _generate_condition(self) -> str:
        """Генерация условия для XOR Gateway."""
        return self.rng.choice(CONDITIONS[self.language])
    
    def generate_linear(self, num_tasks: int = 3) -> Dict[str, Any]:
        """
        Генерация линейного паттерна: Start → Task{n} → End.
        
        Args:
            num_tasks: Количество задач в цепочке
            
        Returns:
            Словарь с узлами и связями
        """
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
        
        # Tasks
        for i in range(num_tasks):
            task_id = self._generate_node_id()
            x_offset += 150
            nodes.append({
                'id': task_id,
                'type': 'Task',
                'name': self._generate_task_name(),
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
            'pattern': 'linear',
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'num_tasks': num_tasks,
                'language': self.language
            }
        }
    
    def generate_xor_branch(self, tasks_per_branch: int = 2) -> Dict[str, Any]:
        """
        Генерация XOR ветвления:
        Start → Task → XOR split → (Task A | Task B) → XOR join → Task → End.
        
        Args:
            tasks_per_branch: Количество задач в каждой ветке
            
        Returns:
            Словарь с узлами и связями
        """
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
        
        # Task before split
        task_before_id = self._generate_node_id()
        nodes.append({
            'id': task_before_id,
            'type': 'Task',
            'name': self._generate_task_name(),
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
        
        # XOR Split Gateway
        xor_split_id = self._generate_node_id()
        condition = self._generate_condition()
        nodes.append({
            'id': xor_split_id,
            'type': 'ExclusiveGateway',
            'name': condition,
            'x': 350,
            'y': 197,
            'width': 50,
            'height': 50
        })
        
        edges.append({
            'id': self._generate_edge_id(),
            'source': task_before_id,
            'target': xor_split_id,
            'name': ''
        })
        
        # Ветки
        branch_yes_label = self.rng.choice(BRANCH_LABELS[self.language]['yes'])
        branch_no_label = self.rng.choice(BRANCH_LABELS[self.language]['no'])
        
        # Верхняя ветка (Yes)
        prev_id = xor_split_id
        x_offset = 450
        y_top = 100
        
        for i in range(tasks_per_branch):
            task_id = self._generate_node_id()
            nodes.append({
                'id': task_id,
                'type': 'Task',
                'name': self._generate_task_name(),
                'x': x_offset,
                'y': y_top - 18,
                'width': 100,
                'height': 80
            })
            
            edge_name = branch_yes_label if i == 0 else ''
            edges.append({
                'id': self._generate_edge_id(),
                'source': prev_id,
                'target': task_id,
                'name': edge_name
            })
            
            prev_id = task_id
            x_offset += 150
        
        last_yes_task = prev_id
        
        # Нижняя ветка (No)
        prev_id = xor_split_id
        x_offset = 450
        y_bottom = 300
        
        for i in range(tasks_per_branch):
            task_id = self._generate_node_id()
            nodes.append({
                'id': task_id,
                'type': 'Task',
                'name': self._generate_task_name(),
                'x': x_offset,
                'y': y_bottom - 18,
                'width': 100,
                'height': 80
            })
            
            edge_name = branch_no_label if i == 0 else ''
            edges.append({
                'id': self._generate_edge_id(),
                'source': prev_id,
                'target': task_id,
                'name': edge_name
            })
            
            prev_id = task_id
            x_offset += 150
        
        last_no_task = prev_id
        
        # XOR Join Gateway
        xor_join_id = self._generate_node_id()
        join_x = x_offset
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
            'source': last_yes_task,
            'target': xor_join_id,
            'name': ''
        })
        
        edges.append({
            'id': self._generate_edge_id(),
            'source': last_no_task,
            'target': xor_join_id,
            'name': ''
        })
        
        # Task after join
        task_after_id = self._generate_node_id()
        nodes.append({
            'id': task_after_id,
            'type': 'Task',
            'name': self._generate_task_name(),
            'x': join_x + 100,
            'y': 182,
            'width': 100,
            'height': 80
        })
        
        edges.append({
            'id': self._generate_edge_id(),
            'source': xor_join_id,
            'target': task_after_id,
            'name': ''
        })
        
        # End Event
        end_id = self._generate_node_id()
        nodes.append({
            'id': end_id,
            'type': 'EndEvent',
            'name': 'End' if self.language == 'en' else 'Конец',
            'x': join_x + 250,
            'y': 200,
            'width': 36,
            'height': 36
        })
        
        edges.append({
            'id': self._generate_edge_id(),
            'source': task_after_id,
            'target': end_id,
            'name': ''
        })
        
        return {
            'pattern': 'xor_branch',
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'tasks_per_branch': tasks_per_branch,
                'condition': condition,
                'language': self.language
            }
        }
    
    def generate_parallel(self, num_branches: int = 2) -> Dict[str, Any]:
        """
        Генерация параллельного паттерна:
        Start → AND split → (Task A || Task B) → AND join → End.
        
        Args:
            num_branches: Количество параллельных веток
            
        Returns:
            Словарь с узлами и связями
        """
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
        
        # AND Split Gateway
        and_split_id = self._generate_node_id()
        nodes.append({
            'id': and_split_id,
            'type': 'ParallelGateway',
            'name': '',
            'x': 200,
            'y': 197,
            'width': 50,
            'height': 50
        })
        
        edges.append({
            'id': self._generate_edge_id(),
            'source': start_id,
            'target': and_split_id,
            'name': ''
        })
        
        # Параллельные ветки
        branch_tasks = []
        y_start = 100
        y_step = 150
        
        for i in range(num_branches):
            task_id = self._generate_node_id()
            y_pos = y_start + (i * y_step)
            
            nodes.append({
                'id': task_id,
                'type': 'Task',
                'name': self._generate_task_name(),
                'x': 350,
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
        
        # AND Join Gateway
        and_join_id = self._generate_node_id()
        nodes.append({
            'id': and_join_id,
            'type': 'ParallelGateway',
            'name': '',
            'x': 500,
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
        
        # End Event
        end_id = self._generate_node_id()
        nodes.append({
            'id': end_id,
            'type': 'EndEvent',
            'name': 'End' if self.language == 'en' else 'Конец',
            'x': 600,
            'y': 200,
            'width': 36,
            'height': 36
        })
        
        edges.append({
            'id': self._generate_edge_id(),
            'source': and_join_id,
            'target': end_id,
            'name': ''
        })
        
        return {
            'pattern': 'parallel',
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'num_branches': num_branches,
                'language': self.language
            }
        }
    
    def generate_loop(self) -> Dict[str, Any]:
        """
        Генерация цикла:
        Start → Task → XOR split (repeat? yes/no) → End или возврат к Task.
        
        Returns:
            Словарь с узлами и связями
        """
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
        
        # Task
        task_id = self._generate_node_id()
        nodes.append({
            'id': task_id,
            'type': 'Task',
            'name': self._generate_task_name(),
            'x': 200,
            'y': 182,
            'width': 100,
            'height': 80
        })
        
        edges.append({
            'id': self._generate_edge_id(),
            'source': start_id,
            'target': task_id,
            'name': ''
        })
        
        # XOR Gateway (loop check)
        xor_id = self._generate_node_id()
        condition = self._generate_condition()
        nodes.append({
            'id': xor_id,
            'type': 'ExclusiveGateway',
            'name': condition,
            'x': 350,
            'y': 197,
            'width': 50,
            'height': 50
        })
        
        edges.append({
            'id': self._generate_edge_id(),
            'source': task_id,
            'target': xor_id,
            'name': ''
        })
        
        # Loop back edge
        repeat_label = self.rng.choice(LOOP_LABELS[self.language]['repeat'])
        edges.append({
            'id': self._generate_edge_id(),
            'source': xor_id,
            'target': task_id,
            'name': repeat_label
        })
        
        # End Event
        end_id = self._generate_node_id()
        exit_label = self.rng.choice(LOOP_LABELS[self.language]['exit'])
        nodes.append({
            'id': end_id,
            'type': 'EndEvent',
            'name': 'End' if self.language == 'en' else 'Конец',
            'x': 450,
            'y': 200,
            'width': 36,
            'height': 36
        })
        
        edges.append({
            'id': self._generate_edge_id(),
            'source': xor_id,
            'target': end_id,
            'name': exit_label
        })
        
        return {
            'pattern': 'loop',
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'condition': condition,
                'language': self.language
            }
        }