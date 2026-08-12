"""
    Модуль очистки, контекстного обогащения и нарезки (chunking) данных FAQ.

    Предоставляет класс TextProcessor для удаления HTML-тегов, нормализации
    пробельных символов, контекстного обогащения структурированным заглавием
    и разбиения длинных ответов на сбалансированные чанки.
"""

import re
from typing import List

# Локальные импорты
from app.config import settings
from app.logger import logger
from app.knowledge_base.exceptions import ProcessorError
from app.knowledge_base.models import ChunkMetadata, RawFAQItem, TextChunk




class TextProcessor:
    """
        Модуль очистки, контекстного обогащения и нарезки (chunking) данных FAQ.

        Выполняет предобработку текста перед векторизацией: удаление HTML-разметки,
        нормализацию символов и пробелов, добавление префиксов раздела и вопроса,
        а также скользящую нарезку длинных текстов на перекрывающиеся фрагменты.
    """

    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP,
    ) -> None:
        """
            Инициализирует процессор параметров нарезки текста.

            :param chunk_size: Максимальный размер одного текстового чанка в символах.
            :param chunk_overlap: Размер перекрытия между соседними чанками в символах.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap


    @staticmethod
    def clean_text(text: str) -> str:
        """
            Удаляет HTML-теги, нормализует спецсимволы и пробельные знаки.

            :param text: Исходная текстовая строка.
            :return: Очищенная текстовая строка.
        """
        if not text: return ""

        # 1. Удаление HTML тегов
        cleaned = re.sub(r"<[^>]+>", " ", text)

        # 2. Замена неразрывных пробелов и спецсимволов
        cleaned = cleaned.replace("\xa0", " ").replace("&nbsp;", " ")

        # 3. Нормализация повторяющихся пробелов и дублирующихся переносов строк
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned)

        return cleaned.strip()


    def _build_context_text(
        self, section_name: str, question: str, answer: str
    ) -> str:
        """
            Формирует контекстно-обогащенный текстовый блок для модели эмбеддингов.

            :param section_name: Название раздела FAQ.
            :param question: Текст вопроса.
            :param answer: Текст ответа (или его фрагмент).
            :return: Объединенный текстовый блок с метками структуры.
        """
        return (
            f"Раздел: {section_name}\n"
            f"Вопрос: {question}\n"
            f"Ответ: {answer}"
        )


    def _split_text(self, text: str) -> List[str]:
        """
            Разбивает длинный текст на перекрывающиеся фрагменты с учетом границ предложений.

            :param text: Исходный текст для разделения.
            :return: Список фрагментов текста, не превышающих chunk_size.
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks: List[str] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size

            # Поиск естественной границы предложения или абзаца
            if end < text_len:
                split_point = max(
                    text.rfind("\n", start, end),
                    text.rfind(". ", start, end),
                    text.rfind("? ", start, end),
                    text.rfind("! ", start, end),
                )
                if split_point > start: end = split_point + 1

            chunk_str = text[start:end].strip()
            if chunk_str: chunks.append(chunk_str)

            start = end - self.chunk_overlap if end < text_len else text_len

        return chunks


    def process_item(self, item: RawFAQItem) -> List[TextChunk]:
        """
            Преобразует один объект RawFAQItem в один или несколько объектов TextChunk.

            :param item: Исходный объект записи FAQ.
            :return: Список сформированных текстовых чанков с метаданными.
        """
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

        # Создаем единый атомарный чанк, если текст укладывается в установленный лимит
        if len(full_context_text) <= self.chunk_size:
            return [
                TextChunk(
                    id=f"faq_{item.section_id}_{item.id}",
                    text=full_context_text,
                    metadata=base_metadata,
                )
            ]

        # Делим длинный текст ответа на фрагменты
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
        """
            Выполняет пакетную обработку и нарезку всех сырых элементов FAQ.

            :param raw_items: Список сырых записей RawFAQItem.
            :return: Полный список готовых для векторизации объектов TextChunk.
            :raises ProcessorError: Если в процессе обработки возникла непредвиденная ошибка.
        """
        logger.info(f"Начало обработки и нарезки {len(raw_items)} элементов...")
        all_chunks: List[TextChunk] = []

        try:
            for item in raw_items:
                item_chunks = self.process_item(item)
                all_chunks.extend(item_chunks)

            logger.info(f"Обработка завершена. Из {len(raw_items)} записей сформировано {len(all_chunks)} чанков.")
            return all_chunks

        except Exception as e:
            logger.error(f"Ошибка при обработке текстов: {e}", exc_info=True)
            raise ProcessorError(f"Ошибка предобработки данных: {e}") from e
