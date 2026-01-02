"""REST API endpoints for dishes - paginated list, inline edit."""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from slugify import slugify
from typing import Optional

from app.database import get_db
from app.models import Dish, AdminUser
from app.services.auth import get_current_admin
from app.services.audit import AuditService, model_to_dict
from app.schemas.pagination import (
    PaginatedResponse, SortOrder, DishListItem, InlineEditResponse
)

router = APIRouter()


@router.get("/api/dishes")
async def api_dishes_list(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    is_available: Optional[bool] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_order: SortOrder = Query(SortOrder.asc),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get dishes list with pagination and filters."""
    query = select(Dish).options(selectinload(Dish.category))

    if search:
        query = query.where(
            or_(
                Dish.name.ilike(f"%{search}%"),
                Dish.description.ilike(f"%{search}%")
            )
        )
    if category_id is not None:
        query = query.where(Dish.category_id == category_id)
    if is_available is not None:
        query = query.where(Dish.is_available == is_available)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    sort_column = getattr(Dish, sort_by, None) if sort_by else Dish.sort_order
    if sort_column is None:
        sort_column = Dish.sort_order
    if sort_order == SortOrder.desc:
        sort_column = sort_column.desc()
    query = query.order_by(sort_column)

    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    dishes = result.scalars().all()

    items = [
        DishListItem(
            id=d.id,
            name=d.name,
            slug=d.slug,
            price=d.price,
            weight=d.weight,
            calories=d.calories,
            is_available=d.is_available,
            sort_order=d.sort_order,
            image_thumbnail=d.image_thumbnail,
            category_id=d.category_id,
            category_name=d.category.name if d.category else ""
        )
        for d in dishes
    ]

    return PaginatedResponse.create(items=items, total=total, page=page, per_page=per_page)


@router.patch("/api/dishes/{dish_id}")
async def api_dish_inline_edit(
    dish_id: int,
    data: dict = Body(...),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Inline edit dish fields."""
    result = await db.execute(select(Dish).where(Dish.id == dish_id))
    dish = result.scalar_one_or_none()
    if not dish:
        raise HTTPException(status_code=404, detail="Блюдо не найдено")

    old_data = model_to_dict(dish)

    allowed_fields = {'name', 'price', 'weight', 'calories', 'is_available', 'sort_order'}

    updated_fields = {}
    for field, value in data.items():
        if field in allowed_fields:
            setattr(dish, field, value)
            updated_fields[field] = value

    if not updated_fields:
        raise HTTPException(status_code=400, detail="Нет разрешённых полей для обновления")

    if 'name' in updated_fields:
        dish.slug = slugify(dish.name, lowercase=True)

    new_data = model_to_dict(dish)
    dish_name = dish.name
    dish_id_val = dish.id

    audit_service = AuditService(db)
    audit_result = await audit_service.log_update(
        admin_user_id=admin.id,
        entity_type='dish',
        entity_id=dish_id_val,
        entity_name=dish_name,
        old_data=old_data,
        new_data=new_data
    )

    if audit_result is None:
        await db.commit()

    return InlineEditResponse(
        success=True,
        field=list(updated_fields.keys())[0] if len(updated_fields) == 1 else "multiple",
        value=list(updated_fields.values())[0] if len(updated_fields) == 1 else updated_fields,
        message="Сохранено"
    )
