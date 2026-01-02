"""Bulk operations, reorder, and export for categories."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update

from app.database import get_db
from app.models import Category, Dish, AdminUser
from app.services.auth import get_current_admin
from app.services.audit import AuditService
from app.services.data_exchange import DataExchangeService
from ..schemas import ReorderRequest, BulkActionRequest

router = APIRouter()


@router.post("/api/categories/reorder")
async def categories_reorder(
    request: ReorderRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Reorder categories by sort_order."""
    for item in request.items:
        await db.execute(
            update(Category).where(Category.id == item.id).values(sort_order=item.sort_order)
        )
    await db.commit()
    return JSONResponse({"success": True})


@router.post("/api/categories/bulk")
async def categories_bulk(
    request: BulkActionRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Bulk actions: delete, activate, deactivate."""
    if request.action == "delete":
        for cat_id in request.ids:
            result = await db.execute(select(Dish).where(Dish.category_id == cat_id))
            if result.scalars().first():
                raise HTTPException(status_code=400, detail=f"Категория {cat_id} содержит блюда")
        await db.execute(delete(Category).where(Category.id.in_(request.ids)))
    elif request.action == "activate":
        await db.execute(
            update(Category).where(Category.id.in_(request.ids)).values(is_active=True)
        )
    elif request.action == "deactivate":
        await db.execute(
            update(Category).where(Category.id.in_(request.ids)).values(is_active=False)
        )
    else:
        raise HTTPException(status_code=400, detail="Неизвестное действие")

    await db.commit()
    return JSONResponse({"success": True, "affected": len(request.ids)})


@router.get("/api/categories/export")
async def api_categories_export(
    format: str = Query("csv", pattern="^(csv|excel)$"),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Export categories to CSV or Excel."""
    service = DataExchangeService(db)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if format == "excel":
        content = await service.export_categories_excel()
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=categories_{timestamp}.xlsx"
            }
        )
    else:
        content = await service.export_categories_csv()
        return Response(
            content=content.encode('utf-8-sig'),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename=categories_{timestamp}.csv"
            }
        )


@router.post("/api/categories/import")
async def api_categories_import(
    file: UploadFile = File(...),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Import categories from CSV file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл не выбран")

    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Поддерживаются только CSV файлы")

    content = await file.read()
    service = DataExchangeService(db)

    created, updated, errors = await service.import_categories_csv(content)

    audit_service = AuditService(db)
    await audit_service.log(
        admin_user_id=admin.id,
        action='import',
        entity_type='category',
        entity_name=file.filename,
        new_data={
            'created': created,
            'updated': updated,
            'errors_count': len(errors)
        }
    )

    return {
        "success": True,
        "created": created,
        "updated": updated,
        "errors": errors[:10] if errors else []
    }


@router.get("/api/categories/template")
async def api_categories_template(
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Download template for categories import."""
    service = DataExchangeService(db)
    content = service.get_categories_template_csv()

    return Response(
        content=content.encode('utf-8-sig'),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=categories_template.csv"
        }
    )
