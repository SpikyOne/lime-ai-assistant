"""
    Модуль Pydantic-схем (DTO) для валидации входных и выходных данных API.

    Определяет структуры запросов и ответов для эндпоинтов `/chat` и `/health`,
    а также стандартную схему возврата сообщений об ошибках.
"""

from typing import List
from pydantic import BaseModel, Field

# Локальные импорты
from app.config import settings




class ChatRequest(BaseModel):
    """
        Схема входного запроса к эндпоинту POST /chat.
    """
    message: str = Field(
        ...,
        min_length=1,
        max_length=settings.MAX_MESSAGE_LENGTH,
        description="Вопрос пользователя к AI-ассистенту",
        examples=["Как смотреть ТВ бесплатно?"],
    )


class ChatResponse(BaseModel):
    """
        Схема успешного ответа эндпоинта POST /chat.
    """
    answer: str = Field(
        ...,
        description="Ответ AI-ассистента"
    )
    sources: List[str] = Field(
        default_factory=list,
        description="Список URL-ссылок на статьи/вопросы FAQ, использованные при подготовке ответа",
    )


class HealthResponse(BaseModel):
    """
        Схема ответа эндпоинта проверки работоспособности GET /health.
    """
    status: str = Field(
        ...,
        description="Текущий статус сервиса",
        examples=["ok"],
    )


class ErrorResponse(BaseModel):
    """
    Стандартная схема структуры ответа при возникновении ошибки.
    """
    detail: str = Field(
        ...,
        description="Подробное сообщение об ошибке",
    )
