#!/bin/bash
set -e

echo "==> Копирую .env (если ещё не создан)"
[ -f .env ] || cp .env.example .env

echo "==> Собираю образы"
docker compose build

echo "==> Строю базу знаний (модель эмбеддингов + индексация ChromaDB)"
docker compose --profile tools up indexer

echo "==> Поднимаю Ollama, API и демо-виджет"
docker compose up -d

echo "==> Готово. Проверка через несколько секунд..."
sleep 5
curl -sf http://localhost:8000/health && echo " — API отвечает" \
  || echo " — API ещё не готов. Подождите и проверьте: docker compose logs -f api"