"""
    Модуль низкоуровневого HTTP-клиента для Ollama API.

    Предоставляет класс OllamaClient для асинхронного взаимодействия
    с локальным или удаленным сервисом Ollama через REST API.
"""

import asyncio
import httpx
from typing import Any, Dict

# Локальные импорты
from app.logger import logger
from app.config import settings
from app.rag_service.exceptions import OllamaConnectionError, LLMError




class OllamaClient:
    """
        Низкоуровневый асинхронный HTTP-клиент для работы с Ollama API.

        Класс отвечает за:
        - отправку запросов на генерацию;
        - прогрев модели;
        - единые параметры inference;
        - удержание модели в памяти;
        - ограничение одновременных генераций;
        - корректное освобождение HTTP-ресурсов.
    """

    def __init__(self) -> None:
        """
            Инициализирует параметры подключения к Ollama и создаёт HTTP-клиент.
        """
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.api_url = f"{self.base_url}/api/generate"

        timeout = httpx.Timeout(
            connect=10.0,
            read=float(settings.LLM_READ_TIMEOUT),
            write=30.0,
            pool=30.0,
        )

        self._client = httpx.AsyncClient(timeout=timeout)

        # На машине с ограниченным количеством RAM одновременно
        # выполняем только один inference.
        #
        # Это дополнительная защита поверх OLLAMA_NUM_PARALLEL=1.
        self._generation_lock = asyncio.Lock()


    async def _request(
            self,
            system_prompt: str,
            user_prompt: str,
            num_predict: int,
    ) -> str:
        """
            Выполняет единичный запрос к Ollama.

            :param system_prompt: Системная инструкция.
            :param user_prompt: Пользовательский запрос.
            :param num_predict: Максимальное число генерируемых токенов.
            :return: Текст ответа модели.
        """

        payload: Dict[str, Any] = {
            "model": self.model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,                                        # Пока работаем без стриминга для простоты
            "keep_alive": -1,                                       # Не даём Ollama выгружать модель после запроса.
            "options": {
                "temperature": self.temperature,
                "top_p": 0.9,
                "num_ctx": settings.LLM_CONTEXT_TOKENS,             # ВАЖНО: это значение должно оставаться одинаковым и для warmup, и для обычной генерации.
                "num_predict": num_predict,
            },
        }

        async with self._generation_lock:
            try:
                logger.debug(
                    "Отправка запроса в Ollama "
                    f"(модель: {self.model}, "
                    f"ctx: {settings.LLM_CONTEXT_TOKENS}, "
                    f"predict: {num_predict})"
                )

                response = await self._client.post(self.api_url, json=payload,)
                response.raise_for_status()

                result = response.json()
                text = result.get("response", "").strip()

                if not text: logger.warning("Ollama вернула пустой ответ.")

                return text

            except httpx.ConnectError as e:
                logger.error(f"Сбой сети при обращении к Ollama API: {type(e).__name__}: {e}", exc_info=True)
                raise OllamaConnectionError(f"Ollama недоступна по адресу {self.base_url}") from e

            except httpx.HTTPStatusError as e:
                logger.error(f"Ollama вернула HTTP-ошибку: {e.response.status_code} {e.response.text}", exc_info=True)
                raise LLMError(f"Ollama вернула HTTP {e.response.status_code}") from e

            except httpx.TimeoutException as e:
                logger.error("Превышено время ожидания ответа Ollama.", exc_info=True)
                raise LLMError("Превышено время ожидания ответа языковой модели.") from e

            except httpx.HTTPError as e:
                logger.error(f"Ошибка API при генерации ответа: {type(e).__name__}: {e}", exc_info=True)
                raise LLMError(f"Ошибка HTTP при обращении к Ollama: {e}") from e

            except ValueError as e:
                logger.error(f"Ollama вернула некорректный JSON: {e}", exc_info=True)
                raise LLMError("Ollama вернула некорректный ответ.") from e

            except Exception as e:
                logger.error(f"Непредвиденная ошибка OllamaClient: {e}",exc_info=True)
                raise LLMError(f"Ошибка генерации ответа: {e}") from e


    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
            Отправляет текстовый промпт в Ollama и возвращает сгенерированный текст.

            :param system_prompt: Системная инструкция с ролью и правилами для модели.
            :param user_prompt: Пользовательский промпт, содержащий контекст и вопрос.
            :return: Очищенная текстовая строка сгенерированного ответа.
        """
        return await self._request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            num_predict=settings.LLM_MAX_TOKENS,
        )


    async def warmup(self) -> None:
        """
            Выполняет прогрев модели после загрузки API.

            Для warmup используется:
                - тот же context window, что и в обычной генерации;
                - минимальная генерация в 1 токен;
                - keep_alive=-1.

            Это позволяет:
                1. реально проверить inference;
                2. загрузить Qwen в память;
                3. не тратить лишнее время на длинный ответ;
                4. не вызвать повторную загрузку модели из-за отличающегося num_ctx.
        """
        logger.info(f"Начинаю прогрев модели '{self.model}'...")
        await self._request(system_prompt="Ты тестовый ассистент.", user_prompt="Ответь одним словом: OK", num_predict=1)
        logger.info(f"Модель '{self.model}' успешно прогрета.")


    async def aclose(self) -> None:
        """
            Корректно закрывает асинхронный HTTP-клиент Ollama и освобождает ресурсы соединения.
        """
        await self._client.aclose()
