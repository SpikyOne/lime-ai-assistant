"""
    Модуль сервис-оркестратора для асинхронного парсинга FAQ.

    Управляет полным циклом сбора данных: загрузкой меню, параллельным извлечением
    текста ответов с ограничением со стороны семафора и сохранением итогового датасета.
"""

import asyncio
from typing import List, Optional

# Локальные импорты
from app.config import settings
from app.logger import logger
from app.faq_parser.models import FAQItem, QuestionLink, ParseStats
from app.faq_parser.exceptions import DownloadError, ExtractionError, SerializationError
from app.faq_parser.downloader import Downloader
from app.faq_parser.extractor import Extractor
from app.faq_parser.serializer import JSONSerializer




class FAQParserService:
    """
        Оркестратор процесса сбора, обработки и сохранения FAQ.

        Координирует работу Downloader, Extractor и JSONSerializer,
        контролируя параллелизм через asyncio.Semaphore и собирая статистику ParseStats.
    """

    def __init__(self, max_concurrent: int = settings.MAX_CONCURRENT):
        """
            Инициализирует сервис парсинга.
            :param max_concurrent: Максимальное количество одновременно обрабатываемых страниц/запросов.
        """
        self.extractor = Extractor()
        self.serializer = JSONSerializer()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.stats = ParseStats()


    async def _parse_item(self, downloader: Downloader, item: QuestionLink) -> Optional[FAQItem]:
        """
            Асинхронно загружает и парсит отдельную страницу вопроса FAQ.

            :param downloader: Экземпляр загрузчика страниц Downloader.
            :param item: Метаданные ссылки на вопрос.
            :return: Заполненный объект FAQItem или None в случае ошибки.
        """
        async with self.semaphore:
            logger.info(f"Парсинг вопроса [{item.id}]: {item.question}")

            # 1. Загрузка HTML-кода страницы вопроса
            try:
                answer_html = await downloader.get_html(
                    item.url,
                    wait_selector=settings.ANSWER_WAIT_SELECTOR
                )

            except DownloadError as e:
                self.stats.failed_download += 1
                logger.warning(f"Пропуск вопроса '{item.question}' из-за ошибки скачивания: {e}")
                return None

            # 2. Извлечение текста ответа из HTML
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
        """
            Запускает полный цикл сбора данных FAQ.
        """
        logger.info("Инициализация процесса сбора данных FAQ...")

        # Использование контекстного менеджера гарантирует корректное закрытие ресурсов браузера
        async with Downloader() as downloader:

            try:
                logger.info(f"Загрузка меню FAQ из {settings.FAQ_START_URL}...")
                # Указываем, что для главной страницы нам достаточно дождаться блоков меню (.p-1)
                main_html = await downloader.get_html(
                    settings.FAQ_START_URL,
                    wait_selector=settings.SECTION_BLOCK_SELECTOR
                )

                links_data = self.extractor.extract_faq_links(main_html)
                self.stats.total_found = len(links_data)

                if self.stats.total_found == 0:
                    logger.warning("Ссылки на вопросы не найдены. Завершение.")
                    return
                logger.info(f"Найдено вопросов: {self.stats.total_found}. Начинаем сбор ответов...")

                # Создание и параллельное выполнение задач сбора ответов
                tasks = [self._parse_item(downloader, item) for item in links_data]
                parsed_results = await asyncio.gather(*tasks)

                # Фильтрация успешно обработанных результатов
                results: List[FAQItem] = [res for res in parsed_results if res is not None]

                # Сериализация и сохранение результатов в JSON-файл
                self.serializer.save(results, settings.FAQ_DATA_FILE)

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
        """
            Выводит сводный отчет по метрикам выполнения парсинга в лог.
        """
        logger.info("=" * 60)
        logger.info("ИТОГОВЫЙ ОТЧЕТ ВЫПОЛНЕНИЯ (SUMMARY):")
        logger.info(f" Общее время работы     : {self.stats.elapsed_seconds} сек.")
        logger.info(f" Всего найдено ссылок   : {self.stats.total_found}")
        logger.info(f" Успешно распаршено     : {self.stats.successful}")
        logger.info(f" Ошибки скачивания (404/Timeout): {self.stats.failed_download}")
        logger.info(f" Ошибки извлечения текста      : {self.stats.failed_extraction}")
        logger.info(f" Процент успеха (Success Rate)  : {self.stats.success_rate}%")
        logger.info("=" * 60)
