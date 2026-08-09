from typing import List

from app.rag_service.models import RetrievedChunk




class ContextBuilder:
    """Формирует итоговый текстовый контекст для LLM из фрагментов."""

    def __init__(self, max_chars: int = 4000):
        # Ограничиваем размер контекста, чтобы не вылезти за лимит токенов модели
        self.max_chars = max_chars


    def build(self, chunks: List[RetrievedChunk]) -> str:
        """Склеивает список чанков в единый текст с разделителями."""
        if not chunks: return ""

        context_parts = []
        current_length = 0

        for idx, chunk in enumerate(chunks, 1):
            # Форматируем чанк
            part = f"[Документ {idx}]\n{chunk.text.strip()}\n\n"

            # Проверяем лимит символов
            if current_length + len(part) > self.max_chars:
                break

            context_parts.append(part)
            current_length += len(part)

        return "".join(context_parts).strip()