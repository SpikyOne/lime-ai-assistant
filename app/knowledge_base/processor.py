import re
from typing import List

from app.config import settings
from .exceptions import ProcessorError
from app.logger import logger
from .models import ChunkMetadata, RawFAQItem, TextChunk




class TextProcessor:
    """Модуль очистки, контекстного обогащения и нарезки данных FAQ."""

    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @staticmethod
    def clean_text(text: str) -> str:
        """Удаляет HTML-теги и нормализует пробельные символы."""
        if not text:
            return ""

        # 1. Удаление HTML тегов
        cleaned = re.sub(r"<[^>]+>", " ", text)

        # 2. Замена спецсимволов и спецпробелов
        cleaned = cleaned.replace("\xa0", " ").replace("&nbsp;", " ")

        # 3. Нормализация повторяющихся пробелов и переносов строк
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned)

        return cleaned.strip()

    def _build_context_text(self, section_name: str, question: str, answer: str) -> str:
        """Формирует обогащенный текстовый блок для векторного поиска."""
        return (
            f"Раздел: {section_name}\n"
            f"Вопрос: {question}\n"
            f"Ответ: {answer}"
        )

    def _split_text(self, text: str) -> List[str]:
        """
        Простой скользящий механизм разделения текста по абзацам/предложениям,
        если текст превышает chunk_size.
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks: List[str] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size

            # Если мы не в самом конце текста, пытаемся разбить по границе предложения или абзаца
            if end < text_len:
                split_point = max(
                    text.rfind("\n", start, end),
                    text.rfind(". ", start, end),
                    text.rfind("? ", start, end),
                    text.rfind("! ", start, end),
                )
                if split_point > start:
                    end = split_point + 1

            chunk_str = text[start:end].strip()
            if chunk_str:
                chunks.append(chunk_str)

            start = end - self.chunk_overlap if end < text_len else text_len

        return chunks

    def process_item(self, item: RawFAQItem) -> List[TextChunk]:
        """Обрабатывает один RawFAQItem и превращает его в список TextChunk."""
        cleaned_question = self.clean_text(item.question)
        cleaned_answer = self.clean_text(item.answer)
        cleaned_section = self.clean_text(item.section_name)

        if not cleaned_answer:
            logger.warning(f"FAQ ID {item.id} содержит пустой ответ после очистки. Пропуск.")
            return []

        base_metadata = ChunkMetadata(
            faq_id=item.id,
            section_id=item.section_id,
            section_name=cleaned_section,
            url=item.url,
            question=cleaned_question,
        )

        full_context_text = self._build_context_text(
            section_name=cleaned_section,
            question=cleaned_question,
            answer=cleaned_answer,
        )

        # Если умещается в лимит — создаем 1 атомарный чанк
        if len(full_context_text) <= self.chunk_size:
            return [
                TextChunk(
                    id=f"faq_{item.section_id}_{item.id}",
                    text=full_context_text,
                    metadata=base_metadata,
                )
            ]

        # Если ответ слишком длинный — делим текст ответа
        answer_chunks = self._split_text(cleaned_answer)
        result_chunks: List[TextChunk] = []

        for idx, ans_chunk in enumerate(answer_chunks):
            chunk_text = self._build_context_text(
                section_name=cleaned_section,
                question=cleaned_question,
                answer=ans_chunk,
            )
            result_chunks.append(
                TextChunk(
                    id=f"faq_{item.section_id}_{item.id}_chunk_{idx}",
                    text=chunk_text,
                    metadata=base_metadata,
                )
            )

        return result_chunks

    def process(self, raw_items: List[RawFAQItem]) -> List[TextChunk]:
        """Принимает список сырых элементов и возвращает готовые чанки."""
        logger.info(f"Начало обработки и нарезки {len(raw_items)} элементов...")
        all_chunks: List[TextChunk] = []

        try:
            for item in raw_items:
                item_chunks = self.process_item(item)
                all_chunks.extend(item_chunks)

            logger.info(
                f"Обработка завершена. Из {len(raw_items)} записей сформировано {len(all_chunks)} чанков."
            )
            return all_chunks

        except Exception as e:
            logger.error(f"Ошибка при обработке текстов: {e}", exc_info=True)
            raise ProcessorError(f"Ошибка предобработки данных: {e}") from e
