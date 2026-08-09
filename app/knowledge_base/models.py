from typing import Dict, Any
from pydantic import BaseModel, Field


class RawFAQItem(BaseModel):
    """
    Модель сырой записи FAQ, загружаемой из JSON-файла парсера.
    1-в-1 повторяет структуру faq_data.json
    """
    id: int = Field(..., description="Уникальный ID вопроса из системы FAQ")
    section_id: int = Field(..., description="ID раздела")
    section_name: str = Field(..., description="Название раздела (например, 'Подписки и аккаунт')")
    url: str = Field(..., description="Прямая ссылка на страницу вопроса")
    question: str = Field(..., description="Заголовок/текст вопроса")
    answer: str = Field(..., description="Полный текст ответа")


class ChunkMetadata(BaseModel):
    """
    Метаданные чанка для сохранения в ChromaDB.
    ChromaDB строго ограничена примитивными типами (str, int, float, bool).
    """
    faq_id: int
    section_id: int
    section_name: str
    url: str
    question: str

    def to_chroma_dict(self) -> Dict[str, Any]:
        """Конвертирует модель в обычный словарь для ChromaDB."""
        return self.model_dump()


class TextChunk(BaseModel):
    """
    Модель подготовленного фрагмента текста для векторизации и сохранения в VectorStore.
    """
    id: str = Field(..., description="Уникальный строковый ID в ChromaDB (например, 'faq_50' или 'faq_50_chunk_0')")
    text: str = Field(..., description="Форматированный текст, который уходит в Embedding-модель")
    metadata: ChunkMetadata = Field(..., description="Метаданные для фильтрации в векторной БД")