"""
    Модуль ограничения частоты запросов (Rate Limiting) для API.

    Использует библиотеку SlowAPI для предотвращения DoS/DDoS-атак и злоупотребления
    ресурсами сервера путем ограничения количества запросов с одного IP-адреса.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address




# Экземпляр ограничителя частоты запросов по IP-адресу клиента
limiter = Limiter(key_func=get_remote_address)


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
        Обрабатывает исключение при превышении пользователем допустимого лимита запросов.
        Возвращает клиенту ответ со статусом HTTP 429 (Too Many Requests).

        :param request: Входящий HTTP-запрос FastAPI.
        :param exc: Экземпляр исключения RateLimitExceeded от библиотеки SlowAPI.
        :return: Объект JSONResponse со статусом 429 и локализованным сообщением об ошибке.
    """
    return JSONResponse(
        status_code=429,
        content={"detail": "Слишком много запросов. Пожалуйста, подождите и попробуйте снова."},
    )
