import chromadb
from typing import List

from app.logger import logger
from app.config import settings
from app.rag_service.exceptions import ChromaConnectionError
from app.rag_service.models import RetrievedChunk
from app.knowledge_base.embeddings import EmbeddingService




class Retriever:
    """Поиск релевантных чанков в общей базе ChromaDB, построенной app.knowledge_base."""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self._init_chroma()

    def _init_chroma(self) -> None:
        """Подключение к директории ChromaDB из knowledge_base."""

        try:
            # Читаем существующие файлы БД
            logger.info(f"Подключение к ChromaDB по пути: {settings.CHROMA_PERSIST_DIR}")
            self.client = chromadb.PersistentClient(path=str(settings.CHROMA_PERSIST_DIR))
            self.collection = self.client.get_collection(name=settings.CHROMA_COLLECTION_NAME)
            logger.info(f"Коллекция загружена. Документов: {self.collection.count()}")

        except Exception as e:
            logger.error(f"Не удалось подключиться к ChromaDB: {e}", exc_info=True)
            raise ChromaConnectionError(f"Ошибка загрузки базы знаний: {e}") from e

    def search(self, query: str, top_k: int = 3) -> List[RetrievedChunk]:
        """Ищет документы, используя эмбеддинг из knowledge_base."""

        logger.info(f"Поиск в БД для запроса: '{query[:60]}...'")

        # 1. Векторизуем запрос
        query_vector = self.embedding_service.embed_query(query)

        # 2. Ищем в Chroma
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        if not documents: return []

        return [
            RetrievedChunk(
                text=doc,
                metadata=metadatas[idx] if metadatas else {},
                score=distances[idx] if distances else None
            )
            for idx, doc in enumerate(documents)
        ]