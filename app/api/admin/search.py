"""Global search routes for admin panel."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Category, Dish, AdminUser
from app.services.auth import get_current_admin

router = APIRouter()


@router.get("/api/search")
async def api_global_search(
    q: str = Query(..., min_length=2),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Глобальный поиск по блюдам и категориям"""
    search_term = f"%{q}%"

    # Поиск блюд
    dishes_result = await db.execute(
        select(Dish)
        .options(selectinload(Dish.category))
        .where(
            or_(
                Dish.name.ilike(search_term),
                Dish.description.ilike(search_term)
            )
        )
        .limit(10)
    )
    dishes = dishes_result.scalars().all()

    # Поиск категорий
    categories_result = await db.execute(
        select(Category)
        .where(
            or_(
                Category.name.ilike(search_term),
                Category.description.ilike(search_term)
            )
        )
        .limit(5)
    )
    categories = categories_result.scalars().all()

    return {
        "dishes": [
            {
                "id": d.id,
                "name": d.name,
                "category": d.category.name if d.category else ""
            }
            for d in dishes
        ],
        "categories": [
            {"id": c.id, "name": c.name}
            for c in categories
        ]
    }
