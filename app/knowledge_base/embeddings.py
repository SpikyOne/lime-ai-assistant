from pathlib import Path
from typing import List
import torch
from sentence_transformers import SentenceTransformer

from app.config import settings
from .exceptions import EmbeddingError
from app.logger import logger
from .models import TextChunk


class EmbeddingService:
    """Сервис для векторизации текста с помощью sentence-transformers."""

    def __init__(self):

        # 1. Получаем путь к локальной модели из конфига
        self.model_path = settings.model_path_or_name

        # 2. Строго проверяем, что модель скачана и файлы не повреждены
        self._validate_local_model(self.model_path)

        # 3. Автоматическое определение устройства для вычислений (GPU или CPU)
        if torch.cuda.is_available(): self.device = "cuda"
        elif torch.backends.mps.is_available(): self.device = "mps"  # Для Apple Silicon (M1/M2/M3)
        else: self.device = "cpu"

        logger.info(f"Инициализация EmbeddingService. Источник: {self.model_path}, Устройство: {self.device}")

        try: self.model = SentenceTransformer(str(self.model_path), device=self.device)
        except Exception as e:
            logger.error(f"Не удалось загрузить модель из {self.model_path}: {e}", exc_info=True)
            raise EmbeddingError(f"Ошибка инициализации embedding модели: {e}") from e



    def _validate_local_model(self, source: str) -> None:
        """Проверяет существование локальной папки и целостность ключевых файлов модели."""
        path = Path(source)

        # Если это локальный путь (содержит слэши или абсолютный путь)
        if path.is_absolute() or "/" in str(source) or "\\" in str(source):
            if not path.exists() or not path.is_dir():
                msg = (
                    f"Папка с моделью не найдена: {path.resolve()}\n"
                    f"Запустите скрипт загрузки: python -m scripts.download_embedding_model"
                )
                logger.error(msg)
                raise EmbeddingError(msg)

            # Проверяем наличие конфигурации (защита от недокачанной папки)
            config_file = path / "config.json"
            if not config_file.exists():
                msg = (
                    f"В папке {path.resolve()} отсутствует config.json. Модель скачана не полностью.\n"
                    f"Перезапустите скрипт загрузки: python scripts/download_model.py"
                )
                logger.error(msg)
                raise EmbeddingError(msg)



    def embed_query(self, query: str) -> List[float]:
        """Генерирует эмбеддинг для одного поискового запроса."""
        try:

            is_e5 = "e5" in str(self.model_path).lower()
            prefix = "query: " if is_e5 else ""

            text_to_embed = f"{prefix}{query}"

            # Генерируем вектор для одного запроса
            embedding_ndarray = self.model.encode(
                [text_to_embed],
                convert_to_numpy=True,
                normalize_embeddings=True  # Обязательно нормализуем, как и документы
            )

            return embedding_ndarray[0].tolist()

        except Exception as e:
            logger.error(f"Ошибка при генерации эмбеддинга запроса: {e}", exc_info=True)
            raise EmbeddingError(f"Не удалось векторизовать запрос: {e}") from e


    def embed_chunks(self, chunks: List[TextChunk], batch_size: int = 32) -> List[List[float]]:
        """
        Генерирует L2-нормализованные эмбеддинги (векторы) для списка текстовых чанков.
        Возвращает список списков float, который напрямую принимает ChromaDB.
        """
        if not chunks:
            logger.warning("Передан пустой список чанков для векторизации.")
            return []

        logger.info(f"Начало векторизации {len(chunks)} чанков (batch_size={batch_size})...")

        try:
            # Особенность моделей E5: перед документами в базе нужно добавлять префикс "passage: "
            # Это значительно повышает качество поиска.
            is_e5 = "e5" in str(self.model_path).lower()
            prefix = "passage: " if is_e5 else ""

            # Извлекаем текст из чанков и добавляем префикс (если нужен)
            texts_to_embed = [f"{prefix}{chunk.text}" for chunk in chunks]

            # Генерация эмбеддингов (encode поддерживает внутреннее батчирование)
            embeddings_ndarray = self.model.encode(
                texts_to_embed,
                batch_size = batch_size,
                show_progress_bar = True,  # Выводит прогресс-бар в консоль
                convert_to_numpy = True,  # Возвращает numpy array
                normalize_embeddings = True  # ВАЖНО: нормализация L2 (улучшает качество косинусного поиска для E5)
            )

            # Конвертируем numpy array в обычный list of lists для совместимости с БД
            embeddings_list = embeddings_ndarray.tolist()

            # Логируем размерность (для e5-base обычно 768)
            vector_dim = len(embeddings_list[0]) if embeddings_list else 0
            logger.info(f"Векторизация успешно завершена. Размерность вектора: {vector_dim}")

            return embeddings_list

        except Exception as e:
            logger.error(f"Ошибка при генерации эмбеддингов: {e}", exc_info=True)
            raise EmbeddingError(f"Критическая ошибка генерации эмбеддингов: {e}") from e