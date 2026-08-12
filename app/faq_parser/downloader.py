"""
    Модуль асинхронной загрузки веб-страниц с использованием Playwright.

    Предоставляет класс Downloader с поддержкой выполнения JavaScript-сценариев,
    ожидания появления DOM-элементов, обработки таймаутов и повторных попыток (Retry Logic).
"""

import asyncio
from types import TracebackType
from typing import Optional, Type
from playwright.async_api import (
    async_playwright,
    Playwright,
    Browser,
    BrowserContext,
    TimeoutError as PlaywrightTimeoutError,
)

# Локальные импорты
from app.config import settings
from app.logger import logger
from app.faq_parser.exceptions import DownloadError



class Downloader:
    """
        Асинхронный загрузчик веб-страниц на базе headless-браузера Chromium (Playwright).

        Поддерживает рендеринг клиентского JavaScript, ожидание появления конкретных
        селекторов и механизм повторных попыток при сбоях сети или задержках ответа.
    """

    def __init__(self) -> None:
        """
            Инициализирует экземпляр загрузчика с пустыми ссылками на ресурсы Playwright.
        """
        self._playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None


    async def __aenter__(self) -> "Downloader":
        """
            Вход в асинхронный контекстный менеджер (async with).
            :return: Запущенный и готовый к работе экземпляр Downloader.
        """
        await self.start()
        return self


    async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType],
    ) -> None:
        """
            Выход из асинхронного контекстного менеджера с гарантированным освобождением ресурсов.
        """
        await self.close()


    async def start(self) -> None:
        """
            Запускает процесс браузера Playwright и создает изолированный контекст.

            :raises DownloadError: Если не удалось инициализировать браузер Playwright.
        """
        logger.info("Запуск браузера Playwright...")

        try:
            self._playwright = await async_playwright().start()
            self.browser = await self._playwright.chromium.launch(headless=True) # Запускаем браузер в фоновом режиме (headless=True)
            self.context = await self.browser.new_context(user_agent=settings.HEADERS.get("User-Agent"))

        except Exception as e:
            logger.error(f"Не удалось инициализировать Playwright: {e}", exc_info=True)
            raise DownloadError(f"Ошибка старта браузера: {e}") from e


    async def get_html(self, url: str, wait_selector: Optional[str] = None) -> str:
        """
            Открывает веб-страницу в новой вкладке браузера и извлекает ее результирующий HTML-код.
            Использует механизм повторных попыток (Retry Logic) с паузой, увеличивающейся с каждой попыткой.

            :param url: Целевой URL-адрес для загрузки.
            :param wait_selector: CSS-селектор элемента, появления которого необходимо дождаться перед сбором HTML.
            :return: Полный HTML-код загруженной страницы.
            :raises DownloadError: Если браузер не запущен или исчерпаны все попытки загрузки.
        """
        if not self.context:
            raise DownloadError("Браузер не запущен. Вызовите start() или используйте 'async with'.")

        last_exception: Optional[Exception] = None

        for attempt in range(1, settings.MAX_RETRIES + 1):
            page = None
            try:
                page = await self.context.new_page()

                # Переход по целевому URL-адресу
                await page.goto(url, timeout=settings.TIMEOUT * 1000)

                # Ожидание появления селектора или полной загрузки DOM
                if wait_selector: await page.wait_for_selector(wait_selector, timeout=settings.TIMEOUT * 1000)
                else: await page.wait_for_load_state("domcontentloaded")

                html = await page.content()
                return html

            except (PlaywrightTimeoutError, Exception) as e:
                last_exception = e
                logger.warning(f"Попытка {attempt}/{settings.MAX_RETRIES} не удалась для {url}: {e}")
                if attempt < settings.MAX_RETRIES:
                    # Увеличиваем паузу с каждой неудачной попыткой
                    await asyncio.sleep(settings.REQUEST_DELAY * attempt)
            finally:
                if page:
                    await page.close()

        logger.error(f"Все {settings.MAX_RETRIES} попытки загрузки {url} завершились ошибкой.")
        raise DownloadError(f"Превышено число попыток загрузки {url}: {last_exception}") from last_exception


    async def close(self):
        """
            Безопасно закрывает контекст браузера и останавливает процесс Playwright.
        """
        logger.info("Закрытие ресурсов браузера...")

        if self.context:
            try: await self.context.close()
            except Exception as e: logger.warning(f"Ошибка при закрытии контекста браузера: {e}")
            finally: self.context = None

        if self.browser:
            try: await self.browser.close()
            except Exception as e: logger.warning(f"Ошибка при закрытии процесса браузера: {e}")
            finally: self.browser = None

        if self._playwright:
            try: await self._playwright.stop()
            except Exception as e: logger.warning(f"Ошибка при остановке Playwright: {e}")
            finally: self._playwright = None

        logger.info("Все ресурсы браузера успешно закрыты.")
