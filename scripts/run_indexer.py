"""
    Скрипт CLI для сборки и индексации базы знаний ChromaDB.

    Запускает пайплайн обработки файлов FAQ, генерации векторных эмбеддингов
    и заполнения векторного хранилища ChromaDB с опциональной полной пересборкой.
"""

import argparse
import sys

# Локальные импорты
from app.knowledge_base.orchestrator import IndexingPipeline
from app.logger import logger




def main() -> None:
    """
        Точка входа CLI для запуска пайплайна индексации базы знаний.
    """

    parser = argparse.ArgumentParser(description="CLI-инструмент для индексации базы знаний RAG.")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Очистить существующую базу ChromaDB перед индексацией"
    )
    args = parser.parse_args()

    try:
        pipeline = IndexingPipeline()
        pipeline.run(force_rebuild=args.rebuild)

    except KeyboardInterrupt:
        logger.warning("Процесс прерван пользователем.")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Критическая ошибка при выполнении пайплайна: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
