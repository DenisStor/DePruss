"""Import/export operations for dishes."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AdminUser
from app.services.auth import get_current_admin
from app.services.audit import AuditService
from app.services.data_exchange import DataExchangeService

router = APIRouter()


@router.get("/api/dishes/export")
async def api_dishes_export(
    format: str = Query("csv", pattern="^(csv|excel)$"),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Export dishes to CSV or Excel."""
    service = DataExchangeService(db)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if format == "excel":
        content = await service.export_dishes_excel()
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=dishes_{timestamp}.xlsx"
            }
        )
    else:
        content = await service.export_dishes_csv()
        return Response(
            content=content.encode('utf-8-sig'),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename=dishes_{timestamp}.csv"
            }
        )


@router.post("/api/dishes/import")
async def api_dishes_import(
    file: UploadFile = File(...),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Import dishes from CSV or Excel file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл не выбран")

    content = await file.read()
    service = DataExchangeService(db)

    if file.filename.endswith('.xlsx'):
        created, updated, errors = await service.import_dishes_excel(content)
    elif file.filename.endswith('.csv'):
        created, updated, errors = await service.import_dishes_csv(content)
    else:
        raise HTTPException(status_code=400, detail="Поддерживаются только CSV и XLSX файлы")

    audit_service = AuditService(db)
    await audit_service.log(
        admin_user_id=admin.id,
        action='import',
        entity_type='dish',
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


@router.get("/api/dishes/template")
async def api_dishes_template(
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Download template for dishes import."""
    service = DataExchangeService(db)
    content = service.get_dishes_template_csv()

    return Response(
        content=content.encode('utf-8-sig'),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=dishes_template.csv"
        }
    )
