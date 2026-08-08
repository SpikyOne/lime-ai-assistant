from typing import List
import chromadb
from chromadb.config import Settings

from .config import config
from app.logger import logger
from .models import TextChunk
from .exceptions import ChromaError


class ChromaRepository:
    """Репозиторий для управления векторной базой данных ChromaDB."""

    def __init__(self):

        # ChromaDB ожидает пути в виде строк, а не объектов Path
        self.persist_dir = str(config.CHROMA_PERSIST_DIR)
        self.collection_name = config.CHROMA_COLLECTION_NAME

        logger.info(f"Инициализация ChromaDB. Директория: {self.persist_dir}")

        try:
            # Инициализируем клиента с сохранением на диск
            self.client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(
                    anonymized_telemetry=False,  # Отключаем телеметрию
                    allow_reset=True  # Разрешаем полный сброс базы (нужно для rebuild)
                )
            )
            self.collection = self._get_or_create_collection()

        except Exception as e:
            logger.error(f"Не удалось подключиться к ChromaDB: {e}", exc_info=True)
            raise ChromaError(f"Ошибка инициализации БД: {e}") from e

    def _get_or_create_collection(self):
        """Возвращает существующую коллекцию или создает новую с правильной метрикой."""
        # hnsw:space = cosine - лучший выбор для текстов, особенно с нормализованными векторами E5
        return self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def search(self, query_embedding: List[float], n_results: int = 3) -> dict:
        """
        Ищет в базе n_results ближайших документов по вектору запроса.
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            return results
        except Exception as e:
            logger.error(f"Ошибка при поиске в ChromaDB: {e}", exc_info=True)
            raise ChromaError(f"Ошибка поиска: {e}") from e


    def upsert(self, chunks: List[TextChunk], embeddings: List[List[float]], clear_existing: bool = False) -> None:
        """
        Сохраняет или обновляет чанки и их векторы в базе данных.
        Если clear_existing=True, коллекция будет полностью очищена перед записью.
        """
        if not chunks or not embeddings:
            logger.warning("Переданы пустые списки чанков или эмбеддингов для сохранения. Отмена операции.")
            return

        if len(chunks) != len(embeddings):
            msg = f"Несовпадение размерностей: {len(chunks)} чанков и {len(embeddings)} векторов."
            logger.error(msg)
            raise ChromaError(msg)

        if clear_existing:
            logger.info(f"Запрошена полная очистка коллекции '{self.collection_name}'...")
            try:
                self.client.delete_collection(self.collection_name)
                # Пересоздаем пустую коллекцию после удаления
                self.collection = self._get_or_create_collection()
                logger.info("Коллекция успешно очищена.")

            except Exception as e:
                logger.error(f"Ошибка при очистке коллекции: {e}")
                raise ChromaError(f"Не удалось очистить коллекцию: {e}") from e

        # Подготавливаем списки данных в формате, который требует ChromaDB
        ids = [chunk.id for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [chunk.metadata.to_chroma_dict() for chunk in chunks]

        total_items = len(ids)
        # ChromaDB имеет ограничения на размер одной транзакции (зависит от SQLite),
        # поэтому большие объемы данных лучше разбивать на батчи.
        batch_size = 2000

        logger.info(f"Начало записи {total_items} документов в коллекцию '{self.collection_name}'...")

        try:
            for i in range(0, total_items, batch_size):
                end_idx = min(i + batch_size, total_items)

                # Метод upsert (update/insert) добавит новые и перезапишет существующие ID
                self.collection.upsert(
                    ids=ids[i:end_idx],
                    documents=documents[i:end_idx],
                    metadatas=metadatas[i:end_idx],
                    embeddings=embeddings[i:end_idx]
                )
                logger.debug(f"Записан батч {i} - {end_idx} из {total_items}.")

            # Выводим финальную статистику
            final_count = self.collection.count()
            logger.info(f"Векторизация завершена! Всего документов в коллекции: {final_count}")

        except Exception as e:
            logger.error(f"Ошибка при сохранении данных в ChromaDB: {e}", exc_info=True)
            raise ChromaError(f"Ошибка записи в БД: {e}") from e