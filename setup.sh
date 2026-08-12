#!/bin/bash
set -e

echo "==> Копирую .env (если ещё не создан)"
[ -f .env ] || cp .env.example .env

echo "==> Собираю образы"
docker compose build

echo "==> Строю базу знаний (модель эмбеддингов + индексация ChromaDB)"
docker compose --profile tools up indexer

echo "==> Поднимаю Ollama"
docker compose up -d ollama

echo ""
echo "==> Ollama скачивает и прогревает модель Qwen3 8B (~5 ГБ)."
echo "    Это разовая операция — при следующих запусках так долго не будет."
echo "    Ждём готовности..."
echo ""

until [ "$(docker inspect -f '{{.State.Health.Status}}' lime-ollama 2>/dev/null)" = "healthy" ]; do
  printf "."
  sleep 3
done

echo ""
echo "==> Модель готова. Запускаю API и демо-виджет."
docker compose up -d

sleep 3
if curl -sf http://localhost:8000/health >/dev/null; then
  echo ""
  echo "  Всё готово."
  echo "  API:          http://localhost:8000"
  echo "  Swagger:      http://localhost:8000/docs"
  echo "  Демо виджета: http://localhost:8080/demo/index.html"
else
  echo ""
  echo "API пока не отвечает — проверьте: docker compose logs -f api"
fi
