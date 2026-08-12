# Lime HD TV — AI-ассистент поддержки

RAG-ассистент на локальной LLM (Ollama / Qwen3 8B): отвечает на вопросы пользователей
по FAQ сервиса Lime HD TV. Работает полностью локально, без внешних AI API.

## Требования

Docker + Docker Compose. ~10 ГБ свободного места (модель эмбеддингов + веса LLM).
Интернет нужен только при первом запуске.

## Быстрый старт

```bash
git clone <репозиторий>
cd lime-ai-assistant
bash setup.sh
```

Либо теми же командами вручную:
```bash
cp .env.example .env
docker compose build
docker compose --profile tools up indexer
docker compose up -d
```

Первый запуск: скачивание модели эмбеддингов и весов Qwen3 8B (~6 ГБ суммарно) —
может занять несколько минут в зависимости от скорости интернета.

## Проверка

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Как отменить подписку?"}'
```
Ответ:
```json
{"answer": "...", "sources": ["https://limehd.tv/faq/8/question/1"]}
```
Swagger-документация: http://localhost:8000/docs
Демо виджета: http://localhost:8080/demo/index.html

## Обычный запуск (данные уже построены)

```bash
docker compose up -d
```

## Обновление базы знаний

Вопросы изменились/добавились (ничего не удалено):
```bash
docker compose --profile tools up parser
docker compose --profile tools run --rm indexer python -m scripts.run_indexer
```

Вопросы были удалены из FAQ — нужна полная пересборка:
```bash
docker compose --profile tools up parser
docker compose --profile tools up indexer
```

## Подключение виджета на свой сайт

```html
<script src="widget.js"></script>
<script>
  LimeAI.init({ apiUrl: "http://localhost:8000" });
</script>
```

## Переменные окружения (.env)

| Переменная | Назначение | По умолчанию |
|---|---|---|
| `LLM_MODEL` | Модель в Ollama | `qwen3:8b` |
| `LLM_TEMPERATURE` | Температура генерации | `0.1` |
| `LLM_MAX_TOKENS` | Макс. длина ответа | `512` |
| `RATE_LIMIT_PER_MINUTE` | Лимит запросов на IP | `20` |
| `MAX_MESSAGE_LENGTH` | Макс. длина вопроса | `1000` |
| `CORS_ALLOWED_ORIGINS` | Разрешённые источники | `["*"]` |

## Известные ограничения

- Без GPU (по умолчанию) генерация ответа на CPU идёт медленнее, чем целевые 5 секунд
  из ТЗ — это ожидаемо для CPU-окружения проверки; с GPU-проходом для Ollama
  укладывается с запасом.
- Первый вопрос сразу после свежего `docker compose up` может получить ответ
  «сервис временно недоступен», если модель Qwen3 ещё докачивается фоном —
  подождите минуту и повторите (см. `docker compose logs -f ollama`).
