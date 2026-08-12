"""
    Модуль сериализации и атомарного сохранения результатов парсинга FAQ.

    Предоставляет класс JSONSerializer для дедупликации объектов FAQItem
    и их безопасного сохранения на диск через механизм атомарной замены файлов.
"""

import os
import json
from dataclasses import asdict
from typing import List

# Локальные импорты
from app.logger import logger
from app.faq_parser.models import FAQItem
from app.faq_parser.exceptions import SerializationError




class JSONSerializer:
    """
        Класс для дедупликации и сериализации объектов FAQItem в формат JSON.
    """

    @staticmethod
    def save(data: List[FAQItem], filename: str):
        """
            Сохраняет список объектов FAQItem в JSON-файл с атомарной гарантией записи.

            Предварительно устраняет дубликаты по идентификатору (id) вопроса.
            Запись выполняется через временный файл (*.tmp) с последующей атомарной заменой (os.replace).

            :param data: Список элементов FAQItem для сохранения.
            :param filename: Целевой путь к JSON-файлу.
            :raises SerializationError: При ошибках доступа к файловой системе или сбоях сериализации JSON.
        """
        if not data:
            logger.warning("Список данных для сохранения пуст.")
            return

        temp_filename = f"{filename}.tmp"
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # Дедупликация объектов FAQItem по уникальному идентификатору id
            deduplicated_data = list({item.id: item for item in data}.values())
            dict_data = [asdict(item) for item in deduplicated_data]

            # Запись данных во временный файл
            with open(temp_filename, 'w', encoding='utf-8') as f:
                json.dump(dict_data, f, ensure_ascii=False, indent=4)

            # Атомарная замена оригинального файла
            os.replace(temp_filename, filename)
            logger.info(f"Успешно сохранено {len(data)} записей в {filename}")

        except (OSError, PermissionError) as e:
            logger.error(f"Ошибка доступа к файловой системе при сохранении {filename}: {e}", exc_info=True)
            raise SerializationError(f"Файловая ошибка: {e}") from e

        except TypeError as e:
            logger.error(f"Ошибка сериализации данных в JSON: {e}", exc_info=True)
            raise SerializationError(f"Ошибка JSON: {e}") from e

        finally:
            # Очистка временного файла в случае сбоя операции os.replace
            if os.path.exists(temp_filename):
                try: os.remove(temp_filename)
                except OSError as e: logger.warning(f"Не удалось удалить временный файл {temp_filename}: {e}")
