import argparse
import sys
from app.knowledge_base.orchestrator import IndexingPipeline
from app.logger import logger




def main():

    parser = argparse.ArgumentParser(description="Knowledge Base RAG CLI")
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
