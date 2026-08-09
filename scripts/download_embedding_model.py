import sys
from huggingface_hub import snapshot_download
from huggingface_hub.utils import enable_progress_bars

from app.config import settings




# Принудительно включаем отображение шкалы загрузки для файлов (tqdm)
enable_progress_bars()


def download():

    model_name = settings.EMBEDDING_MODEL_NAME
    save_dir = settings.EMBEDDING_MODEL_DIR

    print(f"Загрузка модели '{model_name}' в директорию: {save_dir}...")
    print("Если загрузка зависла, нажмите Ctrl+C и перезапустите скрипт — скачивание возобновится.\n")

    try:
        snapshot_download(
            repo_id=model_name,
            local_dir=save_dir,
        )
        print(f"Модель '{model_name}' успешно загружена и готова к работе!")

    except KeyboardInterrupt:
        print("Загрузка прервана пользователем (Ctrl+C).")
        print("Прогресс сохранен. При следующем запуске скачивание продолжится с места остановки.")
        sys.exit(130)

    except Exception as e:
        print(f"Ошибка при скачивании модели: {e}")
        sys.exit(1)


if __name__ == "__main__":
    download()