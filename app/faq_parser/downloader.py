import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError

from .. import config
from app.logger import logger
from .exceptions import DownloadError



class Downloader:
    """Асинхронный загрузчик страниц через браузер с поддержкой JS-ренедринга Playwright."""

    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None


    async def __aenter__(self):
        """Вход в контекстный менеджер (async with)."""
        await self.start()
        return self


    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекстного менеджера с гарантированным закрытием ресурсов."""
        await self.close()


    async def start(self):
        """Инициализация асинхронного браузера Playwright"""
        logger.info("Запуск браузера Playwright...")

        try:
            self._playwright = await async_playwright().start()
            self.browser = await self._playwright.chromium.launch(headless=True) # Запускаем браузер в фоновом режиме (headless=True)
            self.context = await self.browser.new_context(user_agent=config.HEADERS.get("User-Agent"))

        except Exception as e:
            logger.error(f"Не удалось инициализировать Playwright: {e}")
            raise DownloadError(f"Ошибка старта браузера: {e}") from e



    async def get_html(self, url: str, wait_selector: Optional[str] = None) -> str:
        """ Открывает страницу в отдельной асинхронной вкладке и ждет появления конкретного элемента
        с поддержкой повторных попыток (Retry Logic)."""

        if not self.context:
            raise DownloadError("Браузер не запущен. Вызовите start() или используйте 'async with'.")

        last_exception = None


        for attempt in range(1, config.MAX_RETRIES + 1):
            page = None
            try:
                page = await self.context.new_page()

                # Переходим на страницу
                await page.goto(url, timeout=config.TIMEOUT * 1000)

                # Ждем только нужный тег
                if wait_selector: await page.wait_for_selector(wait_selector, timeout=config.TIMEOUT * 1000)
                else: await page.wait_for_load_state("domcontentloaded")

                html = await page.content()
                return html

            except (PlaywrightTimeoutError, Exception) as e:
                last_exception = e
                logger.warning(f"Попытка {attempt}/{config.MAX_RETRIES} не удалась для {url}: {e}")
                if attempt < config.MAX_RETRIES:
                    # Увеличиваем паузу с каждой неудачной попыткой
                    await asyncio.sleep(config.REQUEST_DELAY * attempt)
            finally:
                if page:
                    await page.close()

        logger.error(f"Все {config.MAX_RETRIES} попытки загрузки {url} завершились ошибкой.")
        raise DownloadError(f"Превышено число попыток загрузки {url}: {last_exception}") from last_exception



    async def close(self):
        """Безопасное закрытие всех ресурсов браузера при завершении работы."""
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