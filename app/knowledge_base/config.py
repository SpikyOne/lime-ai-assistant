import os
from datetime import datetime
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict




class Config(BaseSettings):
    """Центральная конфигурация RAG-пайплайна."""

    # Корень проекта (knowledge-base/)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    # Пути к данным и векторной БД
    DATA_FILE_PATH: Path = BASE_DIR / "data" / "faq_data.json"
    CHROMA_PERSIST_DIR: Path = BASE_DIR / "storage" / "chroma"

    # Настройки ChromaDB
    CHROMA_COLLECTION_NAME: str = "limehd_faq"

    # Настройки модели эмбеддингов
    EMBEDDING_MODEL_NAME: str = "intfloat/multilingual-e5-base"

    # Локальная папка для сохранения модели (имя папки берется из названия модели, например: multilingual-e5-base)
    @property
    def EMBEDDING_MODEL_DIR(self) -> Path:
        folder_name = self.EMBEDDING_MODEL_NAME.split("/")[-1]
        return self.BASE_DIR / "models" / folder_name

    @property
    def model_path_or_name(self) -> str:
        """
        Возвращает путь к локальной папке, если модель уже скачана,
        иначе возвращает имя модели на HuggingFace.
        """
        if self.EMBEDDING_MODEL_DIR.exists() and (self.EMBEDDING_MODEL_DIR / "config.json").exists():
            return str(self.EMBEDDING_MODEL_DIR)
        return self.EMBEDDING_MODEL_NAME

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )



# Экспортируем готовый объект конфига
config = Config()


# Название папки логгирования
LOG_DIR = "logs"

# Название файла логов
LOG_FILENAME = f"parser_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

# Путь до файла логов
LOG_FILE = os.path.join(LOG_DIR, LOG_FILENAME)

# Настройки логирования
LOG_LEVEL = "DEBUG"  # "INFO", "DEBUG", "WARNING", "ERROR"



CHUNK_SIZE: int = 1000

CHUNK_OVERLAP: int = 150