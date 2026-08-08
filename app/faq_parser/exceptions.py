class FAQParserError(Exception):
    """Базовое исключение для всех ошибок парсера."""
    pass

class DownloadError(FAQParserError):
    """Ошибка при загрузке или рендеринге страницы."""
    pass

class ExtractionError(FAQParserError):
    """Ошибка при извлечении данных из HTML."""
    pass

class SerializationError(FAQParserError):
    """Ошибка при сохранении данных в файл."""
    pass