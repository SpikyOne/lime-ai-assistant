import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

from app.config import settings




# Убеждаемся, что папка для логов существует
os.makedirs(settings.LOG_DIR, exist_ok=True)

# Название файла логов
log_filename = f"parser_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

# Путь до файла логов
log_file = settings.LOG_DIR / log_filename


# 0. Создаем логгер
logger = logging.getLogger("LimeAIAssistant")


# 1. Динамический уровень логирования из config.py (если не задан — используется INFO)
log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
logger.setLevel(log_level)


# 2. Единый формат логов: [Дата Время] | УРОВЕНЬ | Файл:строка | Сообщение
formatter = logging.Formatter(
    fmt='%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


# 3. Ротация логов: макс 5 МБ на файл, храним до 50 последних файлов
file_handler = RotatingFileHandler(         # Обработчик для записи в файл
    str(log_file),
    maxBytes=5 * 1024 * 1024,               # 5 MB
    backupCount=50,                         # Количество хранящихся ротированных файлов
    encoding='utf-8'
)
file_handler.setFormatter(formatter)


# 4. Обработчик для вывода в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)


# 5. Добавляем обработчики (проверка нужна, чтобы логи не задваивались при импортах)
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)