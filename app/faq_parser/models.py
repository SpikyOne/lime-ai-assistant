"""
    Модуль структур данных и моделей данных парсера FAQ.

    Содержит dataclass-модели для представления ссылок на вопросы,
    итоговых записей FAQ и метрик статистики процесса парсинга.
"""

import time
from dataclasses import dataclass, field




@dataclass
class QuestionLink:
    """
        Представляет промежуточные метаданные ссылки на вопрос FAQ.
    """

    id: int
    section_id: int
    section_name: str
    url: str
    question: str



@dataclass
class FAQItem:
    """
        Представляет извлеченную и полную запись FAQ (вопрос и ответ).
    """

    id: int
    section_id: int
    section_name: str
    url: str
    question: str
    answer: str


    @classmethod
    def from_link(cls, link: QuestionLink, answer: str) -> "FAQItem":
        """
            Фабричный метод для создания объекта FAQItem из ссылки и текста ответа.

            :param link: Экземпляр QuestionLink с метаданными вопроса.
            :param answer: Текст извлеченного ответа.
            :return: Заполненный экземпляр FAQItem.
        """
        return cls(
            id=link.id,
            section_id=link.section_id,
            section_name=link.section_name,
            url=link.url,
            question=link.question,
            answer=answer
        )



@dataclass
class ParseStats:
    """
        Класс для сбора и расчета метрик статистики процесса парсинга.
    """

    start_time: float = field(default_factory=time.monotonic)
    end_time: float = 0.0
    total_found: int = 0
    successful: int = 0
    failed_download: int = 0
    failed_extraction: int = 0


    def finish(self):
        """
            Фиксирует время завершения процесса парсинга.
        """
        self.end_time = time.monotonic()


    @property
    def elapsed_seconds(self) -> float:
        """
            Возвращает длительность выполнения процесса парсинга в секундах.
            :return: Время выполнения в секундах с округлением до сотых.
        """
        return round((self.end_time or time.monotonic()) - self.start_time, 2)

    @property
    def success_rate(self) -> float:
        """
            Рассчитывает процент успешно извлеченных записей FAQ.
            :return: Доля успешно обработанных вопросов в процентах (от 0.0 до 100.0).
        """
        if self.total_found == 0: return 0.0
        return round((self.successful / self.total_found) * 100, 1)
