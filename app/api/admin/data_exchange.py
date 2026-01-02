"""Data exchange routes for admin panel - import/export."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Category, Dish, AdminUser
from app.services.auth import get_current_admin
from .dependencies import templates

router = APIRouter()


@router.get("/data-exchange", response_class=HTMLResponse)
async def data_exchange_page(
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Page for data import/export."""
    # Get counts
    dishes_count = await db.scalar(select(func.count(Dish.id)))
    categories_count = await db.scalar(select(func.count(Category.id)))

    return templates.TemplateResponse(
        "admin/data_exchange.html",
        {
            "request": request,
            "admin": admin,
            "dishes_count": dishes_count or 0,
            "categories_count": categories_count or 0
        }
    )
