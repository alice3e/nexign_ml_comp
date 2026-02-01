"""
Клиент для работы с Eliza API.
"""

import os
import time
import logging
from typing import Dict, Any, Optional
import requests


class ElizaClient:
    """Клиент для работы с Eliza API для генерации BPMN диаграмм."""
    
    # Доступные модели
    MODELS = {
        "alice-ai-235b": {
            "endpoint": "https://api.eliza.yandex.net/internal/zeliboba_lts_235b_aligned_quantized_202510/generative/v1/chat/completions",
            "model_name": "alice-ai-235b"
        },
        "deepseek-v3.1-terminus": {
            "endpoint": "https://api.eliza.yandex.net/internal/deepseek-v3-1-terminus/v1/chat/completions",
            "model_name": "default"
        }
    }
    
    def __init__(
        self,
        model: str = "deepseek-v3.1-terminus",
        token: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        timeout: int = 300
    ):
        """
        Инициализация клиента.
        
        Args:
            model: Имя модели для использования
            token: OAuth токен для Eliza API (если None, берется из переменной окружения)
            temperature: Температура генерации (0.0-1.0)
            max_tokens: Максимальное количество токенов в ответе
            timeout: Таймаут запроса в секундах
        """
        self.logger = logging.getLogger(__name__)
        
        if model not in self.MODELS:
            raise ValueError(
                f"Модель '{model}' не поддерживается. "
                f"Доступные модели: {', '.join(self.MODELS.keys())}"
            )
        
        self.model = model
        self.model_config = self.MODELS[model]
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        
        # Получение токена
        self.token = token or os.getenv("ELIZA_TOKEN")
        if not self.token:
            raise ValueError(
                "ELIZA_TOKEN не установлен. "
                "Установите переменную окружения: export ELIZA_TOKEN=your_token"
            )
        
        self.logger.info(f"ElizaClient инициализирован с моделью: {model}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Возвращает заголовки для запроса."""
        return {
            "Authorization": f"OAuth {self.token}",
            "Content-Type": "application/json",
        }
    
    def send_request(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Отправляет запрос в модель.
        
        Args:
            user_message: Пользовательское сообщение (промпт)
            system_message: Системное сообщение (опционально)
            temperature: Температура генерации (если None, используется значение по умолчанию)
            max_tokens: Максимальное количество токенов (если None, используется значение по умолчанию)
        
        Returns:
            Ответ от модели в формате словаря
        
        Raises:
            requests.exceptions.RequestException: При ошибке запроса
        """
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        self.logger.info(f"Отправка запроса в модель {self.model}")
        self.logger.debug(
            f"Параметры: temperature={temp}, max_tokens={tokens}, "
            f"message_length={len(user_message)}"
        )
        
        # Формирование сообщений
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": user_message})
        
        payload = {
            "model": self.model_config["model_name"],
            "messages": messages,
            "temperature": temp,
            "max_tokens": tokens,
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(
                self.model_config["endpoint"],
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout,
                verify=False  # Отключаем проверку SSL для внутренних сертификатов
            )
            
            duration = time.time() - start_time
            
            response.raise_for_status()
            result = response.json()
            
            self.logger.info(
                f"Ответ получен от модели {self.model} за {duration:.2f} сек"
            )
            self.logger.debug(f"HTTP статус: {response.status_code}")
            
            return result
        
        except requests.exceptions.Timeout:
            duration = time.time() - start_time
            self.logger.error(
                f"Таймаут запроса к модели {self.model} после {duration:.2f} сек"
            )
            raise
        
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.logger.error(
                f"Ошибка запроса к модели {self.model} после {duration:.2f} сек: {e}"
            )
            raise
    
    def extract_response_text(self, response: Dict[str, Any]) -> str:
        """
        Извлекает текст ответа из response.
        
        Args:
            response: Ответ от API
        
        Returns:
            Текст ответа модели
        
        Raises:
            ValueError: Если не удалось извлечь текст из ответа
        """
        try:
            # Для raw ответа
            if "choices" in response:
                return response["choices"][0]["message"]["content"]
            # Для обернутого ответа
            elif "response" in response and "choices" in response["response"]:
                return response["response"]["choices"][0]["message"]["content"]
            else:
                raise ValueError(f"Неожиданный формат ответа: {response}")
        except (KeyError, IndexError) as e:
            raise ValueError(f"Не удалось извлечь текст из ответа: {e}")
    
    def generate_bpmn(
        self,
        prompt: str,
        system_prompt: str
    ) -> str:
        """
        Генерирует BPMN диаграмму на основе промпта.
        
        Args:
            prompt: Описание процесса для генерации
            system_prompt: Системный промпт с инструкциями
        
        Returns:
            Текст ответа модели (содержит XML и описание)
        """
        # Объединяем системный промпт и пользовательский промпт
        full_message = f"{system_prompt}\n\n{prompt}"
        
        # Отправляем запрос
        response = self.send_request(full_message)
        
        # Извлекаем текст ответа
        response_text = self.extract_response_text(response)
        
        return response_text