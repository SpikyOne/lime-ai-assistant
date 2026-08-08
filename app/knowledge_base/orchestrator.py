from .loader import JSONLoader
from .processor import TextProcessor
from .embeddings import EmbeddingService
from .chroma import ChromaRepository
from app.logger import logger




class IndexingPipeline:
    """Оркестратор процесса индексации данных в векторную БД."""

    def __init__(self):
        self.loader = JSONLoader()
        self.processor = TextProcessor()
        self.embedding_service = EmbeddingService()
        self.chroma_repo = ChromaRepository()

    def run(self, force_rebuild: bool = False) -> None:
        logger.info("Запуск пайплайна построения базы знаний...")

        # 1. Загрузка
        raw_items = self.loader.load()

        # 2. Обработка и нарезка на чанки
        chunks = self.processor.process(raw_items)

        # 3. Генерация эмбеддингов
        vectors = self.embedding_service.embed_chunks(chunks)

        # 4. Сохранение в ChromaDB
        self.chroma_repo.upsert(chunks, vectors, clear_existing=force_rebuild)

        logger.info("Пайплайн успешно завершен!")