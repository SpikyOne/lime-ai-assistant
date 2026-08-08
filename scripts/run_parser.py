import asyncio
from app.faq_parser.parser import FAQParserService
from app.logger import logger



async def main():
    """Основная функция для инициализации и запуска парсера FAQ."""

    # Создаем экземпляр парсера
    service = FAQParserService()

    # Запускаем процесс сбора данных
    try: await service.run()
    except KeyboardInterrupt: logger.warning("Парсинг прерван пользователем (Ctrl+C).")
    except Exception as e: logger.critical(f"Непредвиденная системная ошибка: {e}", exc_info=True)

if __name__ == '__main__':
    asyncio.run(main())