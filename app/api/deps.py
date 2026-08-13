"""
    Модуль внедрения зависимостей (Dependency Injection) для FastAPI.

    Предоставляет фабричные функции и аннотированные типы для внедрения
    экземпляров ключевых сервисов (в частности, RAGPipeline) в обработчики HTTP-запросов.
"""

from typing import Annotated
from fastapi import Depends, HTTPException, Request

# Локальные импорты
from app.rag_service.orchestrator import RAGPipeline




def get_pipeline(request: Request) -> RAGPipeline:
    """
        Извлекает экземпляр RAGPipeline из состояния приложения (app.state).

        Экземпляр RAGPipeline инициализируется единовременно как Singleton
        при старте приложения (в lifespan контексте) и сохраняется в `request.app.state.pipeline`.
        До завершения initialization pipeline запросы не допускаются.

        :param request: Объект входящего HTTP-запроса FastAPI.
        :return: Инициализированный и готов к работе экземпляр RAGPipeline.
    """
    if not getattr(request.app.state, "ready", False):
        raise HTTPException(status_code=503, detail=("AI-ассистент ещё запускается. Повторите запрос через несколько секунд."))

    pipeline = getattr(request.app.state, "pipeline", None)

    if pipeline is None:
        raise HTTPException(status_code=503, detail=("AI-ассистент пока недоступен."))

    return pipeline


# Аннотированный тип зависимости для инжекции RAGPipeline в ендпоинты FastAPI
PipelineDep = Annotated[RAGPipeline, Depends(get_pipeline)]
