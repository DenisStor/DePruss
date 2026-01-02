#!/usr/bin/env python3
"""
Скрипт миграции изображений для оптимизации под медленный интернет.
Добавляет tiny_base64, dominant_color и AVIF версии для существующих блюд.

Использование:
    python scripts/migrate_images_optimization.py
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import async_session, init_db
from app.models.dish import Dish
from app.services.image_processor import ImageProcessor, AVIF_SUPPORTED


async def migrate_images():
    """Регенерирует оптимизационные данные для всех блюд с изображениями."""

    print("=" * 60)
    print("Миграция изображений для оптимизации производительности")
    print("=" * 60)
    print(f"AVIF поддержка: {'Да' if AVIF_SUPPORTED else 'Нет (установите pillow-avif-plugin)'}")
    print()

    await init_db()

    async with async_session() as session:
        # Получаем все блюда с изображениями
        result = await session.execute(
            select(Dish).where(Dish.image_small.isnot(None))
        )
        dishes = result.scalars().all()

        total = len(dishes)
        print(f"Найдено блюд с изображениями: {total}")
        print()

        success = 0
        failed = 0

        for i, dish in enumerate(dishes, 1):
            print(f"[{i}/{total}] {dish.name} (ID: {dish.id})...", end=" ")

            try:
                # Регенерируем оптимизационные данные
                paths = ImageProcessor.regenerate_optimization(dish.id)

                if paths:
                    # Обновляем поля
                    dish.image_tiny_base64 = paths.get("tiny_base64")
                    dish.image_dominant_color = paths.get("dominant_color")
                    dish.image_small_avif = paths.get("small_avif")
                    dish.image_medium_avif = paths.get("medium_avif")
                    dish.image_large_avif = paths.get("large_avif")

                    await session.commit()

                    # Статистика
                    avif_count = sum(1 for k in paths if k.endswith("_avif") and paths[k])
                    tiny_size = len(paths.get("tiny_base64", "")) if paths.get("tiny_base64") else 0

                    print(f"OK (tiny: {tiny_size} bytes, AVIF: {avif_count} files)")
                    success += 1
                else:
                    print("SKIP (нет исходных файлов)")

            except Exception as e:
                print(f"ERROR: {e}")
                failed += 1
                await session.rollback()

        print()
        print("=" * 60)
        print(f"Завершено: {success} успешно, {failed} ошибок")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(migrate_images())
