"""
    Скрипт интерактивного CLI-тестирования векторного поиска в ChromaDB.

    Предоставляет консольный интерфейс для ввода поисковых запросов,
    векторизации через EmbeddingService и отображения найденных чанков
    из ChromaRepository с оценкой степени релевантности (distance).
"""

import sys
from typing import Any, Dict, List

# Локальные импорты
from app.knowledge_base.embeddings import EmbeddingService
from app.knowledge_base.chroma import ChromaRepository




def run_chat() -> None:
    """
        Запускает диалоговый цикл консольного тестирования векторного поиска.
    """
    print("Загрузка нейросети и подключение к базе данных...")

    try:
        embedder = EmbeddingService()
        repo = ChromaRepository()

    except Exception as e:
        print(f"Ошибка инициализации: {e}")
        sys.exit(1)

    print("\n" + "=" * 55)
    print("Система поиска по базе знаний готова!")
    print("Введите свой вопрос ниже. Для выхода введите 'выход', 'q' или 'exit'.")
    print("=" * 55)

    while True:
        try:
            # Получаем ввод от пользователя
            query = input("\nВаш вопрос: ").strip()

            # Обработка пустого ввода и команд выхода
            if not query:
                continue

            if query.lower() in ['выход', 'exit', 'q', 'quit']:
                print("Завершение работы. До встречи!")
                break

            # 1. Векторизация поискового запроса
            query_vector = embedder.embed_query(query)

            # 2. Поиск top-3 релевантных чанков в хранилище
            results: Dict[str, List[Any]] = repo.search(query_vector, n_results=3)

            distances: List[float] = results.get("distances", [[]])[0]
            documents: List[str] = results.get("documents", [[]])[0]
            metadatas: List[Dict[str, Any]] = results.get("metadatas", [[]])[0]

            if not distances:
                print("Ничего не найдено.")
                continue

            print("\n" + "-" * 55)
            print("Ответы из базы знаний:")

            for i in range(len(distances)):
                score = distances[i]
                text = documents[i]
                url = metadatas[i].get('url', 'URL не указан')

                # Оценка уверенности совпадения по расстоянию
                if score < 0.20: confidence = "Высокая"
                elif score < 0.35: confidence = "Средняя"
                else: confidence = "Низкая (возможно, не по теме)"

                print(f"\nВариант {i + 1} | Уверенность: {confidence} (score: {score:.4f})")
                print(f"Ссылка: {url}")
                print(f"\n{text}")
                print("-" * 55)

        # Обработка остановки через Ctrl+C
        except KeyboardInterrupt:
            print("\n\nПроцесс прерван пользователем. Завершение работы.")
            break

        except Exception as e:
            print(f"\nПроизошла непредвиденная ошибка: {e}")



if __name__ == "__main__":
    run_chat()
