import httpx

from app.logger import logger
from app.config import settings
from app.rag_service.exceptions import OllamaConnectionError, LLMError




class OllamaClient:
    """Низкоуровневый асинхронный HTTP-клиент для работы с Ollama API."""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.api_url = f"{self.base_url}/api/generate"

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Отправляет запрос в Ollama и возвращает сгенерированный текст."""

        payload = {
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

            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(self.api_url, json=payload)
                response.raise_for_status()

            result = response.json()
            return result.get("response", "").strip()

        except httpx.ConnectError as e:
            logger.error(f"Сбой сети при обращении к Ollama API: {e}")
            raise OllamaConnectionError(f"Ollama недоступна по адресу {self.base_url}") from e

        except httpx.HTTPError as e:
            logger.error(f"Ошибка API при генерации ответа: {e}")
            raise LLMError(f"Внутренняя ошибка LLM: {e}") from e