"""
    Главный модуль запуска и конфигурации FastAPI приложения Lime HD TV AI Assistant.

    Определяет жизненный цикл приложения (lifespan), подключает CORS-мидлвар,
    настраивает ограничение частоты запросов (Rate Limiting), глобальную обработку исключений,
    монтирует маршруты API и управляет readiness-состоянием сервиса.
"""

import asyncio

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

# Локальные импорты
from app.config import settings
from app.logger import logger
from app.rag_service.orchestrator import RAGPipeline
from app.rag_service.exceptions import LLMError
from app.api.error_handlers import register_exception_handlers
from app.api.rate_limit import limiter, rate_limit_handler
from app.api.routes import router as api_router




async def initialize_application(app: FastAPI) -> None:
    """
        Выполняет полную фоновую инициализацию приложения.

        Этапы:
            1. Создание RAGPipeline.
            2. Загрузка multilingual-e5-base.
            3. Подключение ChromaDB.
            4. Создание OllamaClient.
            5. Warmup Qwen.
            6. Перевод приложения в READY.

        До завершения функции app.state.ready=False.
    """
    pipeline = None

    try:
        logger.info("============================================================")
        logger.info("Начинается инициализация AI-пайплайна.")
        logger.info(f"LLM model: {settings.LLM_MODEL}")
        logger.info(f"LLM context: {settings.LLM_CONTEXT_TOKENS}")
        logger.info("============================================================")

        # RAGPipeline содержит синхронную загрузку SentenceTransformer.
        #
        # Выполняем её в отдельном worker thread, чтобы FastAPI
        # продолжал отвечать на /health и /ready во время запуска.
        pipeline = await asyncio.to_thread(RAGPipeline)

        app.state.pipeline = pipeline

        # Retriever.__init__ уже:
        #   1. загрузил E5;
        #   2. подключился к Chroma;
        #   3. получил коллекцию.
        # Поэтому после успешного создания pipeline эти два компонента считаем готовыми.
        app.state.readiness["pipeline"] = True
        app.state.readiness["chroma"] = True

        logger.info("RAGPipeline успешно инициализирован.")
        logger.info("Embeddings + ChromaDB готовы.")


        # ------------------------------------------------------------
        # Warmup LLM
        # ------------------------------------------------------------

        for attempt in range(1, settings.LLM_WARMUP_RETRIES + 1):
            try:
                logger.info(f"Прогрев LLM: попытка {attempt}/{settings.LLM_WARMUP_RETRIES}")

                await pipeline.warmup()

                app.state.readiness["llm"] = True
                app.state.ready = True
                app.state.startup_error = None

                logger.info("============================================================")
                logger.info("AI-ПАЙПЛАЙН ПОЛНОСТЬЮ ГОТОВ.")
                logger.info(f"Модель: {settings.LLM_MODEL}")
                logger.info("Embeddings: READY")
                logger.info("ChromaDB: READY")
                logger.info("LLM: READY")
                logger.info("============================================================")

                return

            except LLMError as e:
                logger.error(f"Warmup LLM не удался (попытка {attempt}): {e}", exc_info=True)

                if attempt < settings.LLM_WARMUP_RETRIES:
                    await asyncio.sleep(settings.LLM_WARMUP_DELAY)

        raise RuntimeError(
            "Не удалось прогреть LLM после "
            f"{settings.LLM_WARMUP_RETRIES} попыток."
        )

    except Exception as e:
        logger.critical(f"Критическая ошибка инициализации приложения: {e}", exc_info=True)

        app.state.ready = False
        app.state.startup_error = ("Не удалось полностью инициализировать AI-пайплайн.")

        # Если pipeline успел создаться, но warmup провалился, аккуратно освобождаем его ресурсы.
        if pipeline is not None:
            try: await pipeline.aclose()
            except Exception:
                logger.error("Ошибка освобождения неготового RAGPipeline.", exc_info=True)

        app.state.pipeline = None


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

        /health может отвечать сразу после запуска процесса.
        Полная готовность контролируется app.state.ready и проверяется через /ready.

        :param app: Экземпляр приложения FastAPI.
    """

    # ------------------------------------------------------------
    # Initial state
    # ------------------------------------------------------------
    app.state.pipeline = None
    app.state.ready = False
    app.state.readiness = {
        "pipeline": False,
        "chroma": False,
        "llm": False,
    }
    app.state.startup_error = None


    # ------------------------------------------------------------
    # Background initialization
    # ------------------------------------------------------------
    initialization_task = asyncio.create_task(
        initialize_application(app),
        name="rag-initialization",
    )

    logger.info("FastAPI запущен. Инициализация RAG выполняется в фоне.")

    try: yield

    finally:
        logger.info("Остановка приложения — освобождение ресурсов...")

        if not initialization_task.done():
            initialization_task.cancel()
            try: await initialization_task
            except asyncio.CancelledError: pass

        pipeline = getattr(app.state, "pipeline", None)

        if pipeline is not None:
            try: await pipeline.aclose()
            except Exception: logger.error("Ошибка закрытия RAGPipeline.", exc_info=True)

        logger.info("Ресурсы приложения освобождены.")



# ================================================================
# FastAPI application
# ================================================================

# Создание и конфигурация экземпляра приложения FastAPI
app = FastAPI(
    title="Lime HD TV AI Assistant API",
    description="REST API AI-ассистента поддержки пользователей Lime HD TV (RAG поверх локальной LLM).",
    version="1.8.9",
    lifespan=lifespan,
)



# ================================================================
# Rate limiting
# ================================================================

# Подключение лимитера частоты запросов (SlowAPI)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)



# ================================================================
# CORS
# ================================================================

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



# ================================================================
# Exception handlers
# ================================================================

# Регистрация централизованных обработчиков ошибок
register_exception_handlers(app)



# ================================================================
# Routes
# ================================================================

# Подключение маршрутов API
app.include_router(api_router)
