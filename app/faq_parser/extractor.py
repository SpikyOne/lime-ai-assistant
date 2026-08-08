from bs4 import BeautifulSoup
from typing import List, Optional

from .. import config
from .models import QuestionLink
from app.logger import logger
from .exceptions import ExtractionError




class Extractor:
    """Класс для извлечения данных из HTML с помощью BeautifulSoup."""

    @staticmethod
    def extract_faq_links(html: str) -> List[QuestionLink]:
        """Собирает структуру разделов и ссылки на все вопросы из меню."""

        if not html:
            raise ExtractionError("Передан пустой HTML для извлечения ссылок.")

        soup = BeautifulSoup(html, 'html.parser')
        faq_items: List[QuestionLink] = []


        # Ищем все блоки разделов по CSS-селектору
        # В данный момент находим все блоки разделов (ориентируемся на div с классом p-1)
        # Ориентируемся на то, что внутри есть <h3> и ссылки <a>
        section_blocks = soup.select(config.SECTION_BLOCK_SELECTOR)
        if not section_blocks:
            logger.warning("На главной странице не найдено блоков разделов.")
            return []

        for block in section_blocks:
            # Ищем название раздела (в данный момент h3)
            h3 = block.select_one(config.SECTION_TITLE_SELECTOR)
            if not h3: continue
            section_name = h3.get_text(strip=True)

            # Ищем все ссылки в этом разделе
            links = block.select(config.QUESTION_LINK_SELECTOR)
            for a in links:
                href = a.get('href', '')
                parts = href.strip('/').split('/')

                try:
                    section_id = int(parts[1])
                    question_id = int(parts[3])
                except (IndexError, ValueError):
                    logger.debug(f"Пропуск некорректного href: {href}")
                    continue

                faq_items.append(QuestionLink(
                    id=question_id,
                    section_id=section_id,
                    section_name=section_name,
                    url=f"{config.BASE_URL}{href}",
                    question=a.get_text(strip=True)
                ))

        return faq_items

    @staticmethod
    def extract_answer(html: str) -> Optional[str]:
        """Находит и возвращает текст ответа со страницы вопроса с поддержкой fallback-селекторов."""
        if not html: return None

        soup = BeautifulSoup(html, 'html.parser')

        # Стратегия 1: Стандартная страница FAQ (ищем контейнер по классу (работает независимо от того, span это или div))
        answer_container = soup.select_one(config.ANSWER_PRIMARY_SELECTOR)
        if answer_container:
            return answer_container.get_text(separator='\n', strip=True)

        # Стратегия 2: Нестандартная/рекламная страница (как ID 99999)
        # Ищем главный контентный блок, который обычно начинается с <h2>
        main_heading = soup.select_one(config.ANSWER_FALLBACK_HEADING_SELECTOR)
        if main_heading:
            # Находим родительский блок, внутри которого лежит и заголовок, и текст
            parent_block = main_heading.find_parent('div')
            if parent_block:
                # Извлекаем весь текст статьи. Переносы строк сохранят читаемость списков.
                # Удаляем сам заголовок h2 из найденного блока, чтобы он не дублировался в тексте ответа
                main_heading.decompose()
                return parent_block.get_text(separator='\n', strip=True)

        return None