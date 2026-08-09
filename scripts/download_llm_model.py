import sys
import json
import requests

from app.config import settings
from app.logger import logger
from app.rag_service.exceptions import OllamaConnectionError, OllamaDownloadError




def pull_ollama_model():
    model_name = settings.LLM_MODEL
    api_url = f"{settings.OLLAMA_BASE_URL}/api/pull"

    logger.info(f"Инициализация загрузки модели '{model_name}' через Ollama...")
    logger.debug(f"Эндпоинт загрузки: {api_url}")

    payload = {"name": model_name, "stream": True}


    try:

        # timeout=(10, None) -> 10 сек на подключение, бесконечно на само скачивание
        # stream=True позволяет получать данные по мере скачивания (chunk by chunk)
        with requests.post(api_url, json=payload, stream=True, timeout=(10, None)) as response:

            # Если вернулась ошибка от API (например 404, если модель не найдена на серверах)
            if response.status_code != 200:
                logger.error(f"Ollama вернула код {response.status_code}: {response.text}")
                raise OllamaDownloadError(f"Ошибка API Ollama (Код {response.status_code}).")

            for line in response.iter_lines():

                if not line: continue

                # Ollama возвращает прогресс в виде JSON-строк
                data = json.loads(line)
                status = data.get("status", "")

                # Если есть данные о байтах, рисуем проценты
                if "total" in data and "completed" in data:
                    total_bytes = data["total"]
                    completed_bytes = data["completed"]

                    # Перевод в гигабайты для красивого отображения
                    total_gb = total_bytes / (1024 ** 3)
                    completed_gb = completed_bytes / (1024 ** 3)

                    percent = (completed_bytes / total_bytes) * 100

                    # \r перезаписывает текущую строку в консоли, создавая эффект анимации
                    sys.stdout.write(
                        f"\r[{percent:5.1f}%] {status} | {completed_gb:.2f} GB / {total_gb:.2f} GB"
                    )
                    sys.stdout.flush()
                else:
                    # Если это просто текстовый статус (например, "pulling manifest")
                    # Текстовые статусы вроде "pulling manifest", затираем старую строку пробелами
                    sys.stdout.write(f"\r{status}" + " " * 40)
                    sys.stdout.flush()

            # Делаем перенос строки после завершения анимации
            logger.info(f"\n\nМодель '{model_name}' успешно загружена и инициализирована в Ollama.")


    except requests.exceptions.ConnectionError as e:
        logger.error(f"\nСбой подключения к Ollama по адресу {settings.OLLAMA_BASE_URL}: {e}")
        raise OllamaConnectionError("Не удалось подключиться к Ollama. Убедитесь, что служба запущена.") from e

    except requests.exceptions.Timeout as e:
        logger.error("\nПревышено время ожидания при подключении к Ollama.")
        raise OllamaConnectionError("Таймаут подключения к Ollama.") from e

    except KeyboardInterrupt:
        logger.warning("Процесс загрузки прерван пользователем (KeyboardInterrupt). Прогресс будет сохранен Ollama.")
        sys.exit(130)

    except Exception as e:
        logger.error(f"\nНепредвиденная ошибка при скачивании модели: {e}", exc_info=True)
        raise OllamaDownloadError(f"Неизвестная ошибка: {e}") from e


if __name__ == "__main__":
    pull_ollama_model()