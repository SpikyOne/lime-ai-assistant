#!/bin/bash

set -e


echo "============================================================"
echo " Lime AI Assistant — CPU mode"
echo "============================================================"



# ============================================================
# 1. .env
# ============================================================

echo ""
echo "==> Проверяю .env"

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Создан .env из .env.example"
else
    echo ".env уже существует"
fi



# ============================================================
# 2. BUILD
# ============================================================

echo ""
echo "==> Собираю Docker-образы"

docker compose build



# ============================================================
# 3. KNOWLEDGE BASE
# ============================================================

echo ""
echo "==> Проверяю/строю базу знаний (модель эмбеддингов + индексация ChromaDB)"

docker compose \
    --profile tools \
    up \
    --abort-on-container-exit \
    indexer



# ============================================================
# 4. START
# ============================================================

echo ""
echo "==> Запускаю систему"

docker compose up -d



# ============================================================
# 5. WAIT FOR /READY
# ============================================================

echo ""
echo "==> Жду полной готовности AI-пайплайна..."
echo ""
echo "    /health = процесс FastAPI жив"
echo "    /ready  = E5 + Chroma + Qwen готовы"
echo ""


MAX_ATTEMPTS=180
ATTEMPT=0

while true; do

    ATTEMPT=$((ATTEMPT + 1))

    if curl -sf http://localhost:8000/ready >/dev/null 2>&1; then
        break
    fi

    if [ "$ATTEMPT" -ge "$MAX_ATTEMPTS" ]; then

        echo ""
        echo "============================================================"
        echo "ОШИБКА: AI-пайплайн не стал READY"
        echo "============================================================"
        echo ""

        echo "Последние логи API:"
        docker compose logs --tail=100 api || true

        echo ""
        echo "Последние логи Ollama:"
        docker compose logs --tail=100 ollama || true

        exit 1
    fi

    printf "."
    sleep 3
done



# ============================================================
# 6. SUCCESS
# ============================================================

echo ""
echo ""
echo "============================================================"
echo " CPU режим готов"
echo "============================================================"

docker compose \
    exec \
    ollama \
    ollama ps || true

echo ""
echo ""
echo "============================================================"
echo "  Lime AI Assistant полностью готов!"
echo "============================================================"
echo ""
echo "  Health:  http://localhost:8000/health"
echo "  Ready:   http://localhost:8000/ready"
echo "  Swagger: http://localhost:8000/docs"
echo "  API:     http://localhost:8000/"
echo "  Widget:  http://localhost:8080/demo/index.html"
echo ""
echo "============================================================"
