"""
Модуль для генерации BPMN 2.0 XML из графовой структуры.
"""

from lxml import etree
from typing import Dict, List, Any


class BPMNGenerator:
    """Генератор BPMN 2.0 XML документов."""
    
    BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
    BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
    DC_NS = "http://www.omg.org/spec/DD/20100524/DC"
    DI_NS = "http://www.omg.org/spec/DD/20100524/DI"
    
    NSMAP = {
        None: BPMN_NS,
        'bpmndi': BPMNDI_NS,
        'dc': DC_NS,
        'di': DI_NS
    }
    
    def __init__(self):
        """Инициализация генератора."""
        self.element_counter = 0
    
    def _generate_id(self, prefix: str = "element") -> str:
        """Генерация уникального ID для элемента."""
        self.element_counter += 1
        return f"{prefix}_{self.element_counter}"
    
    def generate_bpmn(self, graph: Dict[str, Any]) -> str:
        """
        Генерация BPMN XML из графовой структуры.
        
        Args:
            graph: Словарь с описанием графа (nodes, edges, metadata)
            
        Returns:
            Строка с BPMN XML
        """
        # Создание корневого элемента
        definitions = etree.Element(
            f"{{{self.BPMN_NS}}}definitions",
            nsmap=self.NSMAP,
            id="definitions_1",
            targetNamespace="http://bpmn.io/schema/bpmn"
        )
        
        # Создание процесса
        process = etree.SubElement(
            definitions,
            f"{{{self.BPMN_NS}}}process",
            id="process_1",
            isExecutable="false"
        )
        
        # Добавление элементов процесса
        node_id_map = {}
        for node in graph['nodes']:
            element_id = self._add_node_to_process(process, node)
            node_id_map[node['id']] = element_id
        
        # Добавление sequence flows
        flow_id_map = {}
        for edge in graph['edges']:
            flow_id = self._add_sequence_flow(process, edge, node_id_map)
            flow_id_map[edge['id']] = flow_id
        
        # Создание диаграммы (DI)
        diagram = etree.SubElement(
            definitions,
            f"{{{self.BPMNDI_NS}}}BPMNDiagram",
            id="diagram_1"
        )
        
        plane = etree.SubElement(
            diagram,
            f"{{{self.BPMNDI_NS}}}BPMNPlane",
            id="plane_1",
            bpmnElement="process_1"
        )
        
        # Добавление визуальной информации для узлов
        for node in graph['nodes']:
            self._add_node_shape(plane, node, node_id_map)
        
        # Добавление визуальной информации для связей
        for edge in graph['edges']:
            self._add_edge_shape(plane, edge, node_id_map, flow_id_map, graph['nodes'])
        
        # Преобразование в строку
        return etree.tostring(
            definitions,
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8'
        ).decode('utf-8')
    
    def _add_node_to_process(self, process: etree.Element, node: Dict[str, Any]) -> str:
        """Добавление узла в процесс."""
        node_type = node['type']
        node_id = self._generate_id(node_type.lower())
        
        if node_type == 'StartEvent':
            element = etree.SubElement(
                process,
                f"{{{self.BPMN_NS}}}startEvent",
                id=node_id,
                name=node.get('name', '')
            )
        
        elif node_type == 'EndEvent':
            element = etree.SubElement(
                process,
                f"{{{self.BPMN_NS}}}endEvent",
                id=node_id,
                name=node.get('name', '')
            )
        
        elif node_type == 'Task':
            element = etree.SubElement(
                process,
                f"{{{self.BPMN_NS}}}task",
                id=node_id,
                name=node.get('name', '')
            )
        
        elif node_type == 'ExclusiveGateway':
            element = etree.SubElement(
                process,
                f"{{{self.BPMN_NS}}}exclusiveGateway",
                id=node_id,
                name=node.get('name', '')
            )
        
        elif node_type == 'ParallelGateway':
            element = etree.SubElement(
                process,
                f"{{{self.BPMN_NS}}}parallelGateway",
                id=node_id,
                name=node.get('name', '')
            )
        
        else:
            raise ValueError(f"Unknown node type: {node_type}")
        
        return node_id
    
    def _add_sequence_flow(
        self,
        process: etree.Element,
        edge: Dict[str, Any],
        node_id_map: Dict[str, str]
    ) -> str:
        """Добавление sequence flow."""
        flow_id = self._generate_id("flow")
        source_id = node_id_map[edge['source']]
        target_id = node_id_map[edge['target']]
        
        flow = etree.SubElement(
            process,
            f"{{{self.BPMN_NS}}}sequenceFlow",
            id=flow_id,
            sourceRef=source_id,
            targetRef=target_id
        )
        
        if edge.get('name'):
            flow.set('name', edge['name'])
        
        return flow_id
    
    def _add_node_shape(
        self,
        plane: etree.Element,
        node: Dict[str, Any],
        node_id_map: Dict[str, str]
    ):
        """Добавление визуальной информации для узла."""
        element_id = node_id_map[node['id']]
        shape_id = f"{element_id}_di"
        
        shape = etree.SubElement(
            plane,
            f"{{{self.BPMNDI_NS}}}BPMNShape",
            id=shape_id,
            bpmnElement=element_id
        )
        
        bounds = etree.SubElement(
            shape,
            f"{{{self.DC_NS}}}Bounds",
            x=str(node['x']),
            y=str(node['y']),
            width=str(node['width']),
            height=str(node['height'])
        )
    
    def _add_edge_shape(
        self,
        plane: etree.Element,
        edge: Dict[str, Any],
        node_id_map: Dict[str, str],
        flow_id_map: Dict[str, str],
        nodes: List[Dict[str, Any]]
    ):
        """Добавление визуальной информации для связи."""
        source_id = node_id_map[edge['source']]
        target_id = node_id_map[edge['target']]
        flow_id = flow_id_map[edge['id']]
        
        # Создать edge без waypoints
        # bpmn-js автоматически рассчитает правильные waypoints
        # которые будут доходить до краев фигур, а не до центра
        edge_element = etree.SubElement(
            plane,
            f"{{{self.BPMNDI_NS}}}BPMNEdge",
            id=f"{flow_id}_di",
            bpmnElement=flow_id
        )