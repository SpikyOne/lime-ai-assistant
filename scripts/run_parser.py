"""
    Скрипт запуска асинхронного парсера данных FAQ.

    Инициализирует и запускает сервис `FAQParserService` для сбора,
    парсинга и сохранения исходных данных FAQ в файл JSON.
"""

import asyncio

# Локальные импорты
from app.faq_parser.parser import FAQParserService
from app.logger import logger



async def main() -> None:
    """
        Инициализирует и запускает асинхронный процесс парсинга FAQ.
    """

    # Создаем экземпляр парсера
    service = FAQParserService()

    # Запускаем процесс сбора данных
    try: await service.run()
    except KeyboardInterrupt: logger.warning("Парсинг прерван пользователем (Ctrl+C).")
    except Exception as e: logger.critical(f"Непредвиденная системная ошибка: {e}", exc_info=True)

if __name__ == '__main__':
    asyncio.run(main())
