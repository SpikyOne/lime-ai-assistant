import os
import json
from dataclasses import asdict
from typing import List

from .models import FAQItem
from app.logger import logger
from .exceptions import SerializationError



class JSONSerializer:
    """Отвечает за сериализацию и сохранение данных в JSON-формат."""

    @staticmethod
    def save(data: List[FAQItem], filename: str):
        """Сохраняет список объектов FAQItem в JSON-файл."""
        if not data:
            logger.warning("Список данных для сохранения пуст.")
            return

        temp_filename = f"{filename}.tmp"
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            data = list({item.id: item for item in data}.values())
            dict_data = [asdict(item) for item in data]

            # Пишем во временный файл
            with open(temp_filename, 'w', encoding='utf-8') as f:
                json.dump(dict_data, f, ensure_ascii=False, indent=4)

            # Заменяем оригинальный файл мгновенно (атомарно)
            os.replace(temp_filename, filename)
            logger.info(f"Успешно сохранено {len(data)} записей в {filename}")

        except (OSError, PermissionError) as e:
            logger.error(f"Ошибка доступа к файловой системе при сохранении {filename}: {e}")
            raise SerializationError(f"Файловая ошибка: {e}") from e
        except TypeError as e:
            logger.error(f"Ошибка сериализации данных в JSON: {e}")
            raise SerializationError(f"Ошибка JSON: {e}") from e
        finally:
            # Если временный файл остался (значит os.replace не выполнился), чистим его
            if os.path.exists(temp_filename):
                try: os.remove(temp_filename)
                except OSError as e: logger.warning(f"Не удалось удалить временный файл {temp_filename}: {e}")