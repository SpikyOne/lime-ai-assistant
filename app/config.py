from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List




class Settings(BaseSettings):
    """Единая конфигурация проекта: ingestion + indexing + RAG."""

    BASE_DIR: Path = Path(__file__).resolve().parent.parent                         # Корень проекта


    # ---------- Ingestion (faq_parser) ----------
    BASE_URL: str = "https://limehd.tv"                                             # Базовый URL сайта

    # --- Селекторы верстки (CSS Selectors) ---
    # Меню и списки
    SECTION_BLOCK_SELECTOR: str = ".p-1"
    SECTION_TITLE_SELECTOR: str = "h3"
    QUESTION_LINK_SELECTOR: str = "a[href*='/faq/'][href*='/question/']"

    # Контент ответа
    ANSWER_PRIMARY_SELECTOR: str = "span.text-content-secondary"
    ANSWER_FALLBACK_HEADING_SELECTOR: str = "h2"

    # Заголовки для имитации реального браузера
    HEADERS: dict = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    REQUEST_DELAY: float = 1.0                          # Пауза между запросами в секундах (Rate Limit)
    TIMEOUT: int = 10                                   # Тайм-аут ожидания ответа сервера
    MAX_CONCURRENT: int = 8                             # Ограничение количества одновременно открытых вкладок/запросов
    MAX_RETRIES: int = 3                                # Количество повторных попыток при сетевых сбоях

    @property
    def FAQ_START_URL(self) -> str:
        ''' URL начальной страницы FAQ. '''
        return f"{self.BASE_URL}/faq/0"

    @property
    def ANSWER_WAIT_SELECTOR(self) -> str:
        '''Селектор ожидания загрузки элемента на странице ответа'''
        return f"{self.ANSWER_PRIMARY_SELECTOR}, {self.ANSWER_FALLBACK_HEADING_SELECTOR}"

    # ---------- Общие данные (стык ingestion → indexing) ----------
    DATA_DIR: Path = BASE_DIR / "data"                  # Путь для сохранения результата

    @property
    def FAQ_DATA_FILE(self) -> Path:
        '''Конечный путь до .json файла faq вопросов'''
        return self.DATA_DIR / "faq_data.json"

    # ---------- Indexing (knowledge_base) ----------
    CHROMA_PERSIST_DIR: Path = BASE_DIR / "storage" / "chroma"              # Путь к векторной БД
    CHROMA_COLLECTION_NAME: str = "limehd_faq"                              # Название БД
    EMBEDDING_MODEL_NAME: str = "intfloat/multilingual-e5-base"             # Название модели эмбеддингов
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150

    @property
    def EMBEDDING_MODEL_DIR(self) -> Path:
        ''' Локальная папка для сохранения модели (имя папки берется из названия модели'''
        return self.BASE_DIR / "models" / self.EMBEDDING_MODEL_NAME.split("/")[-1]

    @property
    def model_path_or_name(self) -> str:
        """ Возвращает путь к локальной папке, если модель уже скачана, иначе возвращает имя модели на HuggingFace. """
        if self.EMBEDDING_MODEL_DIR.exists() and (self.EMBEDDING_MODEL_DIR / "config.json").exists():
            return str(self.EMBEDDING_MODEL_DIR)
        return self.EMBEDDING_MODEL_NAME


    # ---------- RAG (rag_service) ----------
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "qwen3:8b"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 512


    # ---------- Логирование ----------
    LOG_DIR: Path = BASE_DIR / "logs"                   # Название папки логгирования
    LOG_LEVEL: str = "DEBUG"                            # Настройки логирования: "INFO", "DEBUG", "WARNING", "ERROR"


    # ---------- API (FastAPI) ----------
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ALLOWED_ORIGINS: List[str] = ["*"]             # Виджет встраивается на произвольные сайты — ТЗ явно требует "любой сайт"
    RATE_LIMIT_PER_MINUTE: int = 20
    MAX_MESSAGE_LENGTH: int = 1000

    @property
    def CONVERSATION_LOG_FILE(self) -> Path:
        '''Путь к файлу с логом диалогов (дата, вопрос, ответ)'''
        return self.DATA_DIR / "conversations.jsonl"


    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")



# Экспортируем готовый объект настроек проекта
settings = Settings()


# ==================== Ingestion (faq_parser) ====================
# ================================================================