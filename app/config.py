import os
from datetime import datetime
from pathlib import Path




# Корень проекта (lime-ai-assistant/), вычисляется от расположения этого файла,
# а не от текущей рабочей директории — работает одинаково откуда угодно запущено
BASE_DIR = Path(__file__).resolve().parent.parent


# Базовый URL сайта
BASE_URL = "https://limehd.tv"

# URL начальной страницы FAQ
FAQ_START_URL = f"{BASE_URL}/faq/0"



# --- Селекторы верстки (CSS Selectors) ---
# Меню и списки
SECTION_BLOCK_SELECTOR = ".p-1"
SECTION_TITLE_SELECTOR = "h3"
QUESTION_LINK_SELECTOR = "a[href*='/faq/'][href*='/question/']"

# Контент ответа
ANSWER_PRIMARY_SELECTOR = "span.text-content-secondary"
ANSWER_FALLBACK_HEADING_SELECTOR = "h2"

# Селектор ожидания загрузки элемента на странице ответа
ANSWER_WAIT_SELECTOR = f"{ANSWER_PRIMARY_SELECTOR}, {ANSWER_FALLBACK_HEADING_SELECTOR}"


# Единая точка правды для сырых данных — сюда парсер кладет,
# отсюда же в будущем будет читать индексатор

# Путь для сохранения результата
DATA_DIR = BASE_DIR / "data"

# Конечный путь до файла
OUTPUT_FILE = DATA_DIR / "faq_data.json"


# Название папки логгирования
LOG_DIR = BASE_DIR / "logs"

# Название файла логов
LOG_FILENAME = f"parser_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

# Путь до файла логов
LOG_FILE = LOG_DIR / LOG_FILENAME

# Настройки логирования
LOG_LEVEL = "DEBUG"  # "INFO", "DEBUG", "WARNING", "ERROR"



# Заголовки для имитации реального браузера
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Пауза между запросами в секундах (Rate Limit)
REQUEST_DELAY = 1.0

# Тайм-аут ожидания ответа сервера
TIMEOUT = 10

# Ограничение количества одновременно открытых вкладок/запросов
MAX_CONCURRENT = 8

# Количество повторных попыток при сетевых сбоях
MAX_RETRIES = 3