class KnowledgeBaseError(Exception):
    """Базовое исключение для модуля knowledge-base."""
    pass


class LoaderError(KnowledgeBaseError):
    """Вызывается при ошибках загрузки или парсинга входных данных."""
    pass


class ProcessorError(KnowledgeBaseError):
    """Вызывается при ошибках предобработки и нарезки текста."""
    pass


class EmbeddingError(KnowledgeBaseError):
    """Вызывается при ошибках инициализации модели или генерации эмбеддингов."""
    pass


class ChromaError(KnowledgeBaseError):
    """Вызывается при ошибках инициализации или записи в ChromaDB."""
    pass