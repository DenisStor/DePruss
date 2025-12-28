#!/usr/bin/env python3
"""
Скрипт для создания администратора.
Запуск: python scripts/create_admin.py
"""

import asyncio
import sys
import os

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import async_session, init_db
from app.models import AdminUser
from app.services.auth import get_password_hash
from sqlalchemy import select


async def create_admin():
    # Инициализируем БД
    await init_db()

    async with async_session() as session:
        # Проверяем, есть ли уже админ
        result = await session.execute(select(AdminUser))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Администратор уже существует: {existing.username}")
            choice = input("Создать нового? (y/n): ")
            if choice.lower() != 'y':
                return

        # Запрашиваем данные
        print("\n--- Создание администратора ---")
        username = input("Логин: ").strip()
        if not username:
            print("Ошибка: логин не может быть пустым")
            return

        password = input("Пароль: ").strip()
        if len(password) < 4:
            print("Ошибка: пароль должен быть не менее 4 символов")
            return

        # Создаем админа
        admin = AdminUser(
            username=username,
            password_hash=get_password_hash(password)
        )
        session.add(admin)
        await session.commit()

        print(f"\n✅ Администратор '{username}' создан!")
        print("   Теперь можете войти в админку: /admin/login")


if __name__ == "__main__":
    asyncio.run(create_admin())
