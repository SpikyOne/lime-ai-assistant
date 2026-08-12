"""
    Модуль настройки централизованного логирования приложения.

    Конфигурирует глобальный логгер LimeAIAssistant с ротацией файлов
    и выводом сообщений в стандартный поток вывода (консоль).
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Локальные импорты
from app.config import settings




# Создание директории для файлов логов при ее отсутствии
os.makedirs(settings.LOG_DIR, exist_ok=True)

# Формирование имени текущего файла логов
log_filename = f"parser_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

# Формирование пути к текущему файлу лога
log_file = settings.LOG_DIR / log_filename


# 0. Инициализация и настройка главного логгера
logger = logging.getLogger("LimeAIAssistant")


# 1. Определение уровня логирования из конфигурации из config.py (если не задан — используется INFO)
log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
logger.setLevel(log_level)


# 2. Единый формат логирования для всех обработчиков: [Дата Время] | УРОВЕНЬ | Файл:строка | Сообщение
formatter = logging.Formatter(
    fmt='%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


# 3. # Обработчик ротации файлов (максимум 5 МБ на файл, до 50 ротированных файлов)
file_handler = RotatingFileHandler(         # Обработчик для записи в файл
    str(log_file),
    maxBytes=5 * 1024 * 1024,               # 5 MB
    backupCount=50,                         # Количество хранящихся ротированных файлов
    encoding='utf-8'
)
file_handler.setFormatter(formatter)


# 4. Обработчик вывода сообщений в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)


# 5. Добавление обработчиков (защита от дублирования при повторных импортах)
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
