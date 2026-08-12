"""
    Модуль централизованной обработки исключений веб-приложения FastAPI.

    Определяет и регистрирует обработчики пользовательских и системных ошибок,
    обеспечивая маскирование внутренних деталей системы (preventing sensitive info leaks)
    и безопасное формирование HTTP-ответов для клиентов.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Локальные импорты
from app.exceptions import AppError
from app.logger import logger
from app.rag_service.exceptions import InvalidQueryError




def register_exception_handlers(app: FastAPI) -> None:
    """
        Регистрирует обработчики кастомных и непредвиденных исключений в приложения FastAPI.
        :param app: Экземпляр приложения FastAPI для подключения хэндлеров.
    """

    @app.exception_handler(InvalidQueryError)
    async def invalid_query_handler(request: Request, exc: InvalidQueryError) -> JSONResponse:
        """
            Обрабатывает ошибки валидации пользовательского запроса на уровне RAG.

            Сообщение исключения преднамеренно сфокусировано на пользователе и безопасно
            для отображения в клиенте.
        """
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)}
        )


    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """
            Обрабатывает базовые внутренние ошибки приложения.

            Детали ошибки записываются в лог с Traceback, а клиенту возвращается
            обобщенный текст во избежание утечки внутренней инфраструктуры (ChromaDB, Ollama API).
        """
        logger.error(f"Необработанная ошибка приложения: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Внутренняя ошибка сервера. Попробуйте позже."}
        )


    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
            Перехватывает любые непредвиденные системные исключения и критические сбои.
        """
        logger.critical(f"Непредвиденная необработанная ошибка: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Внутренняя ошибка сервера. Попробуйте позже."}
        )
