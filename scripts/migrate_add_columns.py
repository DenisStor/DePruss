#!/usr/bin/env python3
"""
Миграция: добавление новых колонок для оптимизации изображений.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import async_session, init_db


async def migrate():
    """Добавляет новые колонки для оптимизации изображений."""
    print("Добавление новых колонок в таблицу dishes...")

    await init_db()

    columns_to_add = [
        ("image_tiny_base64", "TEXT"),
        ("image_dominant_color", "VARCHAR(10)"),
        ("image_small_avif", "VARCHAR(500)"),
        ("image_medium_avif", "VARCHAR(500)"),
        ("image_large_avif", "VARCHAR(500)"),
    ]

    async with async_session() as session:
        for column_name, column_type in columns_to_add:
            try:
                await session.execute(
                    text(f"ALTER TABLE dishes ADD COLUMN {column_name} {column_type}")
                )
                await session.commit()
                print(f"  ✅ Добавлена колонка: {column_name}")
            except Exception as e:
                if "duplicate column" in str(e).lower():
                    print(f"  ⏭️  Колонка уже существует: {column_name}")
                else:
                    print(f"  ❌ Ошибка для {column_name}: {e}")
                await session.rollback()

    print("\n✅ Миграция завершена!")


if __name__ == "__main__":
    asyncio.run(migrate())
