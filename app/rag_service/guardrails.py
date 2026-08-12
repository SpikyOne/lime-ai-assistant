"""
    Модуль валидации и фильтрации данных (Guardrails) RAG-сервиса.

    Предоставляет класс Guardrails для первичной очистки и проверки пользовательских
    запросов, а также отсеивания нерелевантной или некорректной информации из чанков.
"""

from typing import List

from app.config import settings
from app.logger import logger
from app.rag_service.models import RetrievedChunk
from app.rag_service.exceptions import InvalidQueryError




class Guardrails:
    """
        Класс для фильтрации и валидации данных в RAG-пайплайне.
    """

    @staticmethod
    def validate_user_query(query: str) -> str:
        """
            Очищает и проверяет поисковый запрос пользователя.

            :param query: Исходный текстовый запрос пользователя.
            :return: Очищенная и усеченная (при превышении лимита) строка запроса.
            :raises InvalidQueryError: Если запрос пустой или состоит только из пробелов.
        """
        query = query.strip()
        if not query: raise InvalidQueryError("Вопрос не может быть пустым.")

        # Ограничение максимальной длины запроса для защиты от перегрузки
        if len(query) > settings.MAX_MESSAGE_LENGTH:
            logger.warning(f"Запрос обрезан, так как превышает {settings.MAX_MESSAGE_LENGTH} символов.")
            query = query[:settings.MAX_MESSAGE_LENGTH]

        return query


    @staticmethod
    def filter_retrieved_chunks(chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        """
            Фильтрует список чанков, полученных из векторного хранилища.

            Исключает пустые фрагменты текста и фиксирует предупреждение,
            если все найденные элементы были отклонены.

            :param chunks: Список чанков, извлеченных из базы знаний.
            :return: Список отфильтрованных релевантных чанков.
        """
        filtered: List[RetrievedChunk] = []
        for chunk in chunks:
            # Убираем пустые чанки
            if not chunk.text.strip(): continue
            filtered.append(chunk)

        if not filtered: logger.warning("Guardrails отклонил все найденные чанки (остался пустой контекст).")

        return filtered
