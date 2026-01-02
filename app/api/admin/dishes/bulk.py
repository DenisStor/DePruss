"""Bulk operations, reorder, and duplicate for dishes."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from slugify import slugify

from app.database import get_db
from app.models import Dish, AdminUser
from app.services.auth import get_current_admin
from app.services.image_processor import ImageProcessor
from ..schemas import ReorderRequest, BulkActionRequest

router = APIRouter()


@router.post("/api/dishes/reorder")
async def dishes_reorder(
    request: ReorderRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Reorder dishes by sort_order."""
    for item in request.items:
        await db.execute(
            update(Dish).where(Dish.id == item.id).values(sort_order=item.sort_order)
        )
    await db.commit()
    return JSONResponse({"success": True})


@router.post("/api/dishes/bulk")
async def dishes_bulk(
    request: BulkActionRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Bulk actions: delete, activate, deactivate."""
    if request.action == "delete":
        for dish_id in request.ids:
            ImageProcessor.delete_images(dish_id)
        await db.execute(delete(Dish).where(Dish.id.in_(request.ids)))
    elif request.action == "activate":
        await db.execute(
            update(Dish).where(Dish.id.in_(request.ids)).values(is_available=True)
        )
    elif request.action == "deactivate":
        await db.execute(
            update(Dish).where(Dish.id.in_(request.ids)).values(is_available=False)
        )
    else:
        raise HTTPException(status_code=400, detail="Неизвестное действие")

    await db.commit()
    return JSONResponse({"success": True, "affected": len(request.ids)})


@router.post("/dishes/{dish_id}/delete")
async def dish_delete(
    dish_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a single dish."""
    ImageProcessor.delete_images(dish_id)
    await db.execute(delete(Dish).where(Dish.id == dish_id))
    await db.commit()
    return RedirectResponse(url="/admin/dishes", status_code=302)


@router.post("/dishes/{dish_id}/duplicate")
async def dish_duplicate(
    dish_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Duplicate a dish."""
    result = await db.execute(select(Dish).where(Dish.id == dish_id))
    original = result.scalar_one_or_none()
    if not original:
        raise HTTPException(status_code=404)

    new_dish = Dish(
        name=f"{original.name} (копия)",
        slug=slugify(f"{original.name} копия", lowercase=True),
        category_id=original.category_id,
        description=original.description,
        price=original.price,
        weight=original.weight,
        calories=original.calories,
        is_available=False,
        sort_order=original.sort_order + 1
    )
    db.add(new_dish)
    await db.flush()

    if original.image_thumbnail:
        paths = ImageProcessor.copy_images(original.id, new_dish.id)
        if paths:
            new_dish.image_thumbnail = paths.get("thumbnail")
            new_dish.image_small = paths.get("small")
            new_dish.image_medium = paths.get("medium")
            new_dish.image_large = paths.get("large")

    await db.commit()
    return RedirectResponse(url=f"/admin/dishes/{new_dish.id}/edit", status_code=302)
