import json
from pathlib import Path
from typing import List, Union
from pydantic import ValidationError

from .config import config
from .models import RawFAQItem
from app.logger import logger
from .exceptions import LoaderError


class JSONLoader:
    """Загрузчик и валидатор исходных данных из JSON-файла."""

    def __init__(self, file_path: Union[str, Path, None] = None):
        # Если путь не передан, берем из конфига
        self.file_path = Path(file_path or config.DATA_FILE_PATH)

    def load(self) -> List[RawFAQItem]:
        """
        Считывает JSON файл, валидирует каждую запись через Pydantic
        и возвращает список объектов RawFAQItem.
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
            logger.error(f"Ошибка чтения JSON из файла {self.file_path}: {e}")
            raise LoaderError(f"Некорректный синтаксис JSON: {e}") from e
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при загрузке данных: {e}", exc_info=True)
            raise LoaderError(f"Ошибка при загрузке файла: {e}") from e
