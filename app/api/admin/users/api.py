"""REST API endpoints for admin users - paginated list, toggle-active."""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.database import get_db
from app.models import AdminUser
from app.services.auth import get_current_admin
from app.schemas.pagination import PaginatedResponse, AdminUserListItem

router = APIRouter()


@router.post("/users/{user_id}/toggle-active")
async def user_toggle_active(
    user_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Toggle user active status."""
    result = await db.execute(select(AdminUser).where(AdminUser.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404)

    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Нельзя деактивировать свой аккаунт")

    user.is_active = not user.is_active
    await db.commit()
    return RedirectResponse(url="/admin/users", status_code=302)


@router.get("/api/users")
async def api_users_list(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get admin users list with pagination."""
    query = select(AdminUser)

    if search:
        query = query.where(AdminUser.username.ilike(f"%{search}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(AdminUser.id)

    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    users = result.scalars().all()

    items = [
        AdminUserListItem(
            id=u.id,
            username=u.username,
            is_active=u.is_active,
            last_login=u.last_login.isoformat() if u.last_login else None,
            created_at=u.created_at.isoformat() if u.created_at else ""
        )
        for u in users
    ]

    return PaginatedResponse.create(items=items, total=total, page=page, per_page=per_page)
