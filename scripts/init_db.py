#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных.
Запуск: python scripts/init_db.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db


async def main():
    print("Инициализация базы данных...")
    await init_db()
    print("✅ База данных создана успешно!")
    print("   Файл: data/cafe.db")


if __name__ == "__main__":
    asyncio.run(main())
