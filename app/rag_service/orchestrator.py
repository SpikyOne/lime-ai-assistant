"""
    Модуль оркестрации RAG-пайплайна.

    Предоставляет класс RAGPipeline, объединяющий компоненты валидации запроса,
    векторного поиска контекста в базе знаний, сборки промпта и асинхронной
    генерации ответа языковой моделью.
"""

import asyncio
from typing import List, Tuple

# Локальные импорты
from app.exceptions import AppError
from app.logger import logger
from app.rag_service.retriever import Retriever
from app.rag_service.guardrails import Guardrails
from app.rag_service.context_builder import ContextBuilder
from app.rag_service.llm.service import LLMService




class RAGPipeline:
    """
        Оркестратор полного цикла RAG: вопрос -> валидация -> векторный поиск -> контекст -> ответ LLM.
    """

    def __init__(self) -> None:
        """
            Инициализирует основные сервисы и компоненты RAG-пайплайна.

            Важен порядок:
                1. Retriever → E5 + Chroma
                2. LLMService → клиент Ollama

            После создания объекта можно выполнить warmup LLM.
        """
        self.retriever = Retriever()
        self.guardrails = Guardrails()
        self.context_builder = ContextBuilder()
        self.llm_service = LLMService()


    async def warmup(self) -> None:
        """
            Прогревает LLM после полной инициализации RAG-пайплайна.
        """
        logger.info("Запуск warmup RAGPipeline: embeddings + Chroma уже готовы.")
        await self.llm_service.warmup()
        logger.info("Warmup RAGPipeline успешно завершён.")


    async def answer(self, question: str) -> Tuple[str, List[str]]:
        """
            Обрабатывает пользовательский вопрос и формирует итоговый ответ с источниками.

            :param question: Текст вопроса пользователя.
            :return: Кортеж из (текст_ответа, список_ссылок_на_источники).
        """
        question = self.guardrails.validate_user_query(question)

        try: chunks = await asyncio.to_thread(self.retriever.search, question)

        except AppError as e:
            logger.error(f"Ошибка на этапе поиска в базе знаний: {e}", exc_info=True)
            return (
                "К сожалению, сейчас не удаётся получить доступ к базе знаний. "
                "Попробуйте задать вопрос немного позже.",
                [],
            )

        chunks = self.guardrails.filter_retrieved_chunks(chunks)

        context = self.context_builder.build(chunks)
        answer_text = await self.llm_service.generate_rag_answer(context, question)

        # Извлечение и дедупликация уникальных URL-источников
        raw_sources = [chunk.metadata.get("url") for chunk in chunks if chunk.metadata.get("url")]
        sources = list(dict.fromkeys(raw_sources))

        return answer_text, sources


    async def aclose(self) -> None:
        """
            Освобождает сетевые и системные ресурсы пайплайна (включая HTTP-клиент Ollama).
        """
        await self.llm_service.client.aclose()
