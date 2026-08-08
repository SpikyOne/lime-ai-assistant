import time
from dataclasses import dataclass, field




@dataclass
class QuestionLink:
    id: int
    section_id: int
    section_name: str
    url: str
    question: str



@dataclass
class FAQItem:
    id: int
    section_id: int
    section_name: str
    url: str
    question: str
    answer: str

    @classmethod
    def from_link(cls, link: QuestionLink, answer: str) -> "FAQItem":
        """Фабрика для удобного создания FAQItem из QuestionLink."""
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
    start_time: float = field(default_factory=time.monotonic)
    end_time: float = 0.0
    total_found: int = 0
    successful: int = 0
    failed_download: int = 0
    failed_extraction: int = 0

    def finish(self):
        self.end_time = time.monotonic()

    @property
    def elapsed_seconds(self) -> float:
        return round((self.end_time or time.monotonic()) - self.start_time, 2)

    @property
    def success_rate(self) -> float:
        if self.total_found == 0: return 0.0
        return round((self.successful / self.total_found) * 100, 1)
