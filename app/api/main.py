from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.logger import logger
from app.rag_service.orchestrator import RAGPipeline
from app.api.error_handlers import register_exception_handlers
from app.api.rate_limit import limiter, rate_limit_handler
from app.api.routes import router as api_router




@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Инициализация RAG-пайплайна (embeddings + Chroma + Ollama-клиент)...")
    app.state.pipeline = RAGPipeline()
    logger.info("RAG-пайплайн готов, API принимает запросы.")

    yield

    logger.info("Остановка приложения — освобождение ресурсов...")
    await app.state.pipeline.aclose()
    logger.info("Ресурсы освобождены.")


app = FastAPI(
    title="Lime HD TV AI Assistant API",
    description="REST API AI-ассистента поддержки пользователей Lime HD TV (RAG поверх локальной LLM).",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Виджет подключается к произвольному стороннему сайту — CORS должен быть открытым,
# без credentials (токенов/куки виджет не использует).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(api_router)