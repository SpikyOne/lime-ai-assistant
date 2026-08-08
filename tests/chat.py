import sys
from app.knowledge_base.embeddings import EmbeddingService
from app.knowledge_base.chroma import ChromaRepository


def run_chat():
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

            # 1. Векторизуем запрос
            query_vector = embedder.embed_query(query)

            # 2. Ищем топ-3 подходящих чанка в базе
            # Вы можете увеличить n_results, если хотите видеть больше вариантов
            results = repo.search(query_vector, n_results=3)

            distances = results.get('distances', [[]])[0]
            documents = results.get('documents', [[]])[0]
            metadatas = results.get('metadatas', [[]])[0]

            if not distances:
                print("Ничего не найдено.")
                continue

            print("\n" + "-" * 55)
            print("Ответы из базы знаний:")

            for i in range(len(distances)):
                score = distances[i]
                text = documents[i]
                url = metadatas[i].get('url', 'URL не указан')

                # Добавляем цветовой маркер в зависимости от дистанции (чем меньше, тем точнее)
                if score < 0.20:
                    confidence = "Высокая"
                elif score < 0.35:
                    confidence = "Средняя"
                else:
                    confidence = "Низкая (возможно, не по теме)"

                print(f"\nВариант {i + 1} | Уверенность: {confidence} (score: {score:.4f})")
                print(f"Ссылка: {url}")
                print(f"\n{text}")
                print("-" * 55)

        except KeyboardInterrupt:
            # Обработка остановки через Ctrl+C
            print("\n\nПроцесс прерван пользователем. Завершение работы.")
            break
        except Exception as e:
            print(f"\nПроизошла непредвиденная ошибка: {e}")


if __name__ == "__main__":
    run_chat()