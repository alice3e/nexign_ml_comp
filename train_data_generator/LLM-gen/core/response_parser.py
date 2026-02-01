"""
Парсер ответов от LLM для извлечения BPMN XML и текстового описания.
"""

import re
import logging
from typing import Tuple, Optional
from xml.etree import ElementTree as ET


class ResponseParser:
    """Парсер для извлечения BPMN XML и описания из ответа модели."""
    
    def __init__(self):
        """Инициализация парсера."""
        self.logger = logging.getLogger(__name__)
    
    def parse_response(self, response_text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Парсит ответ модели и извлекает BPMN XML и текстовое описание.
        
        Args:
            response_text: Текст ответа от модели
        
        Returns:
            Кортеж (bpmn_xml, description_md)
            Возвращает (None, None) если не удалось распарсить
        """
        self.logger.debug("Начало парсинга ответа модели")
        
        # Извлечение BPMN XML
        bpmn_xml = self._extract_xml(response_text)
        if not bpmn_xml:
            self.logger.warning("Не удалось извлечь BPMN XML из ответа")
        else:
            self.logger.info(f"BPMN XML извлечен, длина: {len(bpmn_xml)} символов")
        
        # Извлечение текстового описания
        description_md = self._extract_markdown(response_text)
        if not description_md:
            self.logger.warning("Не удалось извлечь текстовое описание из ответа")
        else:
            self.logger.info(f"Описание извлечено, длина: {len(description_md)} символов")
        
        return bpmn_xml, description_md
    
    def _extract_xml(self, text: str) -> Optional[str]:
        """
        Извлекает BPMN XML из текста.
        
        Args:
            text: Текст для поиска XML
        
        Returns:
            BPMN XML или None если не найден
        """
        # Паттерны для поиска XML блоков
        patterns = [
            r'```xml\s*(.*?)\s*```',  # Markdown код блок с xml
            r'```\s*(<?xml.*?</definitions>)\s*```',  # Markdown код блок без языка
            r'(<?xml.*?</definitions>)',  # Прямой XML без блока
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                xml_content = match.group(1).strip()
                
                # Проверка валидности XML
                if self._validate_xml(xml_content):
                    return xml_content
        
        return None
    
    def _extract_markdown(self, text: str) -> Optional[str]:
        """
        Извлекает текстовое описание в формате Markdown.
        
        Args:
            text: Текст для поиска описания
        
        Returns:
            Markdown описание или None если не найдено
        """
        # Паттерны для поиска Markdown блоков
        patterns = [
            r'```markdown\s*(.*?)\s*```',  # Markdown код блок
            r'```md\s*(.*?)\s*```',  # Markdown код блок (короткий)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                md_content = match.group(1).strip()
                return md_content
        
        # Если не найден блок markdown, попробуем найти описание после XML
        # Ищем текст после закрывающего тега </definitions>
        xml_end_pattern = r'</definitions>\s*```?\s*(.*)'
        match = re.search(xml_end_pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            remaining_text = match.group(1).strip()
            
            # Убираем возможные markdown блоки в начале
            remaining_text = re.sub(r'^```\w*\s*', '', remaining_text)
            remaining_text = re.sub(r'\s*```\s*$', '', remaining_text)
            
            # Проверяем, что это похоже на описание (начинается с # или содержит заголовки)
            if remaining_text and (remaining_text.startswith('#') or '##' in remaining_text):
                return remaining_text.strip()
        
        return None
    
    def _validate_xml(self, xml_content: str) -> bool:
        """
        Проверяет валидность XML.
        
        Args:
            xml_content: XML контент для проверки
        
        Returns:
            True если XML валиден, False иначе
        """
        try:
            ET.fromstring(xml_content)
            return True
        except ET.ParseError as e:
            self.logger.debug(f"XML не валиден: {e}")
            return False
    
    def validate_bpmn(self, xml_content: str) -> bool:
        """
        Проверяет, что XML является валидным BPMN 2.0.
        
        Args:
            xml_content: BPMN XML для проверки
        
        Returns:
            True если BPMN валиден, False иначе
        """
        try:
            root = ET.fromstring(xml_content)
            
            # Проверка namespace
            if 'http://www.omg.org/spec/BPMN/20100524/MODEL' not in root.tag:
                self.logger.warning("BPMN XML не содержит правильный namespace")
                return False
            
            # Проверка наличия обязательных элементов
            namespaces = {
                'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
                'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI'
            }
            
            # Проверка наличия process
            processes = root.findall('.//bpmn:process', namespaces)
            if not processes:
                # Попробуем без namespace prefix
                processes = root.findall('.//process')
            
            if not processes:
                self.logger.warning("BPMN XML не содержит элемент process")
                return False
            
            self.logger.info("BPMN XML прошел базовую валидацию")
            return True
        
        except ET.ParseError as e:
            self.logger.error(f"Ошибка парсинга BPMN XML: {e}")
            return False
    
    def fix_common_xml_issues(self, xml_content: str) -> str:
        """
        Исправляет распространенные проблемы в XML.
        
        Args:
            xml_content: XML контент для исправления
        
        Returns:
            Исправленный XML контент
        """
        # Убираем лишние пробелы и переносы строк
        xml_content = xml_content.strip()
        
        # Убираем возможные HTML entities
        xml_content = xml_content.replace('&nbsp;', ' ')
        xml_content = xml_content.replace('&lt;', '<')
        xml_content = xml_content.replace('&gt;', '>')
        xml_content = xml_content.replace('&amp;', '&')
        xml_content = xml_content.replace('&quot;', '"')
        
        # Проверяем наличие XML декларации
        if not xml_content.startswith('<?xml'):
            xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_content
        
        return xml_content