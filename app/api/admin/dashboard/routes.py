"""Main dashboard routes for admin panel."""
from datetime import datetime
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, or_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Category, Dish, AdminUser, AuditLog
from app.services.auth import get_current_admin
from ..dependencies import templates
from .constants import ACTION_DISPLAY, ENTITY_TYPE_DISPLAY

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    # Categories with dishes for chart
    categories_result = await db.execute(
        select(Category)
        .options(selectinload(Category.dishes))
        .order_by(Category.sort_order)
    )
    categories = categories_result.scalars().all()

    # Category statistics
    cat_stats = await db.execute(
        select(
            func.count(Category.id).label('total'),
            func.sum(case((Category.is_active == True, 1), else_=0)).label('active')
        )
    )
    cat_row = cat_stats.one()
    categories_total = cat_row.total or 0
    categories_active = cat_row.active or 0
    categories_inactive = categories_total - categories_active

    # Dish statistics
    dish_stats = await db.execute(
        select(
            func.count(Dish.id).label('total'),
            func.sum(case((Dish.is_available == True, 1), else_=0)).label('available')
        )
    )
    dish_row = dish_stats.one()
    dishes_total = dish_row.total or 0
    dishes_available = dish_row.available or 0
    dishes_unavailable = dishes_total - dishes_available

    # Recent dishes
    recent_dishes_result = await db.execute(
        select(Dish)
        .options(selectinload(Dish.category))
        .order_by(Dish.updated_at.desc())
        .limit(10)
    )
    recent_dishes = recent_dishes_result.scalars().all()

    # Admin statistics
    admin_stats = await db.execute(
        select(
            func.count(AdminUser.id).label('total'),
            func.sum(case((AdminUser.is_active == True, 1), else_=0)).label('active')
        )
    )
    admin_row = admin_stats.one()
    admins_total = admin_row.total or 0
    admins_active = admin_row.active or 0

    # Data quality metrics
    dishes_no_image_result = await db.execute(
        select(func.count(Dish.id)).where(Dish.image_small.is_(None))
    )
    dishes_without_images = dishes_no_image_result.scalar() or 0

    dishes_no_desc_result = await db.execute(
        select(func.count(Dish.id)).where(
            or_(Dish.description.is_(None), Dish.description == "")
        )
    )
    dishes_without_description = dishes_no_desc_result.scalar() or 0

    dishes_no_cal_result = await db.execute(
        select(func.count(Dish.id)).where(Dish.calories.is_(None))
    )
    dishes_without_calories = dishes_no_cal_result.scalar() or 0

    # Data completeness percentage
    if dishes_total > 0:
        problems_count = dishes_without_images + dishes_without_description + dishes_without_calories
        max_problems = dishes_total * 3
        data_completeness = max(0, min(100, int(100 - (problems_count / max_problems * 100))))
    else:
        data_completeness = 100

    # Price and calories statistics
    dish_types_result = await db.execute(
        select(
            func.min(Dish.price).label('price_min'),
            func.max(Dish.price).label('price_max'),
            func.avg(Dish.price).label('price_avg'),
            func.avg(Dish.calories).label('calories_avg')
        )
    )
    dish_types_row = dish_types_result.one()
    price_min = max(0, dish_types_row.price_min or 0)
    price_max = max(0, dish_types_row.price_max or 0)
    price_avg = max(0, dish_types_row.price_avg or 0)
    calories_avg = max(0, dish_types_row.calories_avg or 0) if dish_types_row.calories_avg else None

    # Recent activity logs
    recent_logs_result = await db.execute(
        select(AuditLog)
        .options(selectinload(AuditLog.admin_user))
        .order_by(AuditLog.created_at.desc())
        .limit(10)
    )
    recent_logs = recent_logs_result.scalars().all()

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "admin": admin,
            "categories": categories,
            "categories_total": categories_total,
            "categories_active": categories_active,
            "categories_inactive": categories_inactive,
            "dishes_total": dishes_total,
            "dishes_available": dishes_available,
            "dishes_unavailable": dishes_unavailable,
            "recent_dishes": recent_dishes,
            "admins_total": admins_total,
            "admins_active": admins_active,
            "dishes_without_images": dishes_without_images,
            "dishes_without_description": dishes_without_description,
            "dishes_without_calories": dishes_without_calories,
            "data_completeness": data_completeness,
            "price_min": price_min,
            "price_max": price_max,
            "price_avg": price_avg,
            "calories_avg": calories_avg,
            "recent_logs": recent_logs,
            "action_display": ACTION_DISPLAY,
            "entity_type_display": ENTITY_TYPE_DISPLAY,
            "now": datetime.now(),
        }
    )
