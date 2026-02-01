"""
Модуль для работы с Eliza API.
Поддерживает различные ML модели через единый интерфейс.
"""

import json
import os
import certifi
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import requests
from .logger import get_logger


class BaseMLModel(ABC):
    """Базовый класс для работы с ML моделями через Eliza API."""

    def __init__(self, token: Optional[str] = None):
        """
        Инициализация модели.

        Args:
            token: OAuth токен для Eliza API (если None, берется из переменной окружения)
        """
        self.logger = get_logger()
        self.token = token or os.getenv("ELIZA_TOKEN")
        if not self.token:
            self.logger.error("ELIZA_TOKEN не установлен в переменных окружения")
            raise ValueError("ELIZA_TOKEN не установлен в переменных окружения")

        # Настройка сертификата для Yandex Internal CA
        self.ca_bundle = self._setup_ca_bundle()
        self.logger.debug(f"Модель {self.__class__.__name__} инициализирована")

    def _setup_ca_bundle(self) -> str:
        """
        Настраивает CA bundle с добавлением Yandex Internal Root CA.

        Returns:
            Путь к CA bundle файлу
        """
        # Получаем путь к стандартному CA bundle
        ca_bundle_path = certifi.where()

        # Путь к Yandex сертификату
        yandex_cert_path = os.path.join(
            os.path.dirname(__file__), "YandexInternalRootCA.pem"
        )

        # Проверяем наличие Yandex сертификата
        if os.path.exists(yandex_cert_path):
            # Читаем содержимое стандартного CA bundle
            with open(ca_bundle_path, "r") as f:
                ca_content = f.read()

            # Читаем Yandex сертификат
            with open(yandex_cert_path, "r") as f:
                yandex_cert = f.read()

            # Проверяем, добавлен ли уже Yandex сертификат
            if "YandexInternalRootCA" not in ca_content:
                # Создаем временный файл с объединенными сертификатами
                temp_ca_path = os.path.join(
                    os.path.dirname(__file__), "combined_ca_bundle.pem"
                )

                with open(temp_ca_path, "w") as f:
                    f.write(ca_content)
                    f.write("\n# Yandex Internal Root CA\n")
                    f.write(yandex_cert)

                return temp_ca_path

        return ca_bundle_path

    @abstractmethod
    def get_endpoint(self) -> str:
        """Возвращает endpoint для модели."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Возвращает имя модели для запроса."""
        pass

    def get_headers(self) -> Dict[str, str]:
        """Возвращает заголовки для запроса."""
        return {
            "Authorization": f"OAuth {self.token}",
            "Content-Type": "application/json",
        }

    def send_request(
        self, message: str, temperature: float = 0.7, max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Отправляет запрос в модель.

        Args:
            message: Текст сообщения для модели
            temperature: Температура генерации (0.0-1.0)
            max_tokens: Максимальное количество токенов в ответе

        Returns:
            Ответ от модели в формате словаря

        Raises:
            requests.exceptions.RequestException: При ошибке запроса
        """
        self.logger.debug(f"Отправка запроса в модель {self.get_model_name()}")
        self.logger.debug(
            f"Параметры: temperature={temperature}, max_tokens={max_tokens}, message_length={len(message)}"
        )

        start_time = time.time()

        payload = {
            "model": self.get_model_name(),
            "messages": [{"role": "user", "content": message}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            response = requests.post(
                self.get_endpoint(),
                headers=self.get_headers(),
                json=payload,
                verify=self.ca_bundle,  # Используем CA bundle с Yandex сертификатом
                timeout=300,  # 5 минут таймаут
            )

            duration = time.time() - start_time

            response.raise_for_status()
            result = response.json()

            self.logger.info(
                f"Ответ получен от модели {self.get_model_name()} за {duration:.2f} сек"
            )
            self.logger.debug(f"HTTP статус: {response.status_code}")

            return result

        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.logger.error(
                f"Ошибка запроса к модели {self.get_model_name()} после {duration:.2f} сек: {e}"
            )
            raise

    def extract_response_text(self, response: Dict[str, Any]) -> str:
        """
        Извлекает текст ответа из response.

        Args:
            response: Ответ от API

        Returns:
            Текст ответа модели
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


class AliceAI235B(BaseMLModel):
    """Модель Alice AI 235B."""

    def get_endpoint(self) -> str:
        return "https://api.eliza.yandex.net/internal/zeliboba_lts_235b_aligned_quantized_202510/generative/v1/chat/completions"

    def get_model_name(self) -> str:
        return "alice-ai-235b"


class DeepSeekV31Terminus(BaseMLModel):
    """Модель DeepSeek V3.1-Terminus."""

    def get_endpoint(self) -> str:
        return "https://api.eliza.yandex.net/internal/deepseek-v3-1-terminus/v1/chat/completions"

    def get_model_name(self) -> str:
        return "default"


class MLClient:
    """Клиент для работы с ML моделями через Eliza API."""

    # Доступные модели
    AVAILABLE_MODELS = {
        "alice-ai-235b": AliceAI235B,
        "deepseek-v3.1-terminus": DeepSeekV31Terminus,
    }

    def __init__(
        self, model_name: str = "deepseek-v3.1-terminus", token: Optional[str] = None
    ):
        """
        Инициализация клиента.

        Args:
            model_name: Имя модели для использования
            token: OAuth токен для Eliza API

        Raises:
            ValueError: Если модель не поддерживается
        """
        if model_name not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Модель '{model_name}' не поддерживается. "
                f"Доступные модели: {', '.join(self.AVAILABLE_MODELS.keys())}"
            )

        self.logger = get_logger()
        self.model_name = model_name
        self.model = self.AVAILABLE_MODELS[model_name](token)
        self.logger.info(f"MLClient инициализирован с моделью: {model_name}")

    def compose_message(
        self,
        ticket_file: str,
        context_dir: str = "context_data",
        system_prompt_file: str = "system_prompt.md",
    ) -> str:
        """
        Создает композицию сообщения из контекста, тикета и системного промпта.

        Порядок:
        1. Все файлы из context_dir (кроме system_prompt.md)
        2. Содержимое тикета (JSON)
        3. system_prompt.md

        Args:
            ticket_file: Путь к JSON файлу с очищенным тикетом
            context_dir: Директория с контекстными файлами
            system_prompt_file: Имя файла с системным промптом

        Returns:
            Скомпонованное сообщение в формате markdown
        """
        self.logger.debug(f"Создание композиции сообщения для тикета из {ticket_file}")
        message_parts = []

        # 1. Добавляем контекстные файлы (кроме system_prompt)
        if os.path.exists(context_dir):
            context_files = sorted(
                [
                    f
                    for f in os.listdir(context_dir)
                    if f.endswith((".md", ".txt")) and f != system_prompt_file
                ]
            )

            for filename in context_files:
                filepath = os.path.join(context_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    message_parts.append(f"# Контекст: {filename}\n\n{content}\n")

        # 2. Добавляем содержимое тикета
        with open(ticket_file, "r", encoding="utf-8") as f:
            ticket_data = json.load(f)
            ticket_json = json.dumps(ticket_data, ensure_ascii=False, indent=2)
            message_parts.append(f"# Данные тикета\n\n```json\n{ticket_json}\n```\n")

        # 3. Добавляем системный промпт
        system_prompt_path = os.path.join(context_dir, system_prompt_file)
        if os.path.exists(system_prompt_path):
            with open(system_prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()
                message_parts.append(f"# Задание\n\n{system_prompt}\n")

        composed_message = "\n---\n\n".join(message_parts)
        self.logger.debug(f"Композиция создана: {len(composed_message)} символов")

        return composed_message

    def process_ticket(
        self,
        ticket_file: str,
        context_dir: str = "context_data",
        output_file: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """
        Обрабатывает тикет: создает композицию, отправляет в модель, сохраняет результат.

        Args:
            ticket_file: Путь к JSON файлу с очищенным тикетом
            context_dir: Директория с контекстными файлами
            output_file: Путь для сохранения ответа (если None, создается автоматически)
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов

        Returns:
            Словарь с результатами обработки:
            {
                'ticket_key': ключ тикета,
                'model': имя модели,
                'response_text': текст ответа,
                'full_response': полный ответ API,
                'output_file': путь к файлу с ответом
            }
        """
        # Получаем ключ тикета из имени файла
        ticket_key = (
            os.path.basename(ticket_file)
            .replace("_clean.json", "")
            .replace(".json", "")
        )

        self.logger.info(f"Обработка тикета {ticket_key} с моделью {self.model_name}")

        # Создаем композицию сообщения
        self.logger.debug("Создание композиции сообщения")
        message = self.compose_message(ticket_file, context_dir)

        # Сохраняем композицию для отладки
        composition_file = ticket_file.replace(
            "_clean.json", "_composition.md"
        ).replace(".json", "_composition.md")
        with open(composition_file, "w", encoding="utf-8") as f:
            f.write(message)
        self.logger.debug(f"Композиция сохранена в {composition_file}")

        # Отправляем запрос в модель
        self.logger.info(f"Отправка запроса в модель {self.model_name}")
        start_time = time.time()
        response = self.model.send_request(message, temperature, max_tokens)
        duration = time.time() - start_time

        # Извлекаем текст ответа
        response_text = self.model.extract_response_text(response)
        self.logger.info(
            f"Получен ответ от модели: {len(response_text)} символов за {duration:.2f} сек"
        )

        # Определяем путь для сохранения ответа
        if output_file is None:
            output_file = ticket_file.replace("_clean.json", "_response.json").replace(
                ".json", "_response.json"
            )

        # Сохраняем результат
        result = {
            "ticket_key": ticket_key,
            "model": self.model_name,
            "response_text": response_text,
            "full_response": response,
            "timestamp": None,  # Будет добавлено при сохранении
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        self.logger.info(f"Результат сохранен в {output_file}")

        result["output_file"] = output_file
        return result

    def process_directory(
        self,
        input_dir: str,
        context_dir: str = "context_data",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> List[Dict[str, Any]]:
        """
        Обрабатывает все очищенные тикеты в директории.

        Args:
            input_dir: Директория с очищенными JSON файлами тикетов
            context_dir: Директория с контекстными файлами
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов

        Returns:
            Список результатов обработки
        """
        results = []

        # Находим все очищенные файлы тикетов
        ticket_files = [
            os.path.join(input_dir, f)
            for f in os.listdir(input_dir)
            if f.endswith("_clean.json")
        ]

        if not ticket_files:
            self.logger.warning(f"Не найдено очищенных файлов тикетов в {input_dir}")
            return results

        self.logger.info(f"Найдено {len(ticket_files)} файлов для обработки")

        for ticket_file in ticket_files:
            try:
                result = self.process_ticket(
                    ticket_file,
                    context_dir,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                results.append(result)
            except Exception as e:
                self.logger.error(
                    f"Ошибка при обработке {ticket_file}: {e}", exc_info=True
                )
                continue

        return results


def main():
    """Пример использования модуля."""
    # Проверяем наличие токена
    if not os.getenv("ELIZA_TOKEN"):
        print("ОШИБКА: ELIZA_TOKEN не установлен в переменных окружения")
        print("Установите: export ELIZA_TOKEN=your_token")
        return

    # Создаем клиент с моделью DeepSeek
    print("Инициализация ML клиента...")
    client = MLClient(model_name="deepseek-v3.1-terminus")

    # Обрабатываем все тикеты в директории
    results = client.process_directory("temp_data", "context_data")

    print(f"\n{'=' * 60}")
    print(f"Обработано тикетов: {len(results)}")
    print(f"{'=' * 60}")

    for result in results:
        print(f"\nТикет: {result['ticket_key']}")
        print(f"Модель: {result['model']}")
        print(f"Ответ ({len(result['response_text'])} символов):")
        print(f"{result['response_text'][:200]}...")
        print(f"Файл с результатом: {result['output_file']}")


if __name__ == "__main__":
    main()
