from typing import List

from app.config import settings
from app.logger import logger
from app.rag_service.models import RetrievedChunk
from app.rag_service.exceptions import InvalidQueryError




class Guardrails:
    """Класс для фильтрации и валидации данных в пайплайне."""

    @staticmethod
    def validate_user_query(query: str) -> str:
        """Очищает и проверяет вопрос пользователя перед поиском."""
        query = query.strip()
        if not query: raise InvalidQueryError("Вопрос не может быть пустым.")

        # Обрезаем слишком длинные запросы (защита от перегрузки / спама)
        if len(query) > settings.MAX_MESSAGE_LENGTH:
            logger.warning(f"Запрос обрезан, так как превышает {settings.MAX_MESSAGE_LENGTH} символов.")
            query = query[:settings.MAX_MESSAGE_LENGTH]

        return query


    @staticmethod
    def filter_retrieved_chunks(chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        """Удаляет мусор или нерелевантные фрагменты, возвращенные базой."""

        filtered = []
        for chunk in chunks:
            # Убираем пустые чанки
            if not chunk.text.strip(): continue
            filtered.append(chunk)

        if not filtered: logger.warning("Guardrails отклонил все найденные чанки (остался пустой контекст).")

        return filtered