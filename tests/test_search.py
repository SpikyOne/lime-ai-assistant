from app.knowledge_base.embeddings import EmbeddingService
from app.knowledge_base.chroma import ChromaRepository


def test_rag():
    print("Загрузка модели и подключение к БД...")
    embedder = EmbeddingService()
    repo = ChromaRepository()

    # Список вопросов от "пользователя", написанных разными формулировками
    test_queries = [
        "У меня черный экран вместо видео, что делать?",
        "Как отменить платную подписку?",
        "Почему эфир отстает от телевизора на пару секунд?",
        "На скольких телевизорах можно смотреть один аккаунт?"
    ]

    print("\n" + "=" * 50)

    for query in test_queries:
        print(f"ВОПРОС ПОЛЬЗОВАТЕЛЯ: '{query}'")

        # 1. Превращаем вопрос в вектор
        query_vector = embedder.embed_query(query)

        # 2. Ищем топ-2 самых подходящих ответа
        results = repo.search(query_vector, n_results=2)

        # ChromaDB возвращает списки списков (так как можно искать сразу несколько запросов)
        distances = results['distances'][0]
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]

        # 3. Выводим результаты
        for i in range(len(distances)):
            # Distance (косинусное расстояние): чем БЛИЖЕ К НУЛЮ, тем лучше совпадение!
            print(f"\n  [{i + 1}] Совпадение (Distance): {distances[i]:.4f}")
            print(f"  ID: {metadatas[i].get('faq_id')} | Раздел: {metadatas[i].get('section_name')}")

            # Выводим первые 150 символов документа, чтобы не засорять консоль
            doc_preview = documents[i].replace('\n', ' ')[:150]
            print(f"  Текст: {doc_preview}...")

        print("\n" + "=" * 50)


if __name__ == "__main__":
    test_rag()