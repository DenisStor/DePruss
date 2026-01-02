from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import Category, Dish

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, db: AsyncSession = Depends(get_db)):
    """Главная страница с меню"""
    result = await db.execute(
        select(Category)
        .where(Category.is_active == True)
        .options(selectinload(Category.dishes))
        .order_by(Category.sort_order)
    )
    categories = result.scalars().all()

    # Сортируем блюда: доступные первыми, недоступные в конце
    for category in categories:
        category.dishes.sort(key=lambda x: (not x.is_available, x.sort_order))

    return templates.TemplateResponse(
        "pages/index.html",
        {
            "request": request,
            "categories": categories,
            "title": "Кухня Де Прусс"
        }
    )


@router.get("/dish/{slug}", response_class=HTMLResponse)
async def dish_detail(request: Request, slug: str, db: AsyncSession = Depends(get_db)):
    """Страница с деталями блюда"""
    result = await db.execute(
        select(Dish)
        .where(Dish.slug == slug)
        .options(selectinload(Dish.category))
    )
    dish = result.scalar_one_or_none()

    if not dish:
        raise HTTPException(status_code=404, detail="Блюдо не найдено")

    return templates.TemplateResponse(
        "pages/dish.html",
        {
            "request": request,
            "dish": dish,
            "title": f"{dish.name} — Кухня Де Прусс"
        }
    )


@router.get("/api/menu")
async def api_menu(db: AsyncSession = Depends(get_db)):
    """JSON API для меню (для JS)"""
    result = await db.execute(
        select(Category)
        .where(Category.is_active == True)
        .options(selectinload(Category.dishes))
        .order_by(Category.sort_order)
    )
    categories = result.scalars().all()

    # Сортируем блюда: доступные первыми, недоступные в конце
    for category in categories:
        category.dishes.sort(key=lambda x: (not x.is_available, x.sort_order))

    return {
        "categories": [
            {
                "id": cat.id,
                "name": cat.name,
                "slug": cat.slug,
                "dishes": [
                    {
                        "id": d.id,
                        "name": d.name,
                        "slug": d.slug,
                        "price": float(d.price),
                        "img": d.image_small,
                        "available": d.is_available
                    }
                    for d in cat.dishes  # Показываем все блюда, включая недоступные
                ]
            }
            for cat in categories
        ]
    }


@router.get("/api/dish/{dish_id}")
async def api_dish(dish_id: int, db: AsyncSession = Depends(get_db)):
    """JSON API для деталей блюда"""
    result = await db.execute(
        select(Dish)
        .where(Dish.id == dish_id)
        .options(selectinload(Dish.category))
    )
    dish = result.scalar_one_or_none()

    if not dish:
        raise HTTPException(status_code=404)

    return {
        "id": dish.id,
        "name": dish.name,
        "slug": dish.slug,
        "description": dish.description,
        "price": float(dish.price),
        "weight": dish.weight,
        "calories": dish.calories,
        "images": {
            "thumbnail": dish.image_thumbnail,
            "small": dish.image_small,
            "medium": dish.image_medium,
            "large": dish.image_large
        },
        "category": {
            "id": dish.category.id,
            "name": dish.category.name,
            "slug": dish.category.slug
        }
    }
