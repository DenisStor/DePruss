import os
import time
from pathlib import Path
from PIL import Image
from io import BytesIO
from app.config import get_settings

settings = get_settings()


class ImageProcessor:
    """Обработка изображений для оптимизации под 3G"""

    SIZES = {
        "thumbnail": (150, 150),    # Blur-up placeholder
        "small": (600, 600),        # Карточки на обычных экранах
        "medium": (1200, 1200),     # Карточки на retina / детальная
        "large": (2000, 2000),      # Полный размер для zoom
    }

    @staticmethod
    def process_and_save(
        file_content: bytes,
        dish_id: int,
        filename: str
    ) -> dict[str, str]:
        """
        Обрабатывает загруженное изображение и создает 4 размера в WebP.
        Возвращает словарь с путями к файлам.
        """
        dish_dir = Path(settings.upload_dir) / str(dish_id)
        dish_dir.mkdir(parents=True, exist_ok=True)

        # Уникальный timestamp для cache-busting
        version = int(time.time())

        # Открываем исходное изображение
        img = Image.open(BytesIO(file_content))

        # Конвертируем в RGB если нужно (для PNG с альфа-каналом)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background

        paths = {}

        for size_name, dimensions in ImageProcessor.SIZES.items():
            # Создаем копию и масштабируем
            img_copy = img.copy()
            img_copy.thumbnail(dimensions, Image.Resampling.LANCZOS)

            # Путь для сохранения с версией для cache-busting
            file_path = dish_dir / f"{size_name}_{version}.webp"
            relative_path = f"/{settings.upload_dir}/{dish_id}/{size_name}_{version}.webp"

            # Настройки качества для разных размеров (высокое качество)
            quality = {
                "thumbnail": 85,
                "small": 92,
                "medium": 94,
                "large": 96,
            }

            # Сохраняем в WebP
            img_copy.save(
                file_path,
                "WEBP",
                quality=quality[size_name],
                method=6  # Максимальное сжатие
            )

            paths[size_name] = relative_path

        return paths

    @staticmethod
    def delete_images(dish_id: int) -> None:
        """Удаляет все изображения блюда"""
        dish_dir = Path(settings.upload_dir) / str(dish_id)
        if dish_dir.exists():
            for file in dish_dir.iterdir():
                file.unlink()
            dish_dir.rmdir()
