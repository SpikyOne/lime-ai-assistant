"""
    Модуль оркестрации пайплайна индексации и векторизации базы знаний.

    Предоставляет класс IndexingPipeline, объединяющий этапы загрузки JSON-данных,
    предобработки текста, генерации векторных эмбеддингов и индексации в ChromaDB.
"""

# Локальные импорты
from app.logger import logger
from app.knowledge_base.loader import JSONLoader
from app.knowledge_base.processor import TextProcessor
from app.knowledge_base.embeddings import EmbeddingService
from app.knowledge_base.chroma import ChromaRepository




class IndexingPipeline:
    """
        Оркестратор процесса построения и обновления векторной базы знаний.
    """

    def __init__(self) -> None:
        """
            Инициализирует компоненты пайплайна индексации.
        """
        self.loader = JSONLoader()
        self.processor = TextProcessor()
        self.embedding_service = EmbeddingService()
        self.chroma_repo = ChromaRepository()


    def run(self, force_rebuild: bool = False) -> None:
        """
            Запускает последовательный процесс загрузки, предобработки, векторизации и индексации.

            :param force_rebuild: Если True, существующая коллекция в ChromaDB будет полностью
                                очищена перед добавлением новых элементов.
        """
        logger.info("Запуск пайплайна построения базы знаний...")

        # 1. Загрузка исходных данных
        raw_items = self.loader.load()

        # 2. Предобработка текста и формирование чанков
        chunks = self.processor.process(raw_items)

        # 3. Генерация векторных эмбеддингов
        vectors = self.embedding_service.embed_chunks(chunks)

        # 4. Сохранение векторов и метаданных в ChromaDB
        self.chroma_repo.upsert(chunks, vectors, clear_existing=force_rebuild)

        logger.info("Пайплайн успешно завершен!")
