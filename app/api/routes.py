"""
    Модуль маршрутизации REST API для Lime HD TV AI Assistant.

    Содержит обработчики HTTP-запросов:
        - GET /health: Проверка работоспособности сервиса (healthcheck).
        - POST /chat: Главный эндпоинт обработки вопросов пользователей с использованием RAG-пайплайна.
"""

from fastapi import APIRouter, BackgroundTasks, Request

# Локальные импорты
from app.config import settings
from app.api.conversation_log import log_conversation
from app.api.deps import PipelineDep
from app.api.rate_limit import limiter
from app.api.schemas import ChatRequest, ChatResponse, ErrorResponse, HealthResponse




router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Проверка состояния сервиса",
    tags=["service"]
)
async def health() -> HealthResponse:
    """
        Возвращает статус работоспособности приложения.
        Используется для Docker healthcheck, оркестраторов (Kubernetes) и внешних систем мониторинга.
    """
    return HealthResponse(status="ok")


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Некорректный запрос (например, пустой вопрос)"},
        429: {"model": ErrorResponse, "description": "Превышен лимит запросов"},
        500: {"model": ErrorResponse, "description": "Внутренняя ошибка сервера"},
    },
    summary="Генерация ответа на вопрос пользователя",
    tags=["chat"],
)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def chat(
    request: Request,
    payload: ChatRequest,
    pipeline: PipelineDep,
    background_tasks: BackgroundTasks,
) -> ChatResponse:
    """
        Принимает текстовый вопрос пользователя и возвращает ответ AI-ассистента.

        Процесс обработки включает:
            1. Поиск релевантного контекста в базе знаний Lime HD TV (ChromaDB).
            2. Генерацию ответа через LLM на основе найденных источников.
            3. Отправку асинхронной задачи логирования диалога в background task.

        :param request: Объект входящего HTTP-запроса (необходим для работы SlowAPI limiter).
        :param payload: Тело запроса с вопросом пользователя.
        :param pipeline: Синглтон-экземпляр RAGPipeline, внедряемый через FastAPI Dependency Injection.
        :param background_tasks: Диспетчер фоновых задач FastAPI.
        :return: Сформированный ответ и список использованных источников.
    """
    answer, sources = await pipeline.answer(payload.message)
    background_tasks.add_task(log_conversation, payload.message, answer)

    return ChatResponse(answer=answer, sources=sources)
