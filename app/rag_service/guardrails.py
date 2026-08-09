from typing import List

from app.logger import logger
from app.rag_service.models import RetrievedChunk




class Guardrails:
    """Класс для фильтрации и валидации данных в пайплайне."""

    @staticmethod
    def validate_user_query(query: str) -> str:
        """Очищает и проверяет вопрос пользователя перед поиском."""
        query = query.strip()
        if not query: raise ValueError("Вопрос не может быть пустым.")

        # Обрезаем слишком длинные запросы (защита от перегрузки / спама)
        max_length = 1000
        if len(query) > max_length:
            logger.warning(f"Запрос обрезан, так как превышает {max_length} символов.")
            query = query[:max_length]

        return query

    @staticmethod
    def filter_retrieved_chunks(chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        """Удаляет мусор или нерелевантные фрагменты, возвращенные базой."""

        filtered = []
        for chunk in chunks:
            # Убираем пустые чанки
            if not chunk.text.strip(): continue

            # Здесь в будущем можно добавить фильтрацию по score
            # (например, отсекать всё, у чего distance > 1.5)
            # if chunk.score and chunk.score > 1.5:
            #     continue

            filtered.append(chunk)

        if not filtered: logger.warning("Guardrails отклонил все найденные чанки (остался пустой контекст).")

        return filtered