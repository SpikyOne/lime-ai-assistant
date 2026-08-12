"""
    Скрипт интерактивного CLI-тестирования RAG-пайплайна.

    Предоставляет консольный интерфейс для диалогового ввода вопросов,
    выполнения векторного поиска по базе знаний и получения ответов от LLM.
"""

import asyncio
import sys

# Локальные импорты
from app.rag_service.orchestrator import RAGPipeline




async def main() -> None:
    """
        Запускает диалоговый консольный цикл взаимодействия с RAG-пайплайном.
    """
    print("Инициализация RAG-пайплайна (модель эмбеддингов + Ollama)...")

    try: pipeline = RAGPipeline()
    except Exception as e:
        print(f"Ошибка инициализации: {e}")
        sys.exit(1)

    print("Готово. Для выхода — 'q', 'exit' или Ctrl+C.\n")

    try:
        while True:
            try:
                query = input("Вопрос: ").strip()
                if not query: continue

                if query.lower() in ("q", "quit", "exit", "выход"):
                    print("Завершение работы.")
                    break

                answer, sources = await pipeline.answer(query)
                print(f"\nОтвет: {answer}")

                if sources: print(f"Источники: {', '.join(sources)}")
                print()

            except KeyboardInterrupt: print("\nПрервано пользователем."); break
            except Exception as e: print(f"\nОшибка при обработке запроса: {e}")

    finally:
        await pipeline.aclose() # Гарантированное освобождение сетевых ресурсов клиента



if __name__ == "__main__":
    asyncio.run(main())
