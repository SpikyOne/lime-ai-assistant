from typing import List

from pydantic import BaseModel, Field

from app.config import settings


class ChatRequest(BaseModel):
    """Тело запроса POST /chat — совпадает с контрактом из ТЗ."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=settings.MAX_MESSAGE_LENGTH,
        description="Вопрос пользователя",
        examples=["Как смотреть ТВ бесплатно?"],
    )


class ChatResponse(BaseModel):
    """Ответ POST /chat. Поле answer обязательно по ТЗ; sources — доп. возможность (ссылки на FAQ)."""
    answer: str = Field(..., description="Ответ AI-ассистента")
    sources: List[str] = Field(default_factory=list, description="Ссылки на связанные вопросы FAQ")


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])


class ErrorResponse(BaseModel):
    """Единая форма тела ответа при ошибке — используется в OpenAPI-документации."""
    detail: str