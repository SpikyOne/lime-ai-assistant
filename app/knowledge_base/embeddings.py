"""
    Модуль генерации векторных эмбеддингов для текстовых чанков и поисковых запросов.

    Использует библиотеку SentenceTransformers и PyTorch для аппаратного ускорения
    вычислений (CUDA, MPS, CPU). Поддерживает специфичные префиксы для E5-моделей
    ("query: " / "passage: ") и L2-нормализацию векторов.
"""

from pathlib import Path
from typing import List, Union

import torch
from sentence_transformers import SentenceTransformer

# Локальные импорты
from app.config import settings
from app.logger import logger
from app.knowledge_base.exceptions import EmbeddingError
from app.knowledge_base.models import TextChunk




class EmbeddingService:
    """
        Сервис для векторного представления (векторизации) текстов через SentenceTransformers.

        Автоматически выбирает доступный вычислительный ускоритель (CUDA, Apple MPS или CPU),
        проверяет целостность локальных весов модели и форматирует тексты в соответствии
        с требованиями выбранной архитектуры эмбеддеров.
    """

    def __init__(self) -> None:
        """
            Инициализирует сервис векторизации и загружает модель эмбеддингов.
        """
        # 1. Получаем путь к локальной модели из конфига
        self.model_path = settings.model_path_or_name

        # 2. Строго проверяем, что модель скачана и файлы не повреждены
        self._validate_local_model(self.model_path)

        # 3. Автоматическое определение устройства для вычислений (GPU, MPS или CPU)
        if torch.cuda.is_available(): self.device = "cuda"
        elif torch.backends.mps.is_available(): self.device = "mps"  # Для Apple Silicon (M1/M2/M3)
        else: self.device = "cpu"

        logger.info(f"Инициализация EmbeddingService. Источник: {self.model_path}, Устройство: {self.device}")

        try: self.model = SentenceTransformer(str(self.model_path), device=self.device)
        except Exception as e:
            logger.error(f"Не удалось загрузить модель из {self.model_path}: {e}", exc_info=True)
            raise EmbeddingError(f"Ошибка инициализации embedding модели: {e}") from e


    def _validate_local_model(self, source: Union[str, Path]) -> str:
        """
            Проверяет существование локальной директории и целостность ключевых файлов модели.

            :param source: Путь к локальной директории или название модели из Hugging Face.
            :raises EmbeddingError: Если директория модели или конфигурационный файл config.json отсутствуют.
        """
        path = Path(source)

        # Признак локального пути — абсолютность или реальное существование на диске,
        # а не просто наличие "/" (у HF repo id вроде "intfloat/..." он тоже есть)
        if path.is_absolute() or path.exists():
            if not path.exists():
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

        return str(source)


    def embed_query(self, query: str) -> List[float]:
        """
            Генерирует L2-нормализованный векторный эмбеддинг для одного поискового запроса.

            :param query: Текст поискового запроса пользователя.
            :return: Список вещественных чисел, представляющих вектор запроса.
            :raises EmbeddingError: Если не удалось сгенерировать эмбеддинг.
        """
        try:
            is_e5 = "e5" in str(self.model_path).lower()
            prefix = "query: " if is_e5 else ""

            text_to_embed = f"{prefix}{query}"

            # Генерируем вектор для одного запроса
            embedding_ndarray = self.model.encode(
                [text_to_embed],
                convert_to_numpy=True,
                normalize_embeddings=True                       # Обязательно нормализуем, как и документы
            )

            return embedding_ndarray[0].tolist()

        except Exception as e:
            logger.error(f"Ошибка при генерации эмбеддинга запроса: {e}", exc_info=True)
            raise EmbeddingError(f"Не удалось векторизовать запрос: {e}") from e


    def embed_chunks(self, chunks: List[TextChunk], batch_size: int = 32) -> List[List[float]]:
        """
            Генерирует L2-нормализованные эмбеддинги для списка текстовых чанков.

            :param chunks: Список объектов TextChunk для векторизации.
            :param batch_size: Размер пакета (batch) для обработки моделью.
            :return: Список векторов заданной размерности, совместимый с ChromaDB.
            :raises EmbeddingError: При критической ошибке в процессе векторизации.
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
                show_progress_bar = True,                           # Выводит прогресс-бар в консоль
                convert_to_numpy = True,                            # Возвращает numpy array
                normalize_embeddings = True                         # ВАЖНО: нормализация L2 (улучшает качество косинусного поиска для E5)
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
