"""
    Модуль единой конфигурации приложения LimeAIAssistant.

    Использует Pydantic BaseSettings для централизованного управления всеми
    параметрами приложения: парсером данных, векторизацией, базой данных ChromaDB,
    сервисом Ollama LLM, параметрами логирования и веб-сервером FastAPI.
"""

from pathlib import Path
from typing import Dict, List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict




class Settings(BaseSettings):
    """
        Единый класс конфигурации приложения: Ingestion -> Indexing -> RAG -> API.
    """

    # ==============================================================================
    # 1. ОБЩИЕ ПУТИ ПРОЕКТА (Base Paths)
    # ==============================================================================
    BASE_DIR: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent,
        description="Корневая директория проекта",
    )

    # ==============================================================================



    # ==============================================================================
    # 2. INGESTION & FAQ PARSER (app.faq_parser)
    # ==============================================================================
    BASE_URL: str = Field(
        default="https://limehd.tv",
        description="Базовый URL сайта для парсинга FAQ",
    )


    # --- Селекторы верстки (CSS Selectors) ---
    # Меню и списки
    SECTION_BLOCK_SELECTOR: str = Field(
        default=".p-1",
        description="CSS-селектор блока раздела FAQ",
    )
    SECTION_TITLE_SELECTOR: str = Field(
        default="h3",
        description="CSS-селектор заголовка раздела",
    )
    QUESTION_LINK_SELECTOR: str = Field(
        default="a[href*='/faq/'][href*='/question/']",
        description="CSS-селектор ссылок на вопросы",
    )

    # Контент ответа
    ANSWER_PRIMARY_SELECTOR: str = Field(
        default="span.text-content-secondary",
        description="Основной CSS-селектор текста ответа",
    )
    ANSWER_FALLBACK_HEADING_SELECTOR: str = Field(
        default="h2",
        description="Резервный CSS-селектор заголовка ответа",
    )


    # --- Настройки HTTP и сетевых запросов ---
    HEADERS: Dict[str, str] = Field(
        default_factory=lambda: {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        },
        description="Заголовки HTTP-запросов для имитации браузера",
    )

    REQUEST_DELAY: float = Field(
        default=1.0,
        description="Пауза между сетевыми запросами в секундах (Rate Limit)",
    )

    TIMEOUT: int = Field(
        default=10,
        description="Таймаут ожидания ответа сервера в секундах",
    )

    MAX_CONCURRENT: int = Field(
        default=8,
        description="Ограничение количества одновременно выполняемых асинхронных задач",
    )

    MAX_RETRIES: int = Field(
        default=3,
        description="Количество повторных попыток при сетевых сбоях",
    )

    @property
    def FAQ_START_URL(self) -> str:
        """URL начальной страницы раздела FAQ."""
        return f"{self.BASE_URL}/faq/0"

    @property
    def ANSWER_WAIT_SELECTOR(self) -> str:
        """Составной селектор ожидания загрузки элементов ответа на странице."""
        return f"{self.ANSWER_PRIMARY_SELECTOR}, {self.ANSWER_FALLBACK_HEADING_SELECTOR}"

    # ==============================================================================



    # ==============================================================================
    # 3. ДАННЫЕ И ПРОМЕЖУТОЧНОЕ ХРАНЕНИЕ (Data Storage)
    # ==============================================================================
    @property
    def DATA_DIR(self) -> Path:
        """Директория хранения данных и артефактов парсинга."""
        return self.BASE_DIR / "data"

    @property
    def FAQ_DATA_FILE(self) -> Path:
        """Полный путь к JSON-файлу с результатом парсинга FAQ."""
        return self.DATA_DIR / "faq_data.json"

    # ==============================================================================



    # ==============================================================================
    # 4. INDEXING & KNOWLEDGE BASE (app.knowledge_base)
    # ==============================================================================
    CHROMA_COLLECTION_NAME: str = Field(
        default="limehd_faq",
        description="Наименование коллекции в базе данных ChromaDB",
    )
    EMBEDDING_MODEL_NAME: str = Field(
        default="intfloat/multilingual-e5-base",
        description="Идентификатор модели векторных эмбеддингов на HuggingFace",
    )
    HF_TOKEN: Optional[str] = Field(
        default=None,
        description="Токен авторизации Hugging Face для снятия ограничений скорости скачивания",
    )
    CHUNK_SIZE: int = Field(
        default=1000,
        description="Максимальный размер текстового чанка в символах",
    )
    CHUNK_OVERLAP: int = Field(
        default=150,
        description="Размер перекрытия (overlap) между чанками в символах",
    )

    @property
    def CHROMA_PERSIST_DIR(self) -> Path:
        """Директория локального сохранения коллекции ChromaDB."""
        return self.BASE_DIR / "storage" / "chroma"

    @property
    def EMBEDDING_MODEL_DIR(self) -> Path:
        """Локальная папка для сохранения весов векторной модели."""
        model_folder_name = self.EMBEDDING_MODEL_NAME.split("/")[-1]
        return self.BASE_DIR / "models" / model_folder_name

    @property
    def model_path_or_name(self) -> str:
        """Возвращает локальный путь к модели при ее наличии или имя репозитория HF."""
        if (
                self.EMBEDDING_MODEL_DIR.exists()
                and
                (self.EMBEDDING_MODEL_DIR / "config.json").exists()
        ):
            return str(self.EMBEDDING_MODEL_DIR)
        return self.EMBEDDING_MODEL_NAME

    # ==============================================================================



    # ==============================================================================
    # 5. RAG SERVICE & LLM (app.rag_service)
    # ==============================================================================
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        description="Базовый URL локальной или удаленной службы Ollama API",
    )

    LLM_MODEL: str = Field(
        default="qwen3:8b",
        description="Наименование языковой модели в Ollama",
    )

    LLM_TEMPERATURE: float = Field(
        default=0.1,
        description="Температура генерации текста LLM",
    )

    LLM_MAX_TOKENS: int = Field(
        default=512,
        description="Максимальное количество генерируемых токенов ответа",
    )

    LLM_CONTEXT_TOKENS: int = Field(
        default=2048,
        description="Размер контекстного окна Ollama для одного запроса",
    )

    LLM_READ_TIMEOUT: int = Field(
        default=180,
        description="Максимальное время ожидания генерации ответа от Ollama",
    )

    LLM_WARMUP_RETRIES: int = Field(
        default=3,
        description="Количество повторных попыток прогрева LLM при старте",
    )

    LLM_WARMUP_DELAY: float = Field(
        default=2.0,
        description="Пауза между попытками прогрева LLM",
    )

    # ==============================================================================



    # ==============================================================================
    # 6. ЛОГИРОВАНИЕ (app.logger)
    # ==============================================================================
    LOG_LEVEL: str = Field(
        default="DEBUG",
        description="Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    @property
    def LOG_DIR(self) -> Path:
        """Директория сохранения ротируемых файлов логов."""
        return self.BASE_DIR / "logs"

    # ==============================================================================



    # ==============================================================================
    # 7. FASTAPI REST API (app.api)
    # ==============================================================================
    API_HOST: str = Field(
        default="0.0.0.0",
        description="Сетевой IP-адрес для запуска веб-сервера",
    )

    API_PORT: int = Field(
        default=8000,
        description="Сетевой порт для запуска веб-сервера",
    )

    CORS_ALLOWED_ORIGINS: List[str] = Field(
        default_factory=lambda: ["*"],          # Виджет встраивается на произвольные сайты
        description="Список разрешенных истоников CORS (Cross-Origin Resource Sharing)",
    )

    RATE_LIMIT_PER_MINUTE: int = Field(
        default=20,
        description="Максимальное количество запросов в минуту от одного IP",
    )

    MAX_MESSAGE_LENGTH: int = Field(
        default=1000,
        description="Максимально допустимая длина входящего вопроса от пользователя",
    )

    @property
    def CONVERSATION_LOG_FILE(self) -> Path:
        """Путь к файлу логирования диалогов пользователей в формате JSONL."""
        return self.DATA_DIR / "conversations.jsonl"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ==============================================================================



# Глобальный экземпляр настроек для экспорта и использования по всему проекту
settings = Settings()
