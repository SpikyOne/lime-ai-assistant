from fastapi import APIRouter, BackgroundTasks, Request

from app.config import settings
from app.api.conversation_log import log_conversation
from app.api.deps import PipelineDep
from app.api.rate_limit import limiter
from app.api.schemas import ChatRequest, ChatResponse, ErrorResponse, HealthResponse




router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["service"])
async def health() -> HealthResponse:
    """Проверка живости процесса — для Docker healthcheck и мониторинга."""
    return HealthResponse(status="ok")


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Некорректный запрос (например, пустой вопрос)"},
        429: {"model": ErrorResponse, "description": "Превышен лимит запросов"},
        500: {"model": ErrorResponse, "description": "Внутренняя ошибка сервера"},
    },
    tags=["chat"],
)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def chat(
    request: Request,
    payload: ChatRequest,
    pipeline: PipelineDep,
    background_tasks: BackgroundTasks,
) -> ChatResponse:
    """Принимает вопрос пользователя, возвращает ответ, построенный RAG-пайплайном."""

    answer, sources = await pipeline.answer(payload.message)
    background_tasks.add_task(log_conversation, payload.message, answer)

    return ChatResponse(answer=answer, sources=sources)