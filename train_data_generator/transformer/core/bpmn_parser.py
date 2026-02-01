"""
Модуль для парсинга BPMN XML и извлечения координат элементов.
"""

from lxml import etree
from typing import Dict, Any, List


class BPMNParser:
    """Парсер BPMN XML для извлечения структуры и координат."""
    
    # BPMN namespaces
    NAMESPACES = {
        'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
        'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
        'dc': 'http://www.omg.org/spec/DD/20100524/DC',
        'di': 'http://www.omg.org/spec/DD/20100524/DI'
    }
    
    def parse(self, bpmn_xml: str) -> Dict[str, Any]:
        """
        Парсинг BPMN XML и создание IR структуры.
        
        Args:
            bpmn_xml: BPMN XML строка
            
        Returns:
            IR JSON структура с узлами и связями
        """
        root = etree.fromstring(bpmn_xml.encode('utf-8'))
        
        # Извлечь элементы процесса
        nodes = self._extract_nodes(root)
        edges = self._extract_edges(root)
        
        # Извлечь координаты из BPMNDiagram
        self._extract_coordinates(root, nodes)
        
        return {
            'graph': {
                'nodes': nodes,
                'edges': edges
            }
        }
    
    def _extract_nodes(self, root: etree._Element) -> List[Dict[str, Any]]:
        """Извлечение узлов из BPMN."""
        nodes = []
        
        # Найти все процессы
        for process in root.findall('.//bpmn:process', self.NAMESPACES):
            # Start Events
            for elem in process.findall('.//bpmn:startEvent', self.NAMESPACES):
                nodes.append({
                    'id': elem.get('id'),
                    'type': 'StartEvent',
                    'name': elem.get('name', ''),
                    'coordinates': {'x': 0, 'y': 0, 'width': 36, 'height': 36}
                })
            
            # End Events
            for elem in process.findall('.//bpmn:endEvent', self.NAMESPACES):
                nodes.append({
                    'id': elem.get('id'),
                    'type': 'EndEvent',
                    'name': elem.get('name', ''),
                    'coordinates': {'x': 0, 'y': 0, 'width': 36, 'height': 36}
                })
            
            # Tasks
            for task_type in ['task', 'userTask', 'serviceTask', 'manualTask', 'scriptTask']:
                for elem in process.findall(f'.//bpmn:{task_type}', self.NAMESPACES):
                    nodes.append({
                        'id': elem.get('id'),
                        'type': 'Task',
                        'name': elem.get('name', ''),
                        'coordinates': {'x': 0, 'y': 0, 'width': 100, 'height': 80}
                    })
            
            # Exclusive Gateways
            for elem in process.findall('.//bpmn:exclusiveGateway', self.NAMESPACES):
                nodes.append({
                    'id': elem.get('id'),
                    'type': 'ExclusiveGateway',
                    'name': elem.get('name', ''),
                    'coordinates': {'x': 0, 'y': 0, 'width': 50, 'height': 50}
                })
            
            # Parallel Gateways
            for elem in process.findall('.//bpmn:parallelGateway', self.NAMESPACES):
                nodes.append({
                    'id': elem.get('id'),
                    'type': 'ParallelGateway',
                    'name': elem.get('name', ''),
                    'coordinates': {'x': 0, 'y': 0, 'width': 50, 'height': 50}
                })
        
        return nodes
    
    def _extract_edges(self, root: etree._Element) -> List[Dict[str, Any]]:
        """Извлечение связей из BPMN."""
        edges = []
        
        for process in root.findall('.//bpmn:process', self.NAMESPACES):
            for flow in process.findall('.//bpmn:sequenceFlow', self.NAMESPACES):
                edges.append({
                    'id': flow.get('id'),
                    'source': flow.get('sourceRef'),
                    'target': flow.get('targetRef'),
                    'label': flow.get('name', '')
                })
        
        return edges
    
    def _extract_coordinates(self, root: etree._Element, nodes: List[Dict[str, Any]]):
        """Извлечение координат из BPMNDiagram."""
        # Создать словарь узлов по ID для быстрого доступа
        nodes_dict = {node['id']: node for node in nodes}
        
        # Найти BPMNDiagram
        for diagram in root.findall('.//bpmndi:BPMNDiagram', self.NAMESPACES):
            for plane in diagram.findall('.//bpmndi:BPMNPlane', self.NAMESPACES):
                # Извлечь координаты для каждого элемента
                for shape in plane.findall('.//bpmndi:BPMNShape', self.NAMESPACES):
                    elem_id = shape.get('bpmnElement')
                    if elem_id in nodes_dict:
                        bounds = shape.find('.//dc:Bounds', self.NAMESPACES)
                        if bounds is not None:
                            nodes_dict[elem_id]['coordinates'] = {
                                'x': float(bounds.get('x', 0)),
                                'y': float(bounds.get('y', 0)),
                                'width': float(bounds.get('width', 100)),
                                'height': float(bounds.get('height', 80))
                            }