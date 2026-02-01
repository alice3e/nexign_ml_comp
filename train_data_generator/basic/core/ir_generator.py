"""
Модуль для генерации IR (Intermediate Representation) JSON.
IR содержит граф: узлы, связи, типы, координаты.
"""

import json
from typing import Dict, Any


class IRGenerator:
    """Генератор IR JSON из графовой структуры."""
    
    def generate_ir(self, graph: Dict[str, Any]) -> str:
        """
        Генерация IR JSON из графа.
        
        Args:
            graph: Словарь с описанием графа
            
        Returns:
            JSON строка с IR
        """
        ir = {
            "version": "1.0",
            "pattern": graph.get('pattern', 'unknown'),
            "metadata": graph.get('metadata', {}),
            "graph": {
                "nodes": self._convert_nodes(graph['nodes']),
                "edges": self._convert_edges(graph['edges'])
            }
        }
        
        return json.dumps(ir, ensure_ascii=False, indent=2)
    
    def _convert_nodes(self, nodes: list) -> list:
        """Конвертация узлов в IR формат."""
        ir_nodes = []
        
        for node in nodes:
            ir_node = {
                "id": node['id'],
                "type": node['type'],
                "name": node.get('name', ''),
                "coordinates": {
                    "x": node['x'],
                    "y": node['y'],
                    "width": node['width'],
                    "height": node['height']
                }
            }
            ir_nodes.append(ir_node)
        
        return ir_nodes
    
    def _convert_edges(self, edges: list) -> list:
        """Конвертация связей в IR формат."""
        ir_edges = []
        
        for edge in edges:
            ir_edge = {
                "id": edge['id'],
                "source": edge['source'],
                "target": edge['target'],
                "label": edge.get('name', '')
            }
            ir_edges.append(ir_edge)
        
        return ir_edges