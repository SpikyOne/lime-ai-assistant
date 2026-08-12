"""
    Главный модуль запуска и конфигурации FastAPI приложения Lime HD TV AI Assistant.

    Определяет жизненный цикл приложения (lifespan), подключает CORS-мидлвар,
    настраивает ограничение частоты запросов (Rate Limiting), глобальную обработку исключений
    и монтирует маршруты API.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

# Локальные импорты
from app.config import settings
from app.logger import logger
from app.rag_service.orchestrator import RAGPipeline
from app.api.error_handlers import register_exception_handlers
from app.api.rate_limit import limiter, rate_limit_handler
from app.api.routes import router as api_router




@asynccontextmanager
async def lifespan(app: FastAPI):
    """
        Управляет жизненным циклом (startup/shutdown) приложения FastAPI.

        На этапе запуска (startup):
        - Инициализирует синглтон RAGPipeline (загрузка моделей эмбеддингов,
          подключение к векторному хранилищу ChromaDB и клиенту Ollama).
        - Сохраняет экземпляр пайплайна в `app.state.pipeline`.

        На этапе завершения (shutdown):
        - Корректно закрывает ресурсы пайплайна (сессии асинхронных HTTP-клиентов).

        :param app: Экземпляр приложения FastAPI.
    """
    logger.info("Инициализация RAG-пайплайна (embeddings + Chroma + Ollama-клиент)...")
    app.state.pipeline = RAGPipeline()
    logger.info("RAG-пайплайн готов, API принимает запросы.")

    yield

    logger.info("Остановка приложения — освобождение ресурсов...")
    await app.state.pipeline.aclose()
    logger.info("Ресурсы освобождены.")



# Создание и конфигурация экземпляра приложения FastAPI
app = FastAPI(
    title="Lime HD TV AI Assistant API",
    description="REST API AI-ассистента поддержки пользователей Lime HD TV (RAG поверх локальной LLM).",
    version="1.0.0",
    lifespan=lifespan,
)


# Подключение лимитера частоты запросов (SlowAPI)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)


# Конфигурация CORS (Cross-Origin Resource Sharing)
# Виджет встраивается в сторонние веб-страницы — разрешены кросс-доменные запросы
# без передачи куки/токенов (allow_credentials=False).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# Регистрация централизованных обработчиков ошибок
register_exception_handlers(app)


# Подключение маршрутов API
app.include_router(api_router)
