"""
Модуль для генерации текстовых описаний BPMN диаграмм.
Поддерживает два формата: Steps (шаги) и Pseudocode (псевдокод).
"""

from typing import Dict, List, Any, Set
from data.dictionaries import STEPS_TEMPLATES, PSEUDOCODE_TEMPLATES


class TextGenerator:
    """Генератор текстовых описаний BPMN диаграмм."""
    
    def __init__(self, language: str = 'ru'):
        """
        Инициализация генератора текста.
        
        Args:
            language: Язык генерации ('ru' или 'en')
        """
        self.language = language
    
    def generate_steps(self, graph: Dict[str, Any]) -> str:
        """
        Генерация описания в формате "шаги".
        
        Args:
            graph: Словарь с описанием графа
            
        Returns:
            Текстовое описание в формате шагов
        """
        templates = STEPS_TEMPLATES[self.language]
        nodes = graph['nodes']
        edges = graph['edges']
        
        # Создать описание диаграммы
        description = []
        
        # Заголовок
        if self.language == 'ru':
            description.append("=== Описание BPMN диаграммы ===\n")
        else:
            description.append("=== BPMN Diagram Description ===\n")
        
        # Описание элементов
        if self.language == 'ru':
            description.append("Элементы диаграммы:")
        else:
            description.append("Diagram elements:")
        
        for node in nodes:
            node_desc = self._describe_node(node, self.language)
            description.append(f"  - {node_desc}")
        
        description.append("")
        
        # Описание связей
        if self.language == 'ru':
            description.append("Связи между элементами:")
        else:
            description.append("Connections between elements:")
        
        for edge in edges:
            edge_desc = self._describe_edge(edge, nodes, self.language)
            description.append(f"  - {edge_desc}")
        
        description.append("")
        
        # Пошаговое выполнение
        if self.language == 'ru':
            description.append("Последовательность выполнения:")
        else:
            description.append("Execution sequence:")
        
        steps = []
        step_num = 1
        
        # Найти Start Event
        start_node = next(n for n in nodes if n['type'] == 'StartEvent')
        
        # Добавить старт
        steps.append(f"{step_num}) {templates['start']}")
        step_num += 1
        
        # Обход графа - не используем visited для линейных цепочек
        step_num = self._traverse_steps_simple(
            start_node['id'], nodes, edges, templates, steps, step_num, set()
        )
        
        description.extend(steps)
        
        return '\n'.join(description)
    
    def _describe_node(self, node: Dict[str, Any], language: str) -> str:
        """Описание узла."""
        node_type = node['type']
        name = node.get('name', '')
        
        if language == 'ru':
            type_names = {
                'StartEvent': 'Событие начала',
                'EndEvent': 'Событие завершения',
                'Task': 'Задача',
                'ExclusiveGateway': 'Шлюз исключающего выбора (XOR)',
                'ParallelGateway': 'Шлюз параллельного выполнения (AND)'
            }
            type_name = type_names.get(node_type, node_type)
            if name:
                return f"{type_name}: \"{name}\""
            else:
                return type_name
        else:
            type_names = {
                'StartEvent': 'Start Event',
                'EndEvent': 'End Event',
                'Task': 'Task',
                'ExclusiveGateway': 'Exclusive Gateway (XOR)',
                'ParallelGateway': 'Parallel Gateway (AND)'
            }
            type_name = type_names.get(node_type, node_type)
            if name:
                return f"{type_name}: \"{name}\""
            else:
                return type_name
    
    def _describe_edge(self, edge: Dict[str, Any], nodes: List[Dict[str, Any]], language: str) -> str:
        """Описание связи."""
        source_node = next(n for n in nodes if n['id'] == edge['source'])
        target_node = next(n for n in nodes if n['id'] == edge['target'])
        
        source_name = source_node.get('name', source_node['type'])
        target_name = target_node.get('name', target_node['type'])
        edge_label = edge.get('name', '')
        
        if language == 'ru':
            if edge_label:
                return f"От \"{source_name}\" к \"{target_name}\" (условие: \"{edge_label}\")"
            else:
                return f"От \"{source_name}\" к \"{target_name}\""
        else:
            if edge_label:
                return f"From \"{source_name}\" to \"{target_name}\" (condition: \"{edge_label}\")"
            else:
                return f"From \"{source_name}\" to \"{target_name}\""
    
    def _traverse_steps_simple(
        self,
        current_id: str,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        templates: Dict[str, str],
        steps: List[str],
        step_num: int,
        visited: Set[str]
    ) -> int:
        """Упрощенный обход графа для генерации шагов."""
        # Защита от бесконечных циклов
        if current_id in visited:
            return step_num
        
        visited.add(current_id)
        
        # Найти текущий узел
        current_node = next((n for n in nodes if n['id'] == current_id), None)
        if not current_node:
            return step_num
        
        # Найти исходящие связи
        outgoing = [e for e in edges if e['source'] == current_id]
        
        # Обработка узла
        if current_node['type'] == 'StartEvent':
            # Старт уже добавлен, просто продолжаем
            if outgoing:
                step_num = self._traverse_steps_simple(
                    outgoing[0]['target'], nodes, edges, templates, steps, step_num, visited
                )
        
        elif current_node['type'] == 'Task':
            steps.append(f"{step_num}) {templates['task'].format(name=current_node['name'])}")
            step_num += 1
            
            # Продолжить к следующему узлу
            if outgoing:
                step_num = self._traverse_steps_simple(
                    outgoing[0]['target'], nodes, edges, templates, steps, step_num, visited
                )
        
        elif current_node['type'] == 'ExclusiveGateway':
            # Проверить, это split или join
            incoming = [e for e in edges if e['target'] == current_id]
            
            if len(outgoing) > 1:  # XOR split
                condition = current_node.get('name', 'условие' if self.language == 'ru' else 'condition')
                steps.append(f"{step_num}) {templates['xor_split'].format(condition=condition)}")
                step_num += 1
                
                # Обработать ветки
                for idx, edge in enumerate(outgoing):
                    branch_label = edge.get('name', f'Ветка {idx+1}' if self.language == 'ru' else f'Branch {idx+1}')
                    indent = "  "
                    
                    # Описать ветку
                    if self.language == 'ru':
                        steps.append(f"{indent}Ветка \"{branch_label}\":")
                    else:
                        steps.append(f"{indent}Branch \"{branch_label}\":")
                    
                    # Обойти ветку с новым visited set
                    target_id = edge['target']
                    self._describe_branch_steps(
                        target_id, nodes, edges, templates, steps, indent + "  ", visited.copy()
                    )
                
                # Найти join и продолжить после него
                join_node = self._find_xor_join(outgoing, nodes, edges)
                if join_node and join_node['id'] not in visited:
                    visited.add(join_node['id'])
                    join_outgoing = [e for e in edges if e['source'] == join_node['id']]
                    if join_outgoing:
                        step_num = self._traverse_steps_simple(
                            join_outgoing[0]['target'], nodes, edges, templates, steps, step_num, visited
                        )
            
            elif len(incoming) > 1:  # XOR join
                # Join - просто продолжаем
                if outgoing:
                    step_num = self._traverse_steps_simple(
                        outgoing[0]['target'], nodes, edges, templates, steps, step_num, visited
                    )
        
        elif current_node['type'] == 'ParallelGateway':
            incoming = [e for e in edges if e['target'] == current_id]
            
            if len(outgoing) > 1:  # AND split
                steps.append(f"{step_num}) {templates['and_split']}")
                step_num += 1
                
                # Обработать параллельные ветки
                for edge in outgoing:
                    target_node = next(n for n in nodes if n['id'] == edge['target'])
                    if target_node['type'] == 'Task':
                        steps.append(f"{templates['and_branch'].format(name=target_node['name'])}")
                
                # Найти AND join и продолжить после него
                and_join = self._find_and_join(outgoing, nodes, edges)
                if and_join and and_join['id'] not in visited:
                    visited.add(and_join['id'])
                    steps.append(f"{step_num}) {templates['and_join']}")
                    step_num += 1
                    
                    and_join_outgoing = [e for e in edges if e['source'] == and_join['id']]
                    if and_join_outgoing:
                        step_num = self._traverse_steps_simple(
                            and_join_outgoing[0]['target'], nodes, edges, templates, steps, step_num, visited
                        )
            
            elif len(incoming) > 1:  # AND join
                # Join уже обработан в split
                if outgoing:
                    step_num = self._traverse_steps_simple(
                        outgoing[0]['target'], nodes, edges, templates, steps, step_num, visited
                    )
        
        elif current_node['type'] == 'EndEvent':
            steps.append(f"{step_num}) {templates['end']}")
            step_num += 1
        
        return step_num
    
    def _describe_branch_steps(
        self,
        current_id: str,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        templates: Dict[str, str],
        steps: List[str],
        indent: str,
        visited: Set[str]
    ):
        """Описание шагов в ветке."""
        if current_id in visited:
            return
        
        visited.add(current_id)
        
        current_node = next((n for n in nodes if n['id'] == current_id), None)
        if not current_node:
            return
        
        # Если это join gateway, останавливаемся
        incoming = [e for e in edges if e['target'] == current_id]
        if current_node['type'] in ['ExclusiveGateway', 'ParallelGateway'] and len(incoming) > 1:
            return
        
        # Описать текущий узел
        if current_node['type'] == 'Task':
            steps.append(f"{indent}{current_node['name']}")
        elif current_node['type'] == 'EndEvent':
            steps.append(f"{indent}{templates['end']}")
            return
        
        # Продолжить обход
        outgoing = [e for e in edges if e['source'] == current_id]
        for edge in outgoing:
            self._describe_branch_steps(
                edge['target'], nodes, edges, templates, steps, indent, visited
            )
    
    def _find_xor_join(
        self,
        split_outgoing: List[Dict[str, Any]],
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ):
        """Найти соответствующий XOR join для XOR split."""
        # Найти узлы, к которым приходят обе ветки
        targets = set()
        for edge in split_outgoing:
            reachable = self._get_reachable_nodes(edge['target'], edges, set())
            if not targets:
                targets = reachable
            else:
                targets = targets.intersection(reachable)
        
        # Найти первый ExclusiveGateway среди общих целей
        for node in nodes:
            if node['id'] in targets and node['type'] == 'ExclusiveGateway':
                incoming = [e for e in edges if e['target'] == node['id']]
                if len(incoming) > 1:
                    return node
        
        return None
    
    def _traverse_branch(
        self,
        current_id: str,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        templates: Dict[str, str],
        steps: List[str],
        step_num: int,
        visited: Set[str],
        indent: str
    ):
        """Обход ветки для детального описания."""
        if current_id in visited:
            return
        
        visited.add(current_id)
        
        current_node = next((n for n in nodes if n['id'] == current_id), None)
        if not current_node:
            return
        
        # Описать текущий узел
        if current_node['type'] == 'Task':
            steps.append(f"{indent}{current_node['name']}")
        elif current_node['type'] == 'EndEvent':
            steps.append(f"{indent}{templates['end']}")
            return
        elif current_node['type'] == 'ExclusiveGateway':
            # Это join, не описываем
            pass
        
        # Продолжить обход
        outgoing = [e for e in edges if e['source'] == current_id]
        for edge in outgoing:
            if edge['target'] not in visited:
                self._traverse_branch(
                    edge['target'], nodes, edges, templates, steps, step_num, visited, indent
                )
    
    def _find_and_join(
        self,
        split_outgoing: List[Dict[str, Any]],
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Найти соответствующий AND join для AND split."""
        # Найти узлы, к которым приходят все ветки
        targets = set()
        for edge in split_outgoing:
            # Обойти ветку и найти все достижимые узлы
            reachable = self._get_reachable_nodes(edge['target'], edges, set())
            if not targets:
                targets = reachable
            else:
                targets = targets.intersection(reachable)
        
        # Найти первый ParallelGateway среди общих целей
        for node in nodes:
            if node['id'] in targets and node['type'] == 'ParallelGateway':
                incoming = [e for e in edges if e['target'] == node['id']]
                if len(incoming) > 1:
                    return node
        
        return None
    
    def _get_reachable_nodes(self, start_id: str, edges: List[Dict[str, Any]], visited: Set[str]) -> Set[str]:
        """Получить все достижимые узлы от start_id."""
        if start_id in visited:
            return set()
        
        visited.add(start_id)
        reachable = {start_id}
        
        outgoing = [e for e in edges if e['source'] == start_id]
        for edge in outgoing:
            reachable.update(self._get_reachable_nodes(edge['target'], edges, visited))
        
        return reachable
    
    def generate_pseudocode(self, graph: Dict[str, Any]) -> str:
        """
        Генерация описания в формате "псевдокод".
        
        Args:
            graph: Словарь с описанием графа
            
        Returns:
            Текстовое описание в формате псевдокода
        """
        templates = PSEUDOCODE_TEMPLATES[self.language]
        lines = []
        indent_level = 0
        
        # Найти Start Event
        nodes = graph['nodes']
        edges = graph['edges']
        start_node = next(n for n in nodes if n['type'] == 'StartEvent')
        
        # Добавить START
        lines.append(templates['start'])
        indent_level += 1
        
        # Обход графа - используем новый метод
        self._traverse_pseudocode_simple(
            start_node['id'], nodes, edges, templates, lines, indent_level, set()
        )
        
        # Добавить END
        lines.append(templates['end'])
        
        return '\n'.join(lines)
    
    def _traverse_pseudocode_simple(
        self,
        current_id: str,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        templates: Dict[str, str],
        lines: List[str],
        indent_level: int,
        visited: Set[str]
    ):
        """Упрощенный обход графа для генерации псевдокода."""
        if current_id in visited:
            return
        
        visited.add(current_id)
        indent = "  " * indent_level
        
        # Найти текущий узел
        current_node = next((n for n in nodes if n['id'] == current_id), None)
        if not current_node:
            return
        
        # Найти исходящие связи
        outgoing = [e for e in edges if e['source'] == current_id]
        
        # Обработка узла
        if current_node['type'] == 'StartEvent':
            # Старт уже добавлен, просто продолжаем
            if outgoing:
                self._traverse_pseudocode_simple(
                    outgoing[0]['target'], nodes, edges, templates, lines, indent_level, visited
                )
        
        elif current_node['type'] == 'Task':
            lines.append(f"{indent}{templates['task'].format(name=current_node['name'])}")
            
            # Продолжить к следующему узлу
            if outgoing:
                self._traverse_pseudocode_simple(
                    outgoing[0]['target'], nodes, edges, templates, lines, indent_level, visited
                )
        
        elif current_node['type'] == 'ExclusiveGateway':
            incoming = [e for e in edges if e['target'] == current_id]
            
            if len(outgoing) > 1:  # XOR split
                condition = current_node.get('name', 'условие' if self.language == 'ru' else 'condition')
                
                # Проверить, это цикл или обычное ветвление
                is_loop = any(
                    self._is_loop_back(e['target'], current_id, edges)
                    for e in outgoing
                )
                
                if is_loop:
                    # WHILE цикл
                    lines.append(f"{indent}{templates['while'].format(condition=condition)}")
                    
                    # Найти ветку цикла (не к End)
                    for edge in outgoing:
                        target_node = next(n for n in nodes if n['id'] == edge['target'])
                        if target_node['type'] != 'EndEvent':
                            self._traverse_pseudocode_simple(
                                edge['target'], nodes, edges, templates, lines, indent_level + 1, visited.copy()
                            )
                    
                    lines.append(f"{indent}{templates['endwhile']}")
                    
                    # Продолжить после цикла
                    for edge in outgoing:
                        target_node = next(n for n in nodes if n['id'] == edge['target'])
                        if target_node['type'] == 'EndEvent':
                            self._traverse_pseudocode_simple(
                                edge['target'], nodes, edges, templates, lines, indent_level, visited
                            )
                else:
                    # IF/ELSE
                    lines.append(f"{indent}{templates['if'].format(condition=condition)}")
                    
                    # Обработать ветки с отдельными visited
                    if len(outgoing) >= 1:
                        self._traverse_pseudocode_simple(
                            outgoing[0]['target'], nodes, edges, templates, lines, indent_level + 1, visited.copy()
                        )
                    
                    if len(outgoing) >= 2:
                        lines.append(f"{indent}{templates['else']}")
                        self._traverse_pseudocode_simple(
                            outgoing[1]['target'], nodes, edges, templates, lines, indent_level + 1, visited.copy()
                        )
                    
                    lines.append(f"{indent}{templates['endif']}")
                    
                    # Найти join и продолжить после него
                    join_node = self._find_xor_join(outgoing, nodes, edges)
                    if join_node and join_node['id'] not in visited:
                        visited.add(join_node['id'])
                        join_outgoing = [e for e in edges if e['source'] == join_node['id']]
                        if join_outgoing:
                            self._traverse_pseudocode_simple(
                                join_outgoing[0]['target'], nodes, edges, templates, lines, indent_level, visited
                            )
            
            elif len(incoming) > 1:  # XOR join
                # Join - просто продолжаем
                if outgoing:
                    self._traverse_pseudocode_simple(
                        outgoing[0]['target'], nodes, edges, templates, lines, indent_level, visited
                    )
        
        elif current_node['type'] == 'ParallelGateway':
            incoming = [e for e in edges if e['target'] == current_id]
            
            if len(outgoing) > 1:  # AND split
                lines.append(f"{indent}{templates['fork']}")
                
                # Обработать параллельные ветки
                for edge in outgoing:
                    target_node = next(n for n in nodes if n['id'] == edge['target'])
                    if target_node['type'] == 'Task':
                        lines.append(f"{indent}{templates['branch'].format(name=target_node['name'])}")
                
                lines.append(f"{indent}{templates['join']}")
                
                # Найти AND join и продолжить после него
                and_join = self._find_and_join(outgoing, nodes, edges)
                if and_join and and_join['id'] not in visited:
                    visited.add(and_join['id'])
                    and_join_outgoing = [e for e in edges if e['source'] == and_join['id']]
                    if and_join_outgoing:
                        self._traverse_pseudocode_simple(
                            and_join_outgoing[0]['target'], nodes, edges, templates, lines, indent_level, visited
                        )
            
            elif len(incoming) > 1:  # AND join
                # Join уже обработан в split
                if outgoing:
                    self._traverse_pseudocode_simple(
                        outgoing[0]['target'], nodes, edges, templates, lines, indent_level, visited
                    )
        
        elif current_node['type'] == 'EndEvent':
            # END будет добавлен в конце
            pass
    
    def _is_loop_back(self, target_id: str, gateway_id: str, edges: List[Dict[str, Any]]) -> bool:
        """Проверка, является ли связь обратной (цикл)."""
        # Упрощенная проверка: если target ведет обратно к gateway
        visited = set()
        return self._can_reach(target_id, gateway_id, edges, visited)
    
    def _can_reach(self, from_id: str, to_id: str, edges: List[Dict[str, Any]], visited: Set[str]) -> bool:
        """Проверка достижимости узла."""
        if from_id == to_id:
            return True
        
        if from_id in visited:
            return False
        
        visited.add(from_id)
        
        outgoing = [e for e in edges if e['source'] == from_id]
        for edge in outgoing:
            if self._can_reach(edge['target'], to_id, edges, visited):
                return True
        
        return False