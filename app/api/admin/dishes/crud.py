"""CRUD operations for dishes - forms and create/edit."""
from fastapi import APIRouter, Depends, Request, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from slugify import slugify

from app.database import get_db
from app.models import Category, Dish, AdminUser
from app.services.auth import get_current_admin
from app.services.image_processor import ImageProcessor
from ..dependencies import templates, settings

router = APIRouter()


@router.get("/dishes", response_class=HTMLResponse)
async def dishes_list(
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Dish).options(selectinload(Dish.category))
        .order_by(Dish.category_id, Dish.sort_order)
    )
    dishes = result.scalars().all()
    cat_result = await db.execute(select(Category).order_by(Category.sort_order))
    categories = cat_result.scalars().all()
    return templates.TemplateResponse(
        "admin/dishes.html",
        {"request": request, "admin": admin, "dishes": dishes, "categories": categories}
    )


@router.get("/dishes/new", response_class=HTMLResponse)
async def dish_new(
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Category).where(Category.is_active == True))
    categories = result.scalars().all()
    return templates.TemplateResponse(
        "admin/dish_form.html",
        {"request": request, "admin": admin, "dish": None, "categories": categories}
    )


@router.post("/dishes")
async def dish_create(
    request: Request, name: str = Form(...), category_id: int = Form(...),
    description: str = Form(""), price: float = Form(...), weight: str = Form(""),
    calories: str = Form(""), is_available: bool = Form(True),
    sort_order: int = Form(0), image: UploadFile = File(None),
    admin: AdminUser = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
):
    dish = Dish(
        name=name, slug=slugify(name, lowercase=True), category_id=category_id,
        description=description, price=price, weight=weight,
        calories=int(calories) if calories else None,
        is_available=is_available, sort_order=sort_order
    )
    db.add(dish)
    await db.flush()
    if image and image.filename:
        content = await image.read()
        if len(content) > settings.max_image_size:
            raise HTTPException(status_code=400, detail="Изображение слишком большое (макс 5MB)")
        paths = ImageProcessor.process_and_save(content, dish.id, image.filename)
        dish.image_thumbnail = paths["thumbnail"]
        dish.image_small = paths["small"]
        dish.image_medium = paths["medium"]
        dish.image_large = paths["large"]
        # Progressive loading optimization
        dish.image_tiny_base64 = paths.get("tiny_base64")
        dish.image_dominant_color = paths.get("dominant_color")
        # AVIF versions
        dish.image_small_avif = paths.get("small_avif")
        dish.image_medium_avif = paths.get("medium_avif")
        dish.image_large_avif = paths.get("large_avif")
    await db.commit()
    return RedirectResponse(url="/admin/dishes", status_code=302)


@router.get("/dishes/{dish_id}/edit", response_class=HTMLResponse)
async def dish_edit(
    request: Request, dish_id: int,
    admin: AdminUser = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Dish).where(Dish.id == dish_id))
    dish = result.scalar_one_or_none()
    if not dish:
        raise HTTPException(status_code=404)
    cat_result = await db.execute(select(Category).where(Category.is_active == True))
    categories = cat_result.scalars().all()
    return templates.TemplateResponse(
        "admin/dish_form.html",
        {"request": request, "admin": admin, "dish": dish, "categories": categories}
    )


@router.post("/dishes/{dish_id}")
async def dish_update(
    dish_id: int, name: str = Form(...), category_id: int = Form(...),
    description: str = Form(""), price: float = Form(...), weight: str = Form(""),
    calories: str = Form(""), is_available: bool = Form(False),
    sort_order: int = Form(0), image: UploadFile = File(None),
    admin: AdminUser = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Dish).where(Dish.id == dish_id))
    dish = result.scalar_one_or_none()
    if not dish:
        raise HTTPException(status_code=404)
    dish.name = name
    dish.slug = slugify(name, lowercase=True)
    dish.category_id = category_id
    dish.description = description
    dish.price = price
    dish.weight = weight
    dish.calories = int(calories) if calories else None
    dish.is_available = is_available
    dish.sort_order = sort_order
    if image and image.filename:
        content = await image.read()
        if len(content) > settings.max_image_size:
            raise HTTPException(status_code=400, detail="Изображение слишком большое")
        ImageProcessor.delete_images(dish.id)
        paths = ImageProcessor.process_and_save(content, dish.id, image.filename)
        dish.image_thumbnail = paths["thumbnail"]
        dish.image_small = paths["small"]
        dish.image_medium = paths["medium"]
        dish.image_large = paths["large"]
        # Progressive loading optimization
        dish.image_tiny_base64 = paths.get("tiny_base64")
        dish.image_dominant_color = paths.get("dominant_color")
        # AVIF versions
        dish.image_small_avif = paths.get("small_avif")
        dish.image_medium_avif = paths.get("medium_avif")
        dish.image_large_avif = paths.get("large_avif")
    await db.commit()
    return RedirectResponse(url="/admin/dishes", status_code=302)
