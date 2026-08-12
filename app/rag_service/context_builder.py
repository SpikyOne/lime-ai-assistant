"""
    Модуль сборки контекста для RAG-сервиса.

    Предоставляет класс ContextBuilder для объединения релевантных текстовых
    чанков в единый структурированный контекст с учетом лимитов длины.
"""

from typing import List

# Локальные импорты
from app.rag_service.models import RetrievedChunk




class ContextBuilder:
    """
        Формирует итоговый текстовый контекст для LLM из найденных фрагментов.
    """

    def __init__(self, max_chars: int = 4000) -> None:
        """
            Инициализирует сборщик контекста с заданным лимитом символов.
            :param max_chars: Максимальная допустимая длина итогового контекста в символах.
        """
        self.max_chars = max_chars                  # Ограничиваем размер контекста, чтобы не вылезти за лимит токенов модели


    def build(self, chunks: List[RetrievedChunk]) -> str:
        """
            Склеивает список чанков в единый структурированный текст с разделителями.

            :param chunks: Список объектов RetrievedChunk, полученных из векторной БД.
            :return: Отформатированная строка контекста для подстановки в промпт LLM.
        """
        if not chunks: return ""

        context_parts: List[str] = []
        current_length = 0

        for idx, chunk in enumerate(chunks, 1):
            # Форматируем чанк
            part = f"[Документ {idx}]\n{chunk.text.strip()}\n\n"

            # Проверяем лимит символов перед добавлением
            if current_length + len(part) > self.max_chars:
                break

            context_parts.append(part)
            current_length += len(part)

        return "".join(context_parts).strip()
