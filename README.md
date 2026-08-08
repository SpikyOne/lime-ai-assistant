# Примерная структура проекта

```
lime-ai-assistant/
├── app/
│   ├── __init__.py
│   ├── config.py                  # ЕДИНЫЙ Settings (Pydantic), всё остальное конфигурируется отсюда
│   ├── logger.py                  # ЕДИНЫЙ logger setup
│   ├── exceptions.py              # базовый AppError, от которого наследуются остальные
│   │
│   ├── ingestion/                 # бывший faq-parser
│   │   ├── __init__.py
│   │   ├── downloader.py
│   │   ├── extractor.py
│   │   ├── models.py              # QuestionLink
│   │   ├── serializer.py
│   │   ├── service.py             # бывший parser.py (FAQParserService)
│   │   └── exceptions.py          # DownloadError, ExtractionError, SerializationError
│   │
│   ├── indexing/                  # бывший knowledge_base
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   ├── processor.py
│   │   ├── embeddings.py
│   │   ├── chroma_repo.py         # бывший chroma.py (переименовать, не путать с пакетом chromadb)
│   │   ├── models.py              # RawFAQItem, ChunkMetadata, TextChunk
│   │   ├── pipeline.py            # бывший orchestrator.py (IndexingPipeline)
│   │   └── exceptions.py          # LoaderError, ProcessorError, EmbeddingError, ChromaError
│   │
│   ├── rag/                       # бывший rag_service
│   │   ├── __init__.py
│   │   ├── retriever.py           # исправленный импорт (см. ниже)
│   │   ├── context_builder.py
│   │   ├── guardrails.py
│   │   ├── models.py              # RetrievedChunk (переименовать из TextChunk — см. ниже)
│   │   ├── pipeline.py            # бывший orchestrator.py, тут наконец реализуется оркестрация
│   │   ├── exceptions.py          # LLMError, OllamaConnectionError, OllamaDownloadError, ChromaConnectionError
│   │   └── llm/                   # бывший lllm/ (опечатка исправлена)
│   │       ├── client.py          # async
│   │       ├── prompts.py
│   │       └── service.py
│   │
│   └── api/                       # НОВОЕ — тут ничего не было
│       ├── __init__.py
│       ├── main.py                # FastAPI app + lifespan (загрузка моделей один раз)
│       ├── schemas.py             # ChatRequest / ChatResponse
│       ├── deps.py                # singleton-провайдеры Retriever/LLMService/RAGPipeline
│       ├── rate_limit.py
│       ├── conversation_log.py    # запись даты/вопроса/ответа (sqlite или jsonl)
│       ├── error_handlers.py      # маппинг кастомных исключений → HTTP-коды
│       └── routes/
│           └── chat.py            # POST /chat
│
├── scripts/
│   ├── run_parser.py              # python -m scripts.run_parser
│   ├── run_indexer.py             # python -m scripts.run_indexer --rebuild
│   ├── download_embedding_model.py
│   ├── download_llm_model.py
│   └── chat_cli.py                # бывший tests/chat.py — интерактивная ручная проверка
│
├── data/
│   └── faq_data.json              # gitignored, генерится парсером
├── storage/
│   └── chroma/                    # gitignored, генерится индексатором
├── models/
│   └── multilingual-e5-base/      # gitignored, генерится скриптом
├── logs/                          # gitignored
│
├── tests/
│   ├── test_search.py             # бывший knowledge_base/tests/test_search.py
│   ├── eval_questions.json        # 20+ вопросов — критерий приёмки по ТЗ
│   └── test_rag_quality.py        # НОВОЕ: прогоняет eval_questions, считает % корректных
│
├── widget/                        # когда дойдёте — сюда
│
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```