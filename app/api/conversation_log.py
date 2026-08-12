"""
    Модуль асинхронного логирования диалогов пользователя с AI-ассистентом.

    Обеспечивает фоновую запись пар «вопрос-ответ» в JSON Lines файл
    с потокобезопасной гарантией записи и без блокировки основного Event Loop.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict

# Локальные импорты
from app.config import settings
from app.logger import logger




# Блокировка для исключения состояния гонки (race condition) при параллельной записи из async-задач
_write_lock = asyncio.Lock()


def _append_line(text: str) -> None:
    """
        Синхронно дописывает строку в файл лога диалогов.
        Создает директорию назначения, если она не существует.
        :param text: Сериализованная в JSON строка для записи.
    """
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(settings.CONVERSATION_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")


async def log_conversation(question: str, answer: str) -> None:
    """
        Сохраняет запись диалога (timestamp, вопрос и ответ) в лог-файл.
        Предназначен для запуска в качестве фоновой задачи (Background Task) FastAPI
        после отправки ответа клиенту, чтобы не увеличивать задержку (latency) ответа.
        :param question: Текст исходного вопроса пользователя.
        :param answer: Текст сформированного ответа AI-ассистента.
    """
    record: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "answer": answer,
    }
    line = json.dumps(record, ensure_ascii=False)

    async with _write_lock:
        try: await asyncio.to_thread(_append_line, line)
        except Exception as e: logger.error(f"Не удалось записать лог диалога: {e}", exc_info=True)
