"""
    Модуль извлечения структурированных данных из HTML-страниц FAQ.

    Использует библиотеку BeautifulSoup4 для синтаксического анализа HTML-кода,
    выделения ссылок на вопросы, названий разделов и извлечения текста ответов
    с применением основной и резервной (fallback) стратегий парсинга.
"""

from bs4 import BeautifulSoup
from typing import List, Optional

# Локальные импорты
from app.config import settings
from app.logger import logger
from app.faq_parser.models import QuestionLink
from app.faq_parser.exceptions import ExtractionError




class Extractor:
    """
        Класс-парсер для синтаксического анализа HTML-страниц и извлечения данных FAQ.
    """

    @staticmethod
    def extract_faq_links(html: str) -> List[QuestionLink]:
        """
            Извлекает из HTML-страницы список категорий и ссылок на отдельные вопросы.

            :param html: Исходный HTML-код главной страницы FAQ.
            :return: Список объектов QuestionLink с метаданными о вопросах.
            :raises ExtractionError: Если передан пустой HTML-документ.
        """
        if not html: raise ExtractionError("Передан пустой HTML для извлечения ссылок.")

        soup = BeautifulSoup(html, 'html.parser')
        faq_items: List[QuestionLink] = []

        # Поиск всех блоков разделов FAQ по CSS-селектору
        section_blocks = soup.select(settings.SECTION_BLOCK_SELECTOR)
        if not section_blocks:
            logger.warning("На главной странице не найдено блоков разделов.")
            return []

        for block in section_blocks:
            # Ищем название раздела (в данный момент h3)
            h3 = block.select_one(settings.SECTION_TITLE_SELECTOR)
            if not h3: continue

            section_name = h3.get_text(strip=True)

            # Поиск всех ссылок на вопросы в пределах текущего раздела
            links = block.select(settings.QUESTION_LINK_SELECTOR)
            for a in links:
                href = a.get('href', '')
                parts = href.strip('/').split('/')

                try:
                    section_id = int(parts[1])
                    question_id = int(parts[3])

                except (IndexError, ValueError):
                    logger.debug(f"Пропуск некорректного href: {href}")
                    continue

                faq_items.append(
                    QuestionLink(
                        id=question_id,
                        section_id=section_id,
                        section_name=section_name,
                        url=f"{settings.BASE_URL}{href}",
                        question=a.get_text(strip=True)
                    )
                )

        return faq_items


    @staticmethod
    def extract_answer(html: str) -> Optional[str]:
        """
            Извлекает текстовое содержимое ответа со страницы вопроса.

            Использует многоэтапную стратегию поиска:
                1. Основной селектор контейнера ответа.
                2. Резервный (fallback) селектор родительского блока заголовка для нестандартных страниц.

            :param html: Исходный HTML-код страницы вопроса.
            :return: Очищенный текст ответа с сохранением форматирования строк или None, если ответ не найден.
        """
        if not html: return None

        soup = BeautifulSoup(html, 'html.parser')

        # Стратегия 1: Извлечение из стандартного контейнера ответа
        answer_container = soup.select_one(settings.ANSWER_PRIMARY_SELECTOR)
        if answer_container:
            return answer_container.get_text(separator='\n', strip=True)

        # Стратегия 2: Резервный поиск для нестандартных/промо-страниц
        main_heading = soup.select_one(settings.ANSWER_FALLBACK_HEADING_SELECTOR)
        if main_heading:
            # Находим родительский блок, внутри которого лежит и заголовок, и текст
            parent_block = main_heading.find_parent('div')
            if parent_block:
                # Удаляем сам заголовок H2, чтобы предотвратить его дублирование в тексте ответа
                main_heading.decompose()
                return parent_block.get_text(separator='\n', strip=True)

        return None
