"""
    Модуль низкоуровневого HTTP-клиента для Ollama API.

    Предоставляет класс OllamaClient для асинхронного взаимодействия
    с локальным или удаленным сервисом Ollama через REST API.
"""

import httpx
from typing import Any, Dict

# Локальные импорты
from app.logger import logger
from app.config import settings
from app.rag_service.exceptions import OllamaConnectionError, LLMError




class OllamaClient:
    """
        Низкоуровневый асинхронный HTTP-клиент для работы с Ollama API.
    """

    def __init__(self) -> None:
        """
            Инициализирует параметры подключения к Ollama и создаёт HTTP-клиент.
        """
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.api_url = f"{self.base_url}/api/generate"
        self._client = httpx.AsyncClient(timeout=60)


    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
            Отправляет текстовый промпт в Ollama и возвращает сгенерированный текст.

            :param system_prompt: Системная инструкция с ролью и правилами для модели.
            :param user_prompt: Пользовательский промпт, содержащий контекст и вопрос.
            :return: Очищенная текстовая строка сгенерированного ответа.
            :raises OllamaConnectionError: При отсутствии сетевого доступа к Ollama.
            :raises LLMError: При HTTP-ошибках или сбоях генерации на стороне Ollama.
        """

        payload: Dict[str, Any] = {
            "model": self.model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,  # Пока работаем без стриминга для простоты
            "options": {
                "temperature": self.temperature,
                "top_p": 0.9,
                "num_predict": settings.LLM_MAX_TOKENS,
            }
        }

        try:
            logger.debug(f"Отправка запроса в Ollama (модель: {self.model})")

            response = await self._client.post(self.api_url, json=payload)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "").strip()

        except httpx.ConnectError as e:
            logger.error(f"Сбой сети при обращении к Ollama API: {e}")
            raise OllamaConnectionError(f"Ollama недоступна по адресу {self.base_url}") from e

        except httpx.HTTPError as e:
            logger.error(f"Ошибка API при генерации ответа: {e}")
            raise LLMError(f"Внутренняя ошибка LLM: {e}") from e


    async def aclose(self) -> None:
        """
            Закрывает асинхронный HTTP-клиент и освобождает ресурсы соединения.
        """
        await self._client.aclose()
