"""
    Модуль моделей данных для RAG-сервиса.

    Содержит структуры данных для представления результатов векторного поиска
    и найденных текстовых фрагментов (чанков), передаваемых в генератор контекста.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field




class RetrievedChunk(BaseModel):
    """
        Модель текстового фрагмента, извлеченного из векторного хранилища.

        Представляет один результат поиска ретривера с ассоциированными
        метаданными и оценкой релевантности (косинусным расстоянием).
        Не путать с TextChunk из app.knowledge_base — тот описывает то, что хранится в Chroma.
    """

    text: str = Field(..., description="Текст извлеченного текстового фрагмента")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Словарь метаданных чанка (faq_id, section_name, url и др.)",
    )
    score: Optional[float] = Field(                                 # Метрика релевантности (distance) из ChromaDB
        default=None,
        description="Метрика релевантности или косинусного расстояния из ChromaDB",
    )
