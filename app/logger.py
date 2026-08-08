import logging
import os
from logging.handlers import RotatingFileHandler

from . import config




# Убеждаемся, что папка для логов существует
os.makedirs(config.LOG_DIR, exist_ok=True)


# 0. Создаем логгер
logger = logging.getLogger("RAGLogger")


# 1. Динамический уровень логирования из config.py (если не задан — используется INFO)
log_level_name = getattr(config, "LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_name, logging.INFO)
logger.setLevel(log_level)


# 2. Единый формат логов: [Дата Время] | УРОВЕНЬ | Файл:строка | Сообщение
formatter = logging.Formatter(
    fmt='%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


# 3. Ротация логов: макс 5 МБ на файл, храним до 50 последних файлов
file_handler = RotatingFileHandler(         # Обработчик для записи в файл
    config.LOG_FILE,
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