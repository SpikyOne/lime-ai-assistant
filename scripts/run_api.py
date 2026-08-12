"""
    Скрипт точки входа для запуска REST API веб-сервера на базе FastAPI и Uvicorn.

    Запускает ASGI-сервер Uvicorn с конфигурацией хоста, порта
    и автоматической перезагрузкой (reload) из глобальных настроек приложения.
"""

import uvicorn

# Локальные импорты
from app.config import settings




def main() -> None:
    """Запускает ASGI-сервер Uvicorn с параметрами из конфигурации."""
    uvicorn.run(
        "app.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )



if __name__ == "__main__":
    main()
