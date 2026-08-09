from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict




class Config(BaseSettings):
    """Конфигурация RAG-пайплайна (retrieval + LLM)."""

    # Файл лежит в app/rag_service/config.py — три уровня вверх до корня проекта
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent


    # ==========================================
    # Настройки ChromaDB
    # ==========================================
    # Та же база, что наполняет app.knowledge_base — пути обязаны совпадать
    CHROMA_PERSIST_DIR: Path = BASE_DIR / "storage" / "chroma"
    CHROMA_COLLECTION_NAME: str = "limehd_faq"


    # ==========================================
    # Настройки LLM (Ollama)
    # ==========================================
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "qwen3:8b"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 512

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

config = Config()