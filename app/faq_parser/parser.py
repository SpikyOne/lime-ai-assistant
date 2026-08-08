import asyncio
from typing import List, Optional

from .. import config
from .models import FAQItem, QuestionLink, ParseStats
from .downloader import Downloader
from .extractor import Extractor
from .serializer import JSONSerializer
from app.logger import logger
from .exceptions import DownloadError, ExtractionError, SerializationError


class FAQParserService:
    """Оркестратор парсинга: асинхронно управляет процессом сбора, обработки и сохранения."""

    def __init__(self, max_concurrent: int = config.MAX_CONCURRENT):
        self.extractor = Extractor()
        self.serializer = JSONSerializer()
        self.semaphore = asyncio.Semaphore(max_concurrent) # Ограничиваем количество одновременно открытых вкладок
        self.stats = ParseStats()


    async def _parse_item(self, downloader: Downloader, item: QuestionLink) -> Optional[FAQItem]:
        """Асинхронная обработка одной ссылки."""
        async with self.semaphore:
            logger.info(f"Парсинг вопроса [{item.id}]: {item.question}")

            # 1. Скачивание
            # Указываем, что тут ждем класс ответа ИЛИ заголовок h2 для рекламной страницы
            try:
                answer_html = await downloader.get_html(
                    item.url,
                    wait_selector=config.ANSWER_WAIT_SELECTOR
                )
            except DownloadError as e:
                self.stats.failed_download += 1
                logger.warning(f"Пропуск вопроса '{item.question}' из-за ошибки скачивания: {e}")
                return None

            # 2. Извлечение текста
            try:
                answer_text = self.extractor.extract_answer(answer_html)
                if not answer_text:
                    raise ExtractionError("Извлеченный текст ответа пуст")

                self.stats.successful += 1
                return FAQItem.from_link(item, answer_text)

            except ExtractionError as e:
                self.stats.failed_extraction += 1
                logger.warning(f"Пропуск [{item.id}]. Не удалось извлечь текст ответа на странице: {item.url}. Ошибка парсинга: {e}")
                return None


    async def run(self):
        logger.info("Инициализация процесса сбора данных FAQ...")

        # Контекстный менеджер гарантирует закрытие сессий/браузера
        async with Downloader() as downloader:

            try:
                logger.info(f"Загрузка меню FAQ из {config.FAQ_START_URL}...")
                # Указываем, что для главной страницы нам достаточно дождаться блоков меню (.p-1)
                main_html = await downloader.get_html(config.FAQ_START_URL, wait_selector=config.SECTION_BLOCK_SELECTOR)

                links_data = self.extractor.extract_faq_links(main_html)
                self.stats.total_found = len(links_data)

                if self.stats.total_found == 0:
                    logger.warning("Ссылки на вопросы не найдены. Завершение.")
                    return
                logger.info(f"Найдено вопросов: {self.stats.total_found}. Начинаем сбор ответов...")

                # Создаем массив асинхронных задач и запускаем их одновременно
                tasks = [self._parse_item(downloader, item) for item in links_data]
                parsed_results = await asyncio.gather(*tasks)

                # Отфильтровываем None (те, что упали с ошибкой или не распарсились)
                results: List[FAQItem] = [res for res in parsed_results if res is not None]

                # Сохранение через отдельный сериализатор
                self.serializer.save(results, config.OUTPUT_FILE)

            except DownloadError  as e:
                logger.critical(f"Не удалось загрузить стартовую страницу FAQ. Завершение работы. Ошибка: {e}")
            except ExtractionError as e:
                logger.critical(f"Критическая ошибка на стартовом этапе: {e}")
            except SerializationError as e:
                logger.critical(f"Сбор данных завершен, но произошла фатальная ошибка при сохранении результатов: {e}")

            finally:
                self.stats.finish()
                self._log_summary()
                logger.info("Работа парсера завершена.")



    def _log_summary(self):
        """Вывод сводного отчета о выполнении парсинга."""
        logger.info("=" * 60)
        logger.info("ИТОГОВЫЙ ОТЧЕТ ВЫПОЛНЕНИЯ (SUMMARY):")
        logger.info(f" Общее время работы     : {self.stats.elapsed_seconds} сек.")
        logger.info(f" Всего найдено ссылок   : {self.stats.total_found}")
        logger.info(f" Успешно распаршено     : {self.stats.successful}")
        logger.info(f" Ошибки скачивания (404/Timeout): {self.stats.failed_download}")
        logger.info(f" Ошибки извлечения текста      : {self.stats.failed_extraction}")
        logger.info(f" Процент успеха (Success Rate)  : {self.stats.success_rate}%")
        logger.info("=" * 60)