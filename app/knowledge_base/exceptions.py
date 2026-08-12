"""
    Модуль пользовательских исключений для компонента базы знаний (Knowledge Base).

    Иерархия исключений позволяет классифицировать ошибки загрузки исходных файлов,
    предобработки текста, векторизации (эмбеддингов) и операций с векторной БД ChromaDB.
"""

# Локальные импорты
from app.exceptions import AppError




class KnowledgeBaseError(AppError):
    """Базовое исключение для всех ошибок модуля базы знаний."""
    pass


class LoaderError(KnowledgeBaseError):
    """Исключение, возникающее при ошибках загрузки или парсинга исходного JSON-датасета."""
    pass


class ProcessorError(KnowledgeBaseError):
    """Исключение, возникающее при ошибках очистки, форматирования и нарезки (chunking) текста."""
    pass


class EmbeddingError(KnowledgeBaseError):
    """Исключение, возникающее при ошибках загрузки модели эмбеддингов или генерации векторов."""
    pass


class ChromaError(KnowledgeBaseError):
    """Исключение, возникающее при ошибках инициализации, поиска или сохранения данных в ChromaDB."""
    pass
