"""
    Модуль Pydantic-моделей данных для базы знаний.

    Описывает структуры для сырых записей FAQ, метаданных чанков (совместимых с ChromaDB)
    и финальных текстовых фрагментов (чанков), отправляемых на векторизацию.
"""

from typing import Any, Dict
from pydantic import BaseModel, Field




class RawFAQItem(BaseModel):
    """
        Сырая запись FAQ, загружаемая из исходного JSON-датасета.
        Точно соответствует структуре элементов в `faq_data.json`.
    """

    id: int = Field(..., description="Уникальный ID вопроса из системы FAQ")
    section_id: int = Field(..., description="ID раздела")
    section_name: str = Field(..., description="Название раздела (например, 'Подписки и аккаунт')")
    url: str = Field(..., description="Прямая ссылка на страницу вопроса")
    question: str = Field(..., description="Заголовок/текст вопроса")
    answer: str = Field(..., description="Полный текст ответа")



class ChunkMetadata(BaseModel):
    """
        Метаданные текстового чанка для сохранения в ChromaDB.

        Все поля ограничены примитивными типами данных (str, int, float, bool),
        что соответствует требованиям к метаданным в ChromaDB.
    """

    faq_id: int
    section_id: int
    section_name: str
    url: str
    question: str


    def to_chroma_dict(self) -> Dict[str, Any]:
        """
            Конвертирует модель метаданных в словарь, совместимый с ChromaDB.
            :return: Словарь примитивных значений метаданных.
        """
        return self.model_dump()



class TextChunk(BaseModel):
    """
        Подготовленный текстовый фрагмент (чанк) для векторизации и сохранения.
        Объединяет строковый идентификатор, форматированный текст для модели эмбеддингов
        и метаданные для последующего поиска и фильтрации.
    """

    id: str = Field(..., description="Уникальный строковый ID в ChromaDB (например, 'faq_50' или 'faq_50_chunk_0')")
    text: str = Field(..., description="Форматированный текст, который уходит в Embedding-модель")
    metadata: ChunkMetadata = Field(..., description="Метаданные для фильтрации в векторной БД")
