"""
    Модуль загрузки и валидации исходного JSON-датасета FAQ.

    Предоставляет класс JSONLoader для чтения файлов, строгой валидации
    структуры записей через Pydantic-модели и фильтрации невалидных элементов.
"""

import json
from pathlib import Path
from typing import List, Union
from pydantic import ValidationError

# Локальные импорты
from app.config import settings
from app.logger import logger
from app.knowledge_base.models import RawFAQItem
from app.knowledge_base.exceptions import LoaderError




class JSONLoader:
    """
        Загрузчик и валидатор исходных данных FAQ из JSON-файла.

        Считывает JSON-файл, выполняет валидацию каждого объекта через Pydantic-модель
        RawFAQItem и пропускает некорректно сформированные записи с логированием ошибок.
    """

    def __init__(self, file_path: Union[str, Path, None] = None) -> None:
        """
            Инициализирует загрузчик с указанием пути к JSON-файлу.
            :param file_path: Путь к файлу с исходными данными. Если не указан,
                            используется значение по умолчанию из конфигурации.
        """
        self.file_path = Path(file_path or settings.FAQ_DATA_FILE)


    def load(self) -> List[RawFAQItem]:
        """
            Считывает и валидирует исходный JSON-датасет FAQ.

            :return: Список валидированных объектов RawFAQItem.
            :raises LoaderError: Если файл не найден, содержит некорректный JSON
                                или корневая структура не является списком.
        """
        if not self.file_path.exists():
            logger.error(f"Файл данных не найден по пути: {self.file_path}")
            raise LoaderError(f"Файл с исходными данными не найден: {self.file_path}")

        logger.info(f"Загрузка данных из {self.file_path}...")

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            if not isinstance(raw_data, list):
                raise LoaderError("Некорректная структура JSON: ожидался список объектов.")

            items: List[RawFAQItem] = []
            skipped_count = 0

            for idx, entry in enumerate(raw_data):
                try:
                    # Валидируем словарь через Pydantic модель
                    item = RawFAQItem.model_validate(entry)
                    items.append(item)

                except ValidationError as ve:
                    skipped_count += 1
                    faq_id = entry.get('id', 'неизвестен') if isinstance(entry, dict) else 'невалидная запись'
                    logger.warning(f"Пропуск некорректной записи #{idx} (FAQ ID: {faq_id}): {ve}")

            logger.info(
                f"Успешно загружено {len(items)} элементов из {len(raw_data)} "
                f"(пропущено невалидных: {skipped_count})."
            )
            return items

        except json.JSONDecodeError as e:
            logger.error(f"Ошибка чтения JSON из файла {self.file_path}: {e}", exc_info=True)
            raise LoaderError(f"Некорректный синтаксис JSON: {e}") from e

        except Exception as e:
            logger.error(f"Непредвиденная ошибка при загрузке данных: {e}", exc_info=True)
            raise LoaderError(f"Ошибка при загрузке файла: {e}") from e
