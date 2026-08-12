"""
    Модуль векторного поиска (Retriever) в базе знаний ChromaDB.

    Предоставляет класс Retriever для векторизации пользовательских запросов
    и извлечения наиболее релевантных текстовых фрагментов из коллекции ChromaDB.
"""

import chromadb
from typing import List

# Локальные импорты
from app.logger import logger
from app.config import settings
from app.rag_service.exceptions import ChromaConnectionError
from app.rag_service.models import RetrievedChunk
from app.knowledge_base.embeddings import EmbeddingService




class Retriever:
    """
        Класс поиска релевантных текстовых фрагментов в базе знаний ChromaDB.

        Использует EmbeddingService для векторизации запроса и выполняет
        семантический поиск ближайших соседей по коллекции ChromaDB.
    """

    def __init__(self) -> None:
        """
            Инициализирует сервис векторизации и подключается к коллекции ChromaDB.
        """
        self.embedding_service = EmbeddingService()
        self._init_chroma()


    def _init_chroma(self) -> None:
        """
            Подключается к локальному хранилищу ChromaDB и загружает коллекцию.

            :raises ChromaConnectionError: При невозможности подключиться к базе данных
                                            или получить доступ к коллекции.
        """
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
        """
            Осуществляет векторный поиск ближайших документов по тексту запроса.

            :param query: Текст поискового запроса пользователя.
            :param top_k: Количество наиболее релевантных документов для выдачи.
            :return: Список найденных объектов RetrievedChunk с метаданными и расстоянием.
            :raises ChromaConnectionError: При ошибке выполнения запроса к базе данных.
        """
        logger.info(f"Поиск в БД для запроса: '{query[:60]}...'")

        # 1. Генерация векторного представления запроса
        query_vector = self.embedding_service.embed_query(query)

        try:
            # 2. Выполнение векторного поиска в ChromaDB
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )

        except Exception as e:
            logger.error(f"Ошибка при поиске в ChromaDB: {e}", exc_info=True)
            raise ChromaConnectionError(f"Ошибка поиска в базе знаний: {e}") from e

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
