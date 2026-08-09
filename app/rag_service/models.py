from typing import Dict, Any, Optional
from pydantic import BaseModel, Field




class RetrievedChunk(BaseModel):
    """Один фрагмент, найденный ретривером (результат поиска).
    Не путать с TextChunk из app.knowledge_base — тот описывает то, что хранится в Chroma."""
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: Optional[float] = None  # Метрика релевантности (distance) из ChromaDB
