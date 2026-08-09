from typing import Annotated

from fastapi import Depends, Request

from app.rag_service.orchestrator import RAGPipeline


def get_pipeline(request: Request) -> RAGPipeline:
    """Возвращает singleton RAGPipeline, созданный один раз при старте приложения (см. lifespan в main.py)."""
    return request.app.state.pipeline


PipelineDep = Annotated[RAGPipeline, Depends(get_pipeline)]