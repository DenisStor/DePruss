import os
import time
import base64
import warnings
from pathlib import Path
from PIL import Image, ImageFilter
from io import BytesIO
from app.config import get_settings

settings = get_settings()

# Check AVIF support
try:
    import pillow_avif  # noqa: F401
    AVIF_SUPPORTED = True
except ImportError:
    AVIF_SUPPORTED = False
    warnings.warn("pillow-avif-plugin not installed, AVIF generation disabled")


class ImageProcessor:
    """Обработка изображений для оптимизации под медленный интернет"""

    SIZES = {
        "tiny": (20, 20),           # LQIP placeholder (~200 bytes)
        "thumbnail": (150, 150),    # Blur-up placeholder
        "small": (600, 600),        # Карточки на обычных экранах
        "medium": (1200, 1200),     # Карточки на retina / детальная
        "large": (2000, 2000),      # Полный размер для zoom
    }

    # Качество для WebP
    WEBP_QUALITY = {
        "tiny": 60,
        "thumbnail": 85,
        "small": 92,
        "medium": 94,
        "large": 96,
    }

    # Качество для AVIF (генерируем только для small, medium, large)
    AVIF_QUALITY = {
        "small": 75,
        "medium": 80,
        "large": 85,
    }

    @staticmethod
    def _prepare_image(file_content: bytes) -> Image.Image:
        """Открывает и конвертирует изображение в RGB"""
        img = Image.open(BytesIO(file_content))

        # Конвертируем в RGB если нужно (для PNG с альфа-каналом)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background

        return img

    @staticmethod
    def generate_tiny_base64(img: Image.Image) -> str:
        """
        Генерирует inline base64 для tiny placeholder.
        Возвращает data URI (~200-400 bytes).
        """
        tiny = img.copy()
        tiny.thumbnail((20, 20), Image.Resampling.LANCZOS)

        # Добавляем небольшой blur для сглаживания артефактов
        tiny = tiny.filter(ImageFilter.GaussianBlur(radius=1))

        buffer = BytesIO()
        tiny.save(buffer, "WEBP", quality=50, method=6)
        b64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return f"data:image/webp;base64,{b64_data}"

    @staticmethod
    def extract_dominant_color(img: Image.Image) -> str:
        """
        Извлекает доминантный цвет изображения.
        Возвращает hex-код (#RRGGBB).
        """
        # Уменьшаем до маленького размера для быстрого анализа
        small = img.copy()
        small.thumbnail((50, 50), Image.Resampling.LANCZOS)

        # Получаем все пиксели
        pixels = list(small.getdata())

        # Вычисляем средний цвет (простой подход)
        r_total = g_total = b_total = 0
        count = len(pixels)

        for pixel in pixels:
            r_total += pixel[0]
            g_total += pixel[1]
            b_total += pixel[2]

        r_avg = r_total // count
        g_avg = g_total // count
        b_avg = b_total // count

        return f"#{r_avg:02x}{g_avg:02x}{b_avg:02x}"

    @staticmethod
    def process_and_save(
        file_content: bytes,
        dish_id: int,
        filename: str
    ) -> dict[str, str]:
        """
        Обрабатывает загруженное изображение и создает все размеры.
        Возвращает словарь с путями к файлам и данными для progressive loading.
        """
        dish_dir = Path(settings.upload_dir) / str(dish_id)
        dish_dir.mkdir(parents=True, exist_ok=True)

        # Уникальный timestamp для cache-busting
        version = int(time.time())

        # Открываем исходное изображение
        img = ImageProcessor._prepare_image(file_content)

        paths = {}

        # Генерируем tiny base64 и dominant color
        paths["tiny_base64"] = ImageProcessor.generate_tiny_base64(img)
        paths["dominant_color"] = ImageProcessor.extract_dominant_color(img)

        # Генерируем все размеры WebP
        for size_name, dimensions in ImageProcessor.SIZES.items():
            # Пропускаем tiny - он уже как base64
            if size_name == "tiny":
                continue

            # Создаем копию и масштабируем
            img_copy = img.copy()
            img_copy.thumbnail(dimensions, Image.Resampling.LANCZOS)

            # Путь для сохранения WebP
            webp_path = dish_dir / f"{size_name}_{version}.webp"
            relative_webp = f"/{settings.upload_dir}/{dish_id}/{size_name}_{version}.webp"

            # Сохраняем WebP
            img_copy.save(
                webp_path,
                "WEBP",
                quality=ImageProcessor.WEBP_QUALITY[size_name],
                method=6  # Максимальное сжатие
            )
            paths[size_name] = relative_webp

            # Генерируем AVIF для small, medium, large
            if AVIF_SUPPORTED and size_name in ImageProcessor.AVIF_QUALITY:
                avif_path = dish_dir / f"{size_name}_{version}.avif"
                relative_avif = f"/{settings.upload_dir}/{dish_id}/{size_name}_{version}.avif"

                try:
                    img_copy.save(
                        avif_path,
                        "AVIF",
                        quality=ImageProcessor.AVIF_QUALITY[size_name],
                    )
                    paths[f"{size_name}_avif"] = relative_avif
                except Exception as e:
                    warnings.warn(f"Failed to save AVIF for {size_name}: {e}")

        return paths

    @staticmethod
    def regenerate_optimization(dish_id: int) -> dict[str, str] | None:
        """
        Регенерирует tiny_base64, dominant_color и AVIF для существующего блюда.
        Читает large файл и генерирует оптимизационные данные.
        """
        dish_dir = Path(settings.upload_dir) / str(dish_id)
        if not dish_dir.exists():
            return None

        # Находим large или medium файл
        large_files = list(dish_dir.glob("large_*.webp"))
        medium_files = list(dish_dir.glob("medium_*.webp"))

        source_file = None
        if large_files:
            source_file = large_files[0]
        elif medium_files:
            source_file = medium_files[0]
        else:
            return None

        # Читаем исходное изображение
        with open(source_file, 'rb') as f:
            file_content = f.read()

        img = ImageProcessor._prepare_image(file_content)

        paths = {}

        # Генерируем tiny base64 и dominant color
        paths["tiny_base64"] = ImageProcessor.generate_tiny_base64(img)
        paths["dominant_color"] = ImageProcessor.extract_dominant_color(img)

        # Извлекаем версию из имени файла
        version = source_file.stem.split('_')[-1]

        # Генерируем AVIF для существующих WebP
        if AVIF_SUPPORTED:
            for size_name in ["small", "medium", "large"]:
                webp_files = list(dish_dir.glob(f"{size_name}_*.webp"))
                if not webp_files:
                    continue

                webp_file = webp_files[0]
                webp_version = webp_file.stem.split('_')[-1]

                # Читаем WebP и конвертируем в AVIF
                with open(webp_file, 'rb') as f:
                    webp_content = f.read()

                webp_img = Image.open(BytesIO(webp_content))
                if webp_img.mode != 'RGB':
                    webp_img = webp_img.convert('RGB')

                avif_path = dish_dir / f"{size_name}_{webp_version}.avif"
                relative_avif = f"/{settings.upload_dir}/{dish_id}/{size_name}_{webp_version}.avif"

                try:
                    webp_img.save(
                        avif_path,
                        "AVIF",
                        quality=ImageProcessor.AVIF_QUALITY[size_name],
                    )
                    paths[f"{size_name}_avif"] = relative_avif
                except Exception as e:
                    warnings.warn(f"Failed to save AVIF for {size_name}: {e}")

        return paths

    @staticmethod
    def delete_images(dish_id: int) -> None:
        """Удаляет все изображения блюда"""
        dish_dir = Path(settings.upload_dir) / str(dish_id)
        if dish_dir.exists():
            for file in dish_dir.iterdir():
                file.unlink()
            dish_dir.rmdir()

    @staticmethod
    def copy_images(source_dish_id: int, target_dish_id: int) -> dict[str, str] | None:
        """Копирует изображения из одного блюда в другое"""
        import shutil

        source_dir = Path(settings.upload_dir) / str(source_dish_id)
        if not source_dir.exists():
            return None

        target_dir = Path(settings.upload_dir) / str(target_dish_id)
        target_dir.mkdir(parents=True, exist_ok=True)

        # Новый timestamp для cache-busting
        version = int(time.time())

        paths = {}

        # Копируем WebP файлы
        for size_name in ["thumbnail", "small", "medium", "large"]:
            source_files = list(source_dir.glob(f"{size_name}_*.webp"))
            if not source_files:
                continue

            source_file = source_files[0]
            target_file = target_dir / f"{size_name}_{version}.webp"
            relative_path = f"/{settings.upload_dir}/{target_dish_id}/{size_name}_{version}.webp"

            shutil.copy2(source_file, target_file)
            paths[size_name] = relative_path

        # Копируем AVIF файлы
        for size_name in ["small", "medium", "large"]:
            source_files = list(source_dir.glob(f"{size_name}_*.avif"))
            if not source_files:
                continue

            source_file = source_files[0]
            target_file = target_dir / f"{size_name}_{version}.avif"
            relative_path = f"/{settings.upload_dir}/{target_dish_id}/{size_name}_{version}.avif"

            shutil.copy2(source_file, target_file)
            paths[f"{size_name}_avif"] = relative_path

        # Генерируем tiny и dominant color для нового блюда
        large_files = list(target_dir.glob("large_*.webp"))
        if large_files:
            with open(large_files[0], 'rb') as f:
                file_content = f.read()
            img = ImageProcessor._prepare_image(file_content)
            paths["tiny_base64"] = ImageProcessor.generate_tiny_base64(img)
            paths["dominant_color"] = ImageProcessor.extract_dominant_color(img)

        return paths if paths else None
