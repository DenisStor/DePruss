"""CRUD operations for admin users - forms and create/edit."""
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import AdminUser
from app.services.auth import get_current_admin, get_password_hash
from ..dependencies import templates

router = APIRouter()


@router.get("/users", response_class=HTMLResponse)
async def users_list(
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AdminUser).order_by(AdminUser.id))
    users = result.scalars().all()

    return templates.TemplateResponse(
        "admin/users.html",
        {"request": request, "admin": admin, "users": users}
    )


@router.get("/users/new", response_class=HTMLResponse)
async def user_new(
    request: Request,
    admin: AdminUser = Depends(get_current_admin)
):
    return templates.TemplateResponse(
        "admin/user_form.html",
        {"request": request, "admin": admin, "user": None}
    )


@router.post("/users")
async def user_create(
    username: str = Form(...),
    password: str = Form(...),
    is_active: bool = Form(True),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    existing = await db.execute(select(AdminUser).where(AdminUser.username == username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Пользователь с таким именем уже существует")

    user = AdminUser(
        username=username,
        password_hash=get_password_hash(password),
        is_active=is_active
    )
    db.add(user)
    await db.commit()
    return RedirectResponse(url="/admin/users", status_code=302)


@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def user_edit(
    request: Request,
    user_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AdminUser).where(AdminUser.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404)

    return templates.TemplateResponse(
        "admin/user_form.html",
        {"request": request, "admin": admin, "user": user}
    )


@router.post("/users/{user_id}")
async def user_update(
    user_id: int,
    username: str = Form(...),
    password: str = Form(""),
    is_active: bool = Form(False),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AdminUser).where(AdminUser.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404)

    if user.username != username:
        existing = await db.execute(select(AdminUser).where(AdminUser.username == username))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Пользователь с таким именем уже существует")

    user.username = username
    if password:
        user.password_hash = get_password_hash(password)
    user.is_active = is_active

    await db.commit()
    return RedirectResponse(url="/admin/users", status_code=302)
