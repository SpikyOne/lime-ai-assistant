"""
    Модуль высокоуровневого сервиса генерации ответов LLM.

    Предоставляет класс LLMService для форматирования контекста, подстановки
    данных в шаблоны промптов и асинхронного получения ответа от языковой модели.
"""

# Локальные импорты
from app.logger import logger
from app.rag_service.exceptions import LLMError
from app.rag_service.llm.client import OllamaClient
from app.rag_service.llm.prompts import SYSTEM_PROMPT, RAG_USER_TEMPLATE




class LLMService:
    """
        Высокоуровневый сервис для генерации ответов языковой моделью в RAG-пайплайне.
    """

    def __init__(self) -> None:
        """
            Инициализирует клиент взаимодействия с LLM-провайдером.
        """
        self.client = OllamaClient()

    async def generate_rag_answer(self, context: str, question: str) -> str:
        """
            Собирает итоговый промпт из контекста и вопроса, затем генерирует ответ через LLM.

            :param context: Сформированный контекст из релевантных фрагментов базы знаний.
            :param question: Очищенный поисковый запрос пользователя.
            :return: Сгенерированный текст ответа или сообщение об отсутствии информации / ошибке.
        """
        # Если контекст пустой (например, guardrails отфильтровал все документы)
        if not context.strip():
            logger.warning("Передан пустой контекст. LLM не вызывается.")
            return "К сожалению, в базе знаний нет подходящей информации для ответа на ваш вопрос."

        # Формирование итогового пользовательского промпта
        user_prompt = RAG_USER_TEMPLATE.format(context=context, question=question)
        logger.info(f"Генерация ответа для вопроса: '{question[:50]}...'")

        try: return await self.client.generate(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
        except LLMError: return "Извините, сервис генерации ответов временно недоступен."
