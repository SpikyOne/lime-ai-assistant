import asyncio
from typing import List, Tuple

from app.exceptions import AppError
from app.logger import logger
from app.rag_service.retriever import Retriever
from app.rag_service.guardrails import Guardrails
from app.rag_service.context_builder import ContextBuilder
from app.rag_service.llm.service import LLMService




class RAGPipeline:
    """Оркестратор полного цикла: вопрос ---> поиск ---> контекст ---> ответ LLM."""

    def __init__(self):
        self.retriever = Retriever()
        self.guardrails = Guardrails()
        self.context_builder = ContextBuilder()
        self.llm_service = LLMService()

    async def answer(self, question: str) -> Tuple[str, List[str]]:
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

        sources = [c.metadata.get("url") for c in chunks if c.metadata.get("url")]
        return answer_text, sources


    async def aclose(self) -> None:
        """Освобождает ресурсы пайплайна (HTTP-клиент Ollama) — вызывать при остановке приложения."""
        await self.llm_service.client.aclose()