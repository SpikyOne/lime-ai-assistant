import asyncio
import json
from datetime import datetime, timezone

from app.config import settings
from app.logger import logger




_write_lock = asyncio.Lock()


def _append_line(text: str) -> None:
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(settings.CONVERSATION_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")


async def log_conversation(question: str, answer: str) -> None:
    """Сохраняет дату/время, вопрос и ответ — требование ТЗ.
    Вызывается как фоновая задача, уже после того как ответ ушёл клиенту."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "answer": answer,
    }
    line = json.dumps(record, ensure_ascii=False)

    async with _write_lock:
        try: await asyncio.to_thread(_append_line, line)
        except Exception as e: logger.error(f"Не удалось записать лог диалога: {e}", exc_info=True)