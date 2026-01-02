"""REST API endpoints for categories - paginated list, inline edit."""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from slugify import slugify
from typing import Optional

from app.database import get_db
from app.models import Category, Dish, AdminUser
from app.services.auth import get_current_admin
from app.services.audit import AuditService, model_to_dict
from app.schemas.pagination import (
    PaginatedResponse, SortOrder, CategoryListItem, InlineEditResponse
)

router = APIRouter()


@router.get("/api/categories")
async def api_categories_list(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_order: SortOrder = Query(SortOrder.asc),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get categories list with pagination."""
    query = select(Category)

    if search:
        query = query.where(
            or_(
                Category.name.ilike(f"%{search}%"),
                Category.description.ilike(f"%{search}%")
            )
        )
    if is_active is not None:
        query = query.where(Category.is_active == is_active)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    sort_column = getattr(Category, sort_by, None) if sort_by else Category.sort_order
    if sort_column is None:
        sort_column = Category.sort_order
    if sort_order == SortOrder.desc:
        sort_column = sort_column.desc()
    query = query.order_by(sort_column)

    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    categories = result.scalars().all()

    if categories:
        category_ids = [c.id for c in categories]
        dish_counts_result = await db.execute(
            select(Dish.category_id, func.count(Dish.id).label('count'))
            .where(Dish.category_id.in_(category_ids))
            .group_by(Dish.category_id)
        )
        dish_counts = {row.category_id: row.count for row in dish_counts_result}
    else:
        dish_counts = {}

    items = [
        CategoryListItem(
            id=c.id,
            name=c.name,
            slug=c.slug,
            description=c.description,
            is_active=c.is_active,
            sort_order=c.sort_order,
            dishes_count=dish_counts.get(c.id, 0)
        )
        for c in categories
    ]

    return PaginatedResponse.create(items=items, total=total, page=page, per_page=per_page)


@router.patch("/api/categories/{cat_id}")
async def api_category_inline_edit(
    cat_id: int,
    data: dict = Body(...),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Inline edit category fields."""
    result = await db.execute(select(Category).where(Category.id == cat_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")

    old_data = model_to_dict(category)

    allowed_fields = {'name', 'description', 'is_active', 'sort_order'}

    updated_fields = {}
    for field, value in data.items():
        if field in allowed_fields:
            setattr(category, field, value)
            updated_fields[field] = value

    if not updated_fields:
        raise HTTPException(status_code=400, detail="Нет разрешённых полей для обновления")

    if 'name' in updated_fields:
        category.slug = slugify(category.name, lowercase=True)

    new_data = model_to_dict(category)
    category_name = category.name
    category_id = category.id

    audit_service = AuditService(db)
    audit_result = await audit_service.log_update(
        admin_user_id=admin.id,
        entity_type='category',
        entity_id=category_id,
        entity_name=category_name,
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
