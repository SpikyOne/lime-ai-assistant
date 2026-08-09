from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import AppError
from app.logger import logger
from app.rag_service.exceptions import InvalidQueryError




def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(InvalidQueryError)
    async def invalid_query_handler(request: Request, exc: InvalidQueryError) -> JSONResponse:
        # Сообщение этого исключения специально написано для показа пользователю
        return JSONResponse(status_code=400, content={"detail": str(exc)})


    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        # Любая другая внутренняя ошибка — подробности только в лог, наружу generic-текст
        # (иначе есть риск утечки внутренних деталей — URL Ollama, упоминание Chroma и т.п.)
        logger.error(f"Необработанная ошибка приложения: {exc}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Внутренняя ошибка сервера. Попробуйте позже."})


    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.critical(f"Непредвиденная необработанная ошибка: {exc}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Внутренняя ошибка сервера. Попробуйте позже."})