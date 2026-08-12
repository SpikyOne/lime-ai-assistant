"""
    Скрипт проверки и тестирования качества векторного поиска в базе знаний.

    Выполняет пакетную векторизацию контрольных вопросов и ищет наиболее
    релевантные фрагменты (топ-2 совпадений) в хранилище ChromaDB.
"""

from typing import Any, Dict, List

# Локальные импорты
from app.knowledge_base.embeddings import EmbeddingService
from app.knowledge_base.chroma import ChromaRepository




def test_rag() -> None:
    """
        Запускает автотест векторного поиска для набора эталонных вопросов.
    """
    print("Загрузка модели и подключение к БД...")
    embedder = EmbeddingService()
    repo = ChromaRepository()

    # Список тестовых пользовательских вопросов в разных формулировках
    test_queries = [
        "У меня черный экран вместо видео, что делать?",
        "Как отменить платную подписку?",
        "Почему эфир отстает от телевизора на пару секунд?",
        "На скольких телевизорах можно смотреть один аккаунт?"
    ]

    print("\n" + "=" * 50)

    for query in test_queries:
        print(f"ВОПРОС ПОЛЬЗОВАТЕЛЯ: '{query}'")

        # 1. Векторизация тестового вопроса
        query_vector = embedder.embed_query(query)

        # 2. Поиск топ-2 подходящих вариантов
        results: Dict[str, List[Any]] = repo.search(query_vector, n_results=2)

        # ChromaDB возвращает списки списков (так как можно искать сразу несколько запросов)
        distances: List[float] = results.get("distances", [[]])[0]
        documents: List[str] = results.get("documents", [[]])[0]
        metadatas: List[Dict[str, Any]] = results.get("metadatas", [[]])[0]

        # 3. Вывод результатов совпадения
        for i in range(len(distances)):
            score = distances[i]
            doc_text = documents[i] if i < len(documents) else ""
            metadata = metadatas[i] if i < len(metadatas) else {}

            # Distance (косинусное расстояние): чем ближе к нулю, тем лучше совпадение
            print(f"\n  [{i + 1}] Совпадение (Distance): {score:.4f}")
            print(f"  ID: {metadata.get('faq_id', 'N/A')} | Раздел: {metadata.get('section_name', 'N/A')}")

            # Выводим первые 150 символов документа, чтобы не засорять консоль
            doc_preview = doc_text.replace('\n', ' ')[:150]
            print(f"  Текст: {doc_preview}...")

        print("\n" + "=" * 50)


if __name__ == "__main__":
    test_rag()
