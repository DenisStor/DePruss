from fastapi import APIRouter, Depends, Request, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from slugify import slugify
from datetime import datetime

from app.database import get_db
from app.models import Category, Dish, AdminUser
from app.services.auth import (
    get_current_admin, authenticate_admin, create_access_token, get_password_hash
)
from app.services.image_processor import ImageProcessor
from app.config import get_settings

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")
settings = get_settings()


# ==================== AUTH ====================

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("admin/login.html", {"request": request})


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_admin(db, username, password)
    if not user:
        return templates.TemplateResponse(
            "admin/login.html",
            {"request": request, "error": "Неверный логин или пароль"}
        )

    # Обновляем время входа
    user.last_login = datetime.utcnow()
    await db.commit()

    # Создаем токен и устанавливаем cookie
    token = create_access_token(data={"sub": user.username})
    response = RedirectResponse(url="/admin", status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=86400,  # 24 часа
        samesite="lax"
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("access_token")
    return response


# ==================== DASHBOARD ====================

@router.get("", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    categories_count = len((await db.execute(select(Category))).scalars().all())
    dishes_count = len((await db.execute(select(Dish))).scalars().all())

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "admin": admin,
            "categories_count": categories_count,
            "dishes_count": dishes_count
        }
    )


# ==================== CATEGORIES ====================

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
    # Проверяем, нет ли блюд в категории
    result = await db.execute(select(Dish).where(Dish.category_id == cat_id))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Нельзя удалить категорию с блюдами")

    await db.execute(delete(Category).where(Category.id == cat_id))
    await db.commit()
    return RedirectResponse(url="/admin/categories", status_code=302)


# ==================== DISHES ====================

@router.get("/dishes", response_class=HTMLResponse)
async def dishes_list(
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Dish)
        .options(selectinload(Dish.category))
        .order_by(Dish.category_id, Dish.sort_order)
    )
    dishes = result.scalars().all()

    return templates.TemplateResponse(
        "admin/dishes.html",
        {"request": request, "admin": admin, "dishes": dishes}
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
    request: Request,
    name: str = Form(...),
    category_id: int = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    weight: str = Form(""),
    calories: int = Form(None),
    is_vegetarian: bool = Form(False),
    is_spicy: bool = Form(False),
    is_available: bool = Form(True),
    sort_order: int = Form(0),
    image: UploadFile = File(None),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    dish = Dish(
        name=name,
        slug=slugify(name, lowercase=True),
        category_id=category_id,
        description=description,
        price=price,
        weight=weight,
        calories=calories,
        is_vegetarian=is_vegetarian,
        is_spicy=is_spicy,
        is_available=is_available,
        sort_order=sort_order
    )
    db.add(dish)
    await db.flush()  # Получаем ID

    # Обработка изображения
    if image and image.filename:
        content = await image.read()
        if len(content) > settings.max_image_size:
            raise HTTPException(status_code=400, detail="Изображение слишком большое (макс 5MB)")

        paths = ImageProcessor.process_and_save(content, dish.id, image.filename)
        dish.image_thumbnail = paths["thumbnail"]
        dish.image_small = paths["small"]
        dish.image_medium = paths["medium"]
        dish.image_large = paths["large"]

    await db.commit()
    return RedirectResponse(url="/admin/dishes", status_code=302)


@router.get("/dishes/{dish_id}/edit", response_class=HTMLResponse)
async def dish_edit(
    request: Request,
    dish_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
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
    dish_id: int,
    name: str = Form(...),
    category_id: int = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    weight: str = Form(""),
    calories: int = Form(None),
    is_vegetarian: bool = Form(False),
    is_spicy: bool = Form(False),
    is_available: bool = Form(False),
    sort_order: int = Form(0),
    image: UploadFile = File(None),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
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
    dish.calories = calories
    dish.is_vegetarian = is_vegetarian
    dish.is_spicy = is_spicy
    dish.is_available = is_available
    dish.sort_order = sort_order

    # Обновление изображения
    if image and image.filename:
        content = await image.read()
        if len(content) > settings.max_image_size:
            raise HTTPException(status_code=400, detail="Изображение слишком большое")

        # Удаляем старые изображения
        ImageProcessor.delete_images(dish.id)

        paths = ImageProcessor.process_and_save(content, dish.id, image.filename)
        dish.image_thumbnail = paths["thumbnail"]
        dish.image_small = paths["small"]
        dish.image_medium = paths["medium"]
        dish.image_large = paths["large"]

    await db.commit()
    return RedirectResponse(url="/admin/dishes", status_code=302)


@router.post("/dishes/{dish_id}/delete")
async def dish_delete(
    dish_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    ImageProcessor.delete_images(dish_id)
    await db.execute(delete(Dish).where(Dish.id == dish_id))
    await db.commit()
    return RedirectResponse(url="/admin/dishes", status_code=302)
