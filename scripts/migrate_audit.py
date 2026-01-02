#!/usr/bin/env python3
"""
Миграция для создания таблицы audit_logs
Запуск: python scripts/migrate_audit.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine, Base
from app.models import AuditLog  # Импортируем для регистрации модели


async def check_table_exists(conn, table_name: str) -> bool:
    """Проверяет существование таблицы в SQLite"""
    result = await conn.execute(
        text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    )
    return result.scalar() is not None


async def migrate():
    print("🔄 Запуск миграции для audit_logs...")

    async with engine.begin() as conn:
        # Проверяем, существует ли таблица
        table_exists = await check_table_exists(conn, 'audit_logs')

        if table_exists:
            print("ℹ️  Таблица audit_logs уже существует")
            return

        # Создаём только таблицу audit_logs
        await conn.run_sync(
            lambda sync_conn: AuditLog.__table__.create(sync_conn, checkfirst=True)
        )

        print("✅ Таблица audit_logs создана успешно!")

        # Создаём индексы
        print("📇 Создание индексов...")
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs(action)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_audit_logs_entity_type ON audit_logs(entity_type)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_audit_logs_entity_id ON audit_logs(entity_id)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs(created_at)"
        ))
        print("✅ Индексы созданы")


async def main():
    await migrate()
    print("🎉 Миграция завершена!")


if __name__ == "__main__":
    asyncio.run(main())
