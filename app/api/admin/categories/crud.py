"""CRUD operations for categories - forms and create/edit/delete."""
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from slugify import slugify

from app.database import get_db
from app.models import Category, Dish, AdminUser
from app.services.auth import get_current_admin
from ..dependencies import templates

router = APIRouter()


@router.get("/categories", response_class=HTMLResponse)
async def categories_list(
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Category).order_by(Category.sort_order))
    categories = result.scalars().all()

    return templates.TemplateResponse(
        "admin/categories.html",
        {"request": request, "admin": admin, "categories": categories}
    )


@router.get("/categories/new", response_class=HTMLResponse)
async def category_new(
    request: Request,
    admin: AdminUser = Depends(get_current_admin)
):
    return templates.TemplateResponse(
        "admin/category_form.html",
        {"request": request, "admin": admin, "category": None}
    )


@router.post("/categories")
async def category_create(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    sort_order: int = Form(0),
    is_active: bool = Form(True),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    category = Category(
        name=name,
        slug=slugify(name, lowercase=True),
        description=description,
        sort_order=sort_order,
        is_active=is_active
    )
    db.add(category)
    await db.commit()
    return RedirectResponse(url="/admin/categories", status_code=302)


@router.get("/categories/{cat_id}/edit", response_class=HTMLResponse)
async def category_edit(
    request: Request,
    cat_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Category).where(Category.id == cat_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404)

    return templates.TemplateResponse(
        "admin/category_form.html",
        {"request": request, "admin": admin, "category": category}
    )


@router.post("/categories/{cat_id}")
async def category_update(
    cat_id: int,
    name: str = Form(...),
    description: str = Form(""),
    sort_order: int = Form(0),
    is_active: bool = Form(False),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Category).where(Category.id == cat_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404)

    category.name = name
    category.slug = slugify(name, lowercase=True)
    category.description = description
    category.sort_order = sort_order
    category.is_active = is_active
    await db.commit()

    return RedirectResponse(url="/admin/categories", status_code=302)


@router.post("/categories/{cat_id}/delete")
async def category_delete(
    cat_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Dish).where(Dish.category_id == cat_id))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Нельзя удалить категорию с блюдами")

    await db.execute(delete(Category).where(Category.id == cat_id))
    await db.commit()
    return RedirectResponse(url="/admin/categories", status_code=302)
