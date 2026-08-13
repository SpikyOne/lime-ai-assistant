#!/bin/bash

set -e


echo "============================================================"
echo " Lime AI Assistant — NVIDIA GPU mode"
echo "============================================================"



# ============================================================
# -1. Проверка NVIDIA
# ============================================================

if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo ""
    echo "ОШИБКА:"
    echo "nvidia-smi не найден."
    echo ""
    echo "Убедитесь, что установлен NVIDIA драйвер."
    exit 1
fi


if ! nvidia-smi >/dev/null 2>&1; then
    echo ""
    echo "ОШИБКА:"
    echo "NVIDIA GPU недоступна."
    exit 1
fi



# ============================================================
# 0. Проверка Docker GPU
# ============================================================

echo ""
echo "==> Проверяю Docker GPU runtime..."

if ! docker run --rm --gpus all \
    nvidia/cuda:12.9.0-base-ubuntu22.04 \
    nvidia-smi >/dev/null 2>&1; then

    echo ""
    echo "ОШИБКА:"
    echo "Docker не может получить доступ к NVIDIA GPU."
    echo ""
    echo "Проверьте NVIDIA Container Toolkit / Docker GPU support."

    exit 1

fi

echo ""
echo "==> NVIDIA GPU доступна Docker."



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

docker compose \
    -f docker-compose.yml \
    -f docker-compose.gpu.yml \
    build



# ============================================================
# 3. KNOWLEDGE BASE
# ============================================================

echo ""
echo "==> Проверяю/строю базу знаний (модель эмбеддингов + индексация ChromaDB)"

docker compose \
    -f docker-compose.yml \
    -f docker-compose.gpu.yml \
    --profile tools \
    up \
    --abort-on-container-exit \
    indexer



# ============================================================
# 4. START
# ============================================================

echo ""
echo "==> Запускаю систему"

docker compose \
    -f docker-compose.yml \
    -f docker-compose.gpu.yml \
    up -d


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
echo " GPU режим готов"
echo "============================================================"

docker compose \
    -f docker-compose.yml \
    -f docker-compose.gpu.yml \
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
