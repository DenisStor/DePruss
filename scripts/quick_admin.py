#!/usr/bin/env python3
"""Быстрое создание админа без интерактивного ввода"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import async_session, init_db
from app.models import AdminUser
from app.services.auth import get_password_hash


async def create_admin():
    await init_db()

    async with async_session() as session:
        admin = AdminUser(
            username="admin",
            password_hash=get_password_hash("admin123")
        )
        session.add(admin)
        await session.commit()
        print("✅ Админ создан: admin / admin123")


if __name__ == "__main__":
    asyncio.run(create_admin())
