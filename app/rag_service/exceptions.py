class RAGServiceError(Exception):
    """Самое базовое исключение для всего RAG-пайплайна."""
    pass



# ==========================================
# Блок LLM (Ollama и генерация текста)
# ==========================================
class LLMError(RAGServiceError):
    """Базовое исключение для модуля LLM."""
    pass


class OllamaConnectionError(LLMError):
    """Вызывается, если Ollama не запущена или недоступна по сети."""
    pass


class OllamaDownloadError(LLMError):
    """Вызывается при ошибках во время скачивания весов модели."""
    pass



class ChromaConnectionError(RAGServiceError):
    """Вызывается, если не удалось подключиться к существующей коллекции ChromaDB."""
    pass