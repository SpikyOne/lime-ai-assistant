from app.logger import logger
from app.rag_service.exceptions import LLMError
from app.rag_service.llm.client import OllamaClient
from app.rag_service.llm.prompts import SYSTEM_PROMPT, RAG_USER_TEMPLATE




class LLMService:
    """Высокоуровневый сервис для работы с LLM в рамках RAG."""

    def __init__(self):
        self.client = OllamaClient()

    async def generate_rag_answer(self, context: str, question: str) -> str:
        """ Собирает итоговый промпт из контекста и вопроса, и отправляет его в LLM для получения ответа. """

        # Если контекст пустой (например, guardrails обрезал все документы)
        if not context.strip():
            logger.warning("Передан пустой контекст. LLM не вызывается.")
            return "К сожалению, в базе знаний нет подходящей информации для ответа на ваш вопрос."

        # Формируем итоговый промпт пользователя
        user_prompt = RAG_USER_TEMPLATE.format(context=context, question=question)
        logger.info(f"Генерация ответа для вопроса: '{question[:50]}...'")

        try: return await self.client.generate(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
        except LLMError: return "Извините, сервис генерации ответов временно недоступен."
