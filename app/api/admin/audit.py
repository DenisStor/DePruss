"""Audit log routes for admin panel."""
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.database import get_db
from app.models import AdminUser
from app.services.auth import get_current_admin
from app.services.audit import AuditService
from app.schemas import PaginatedResponse, AuditLogListItem
from .dependencies import templates

router = APIRouter()


# ==================== PAGE ====================

@router.get("/audit-logs", response_class=HTMLResponse)
async def audit_logs_page(
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Страница истории изменений"""
    # Получаем список администраторов для фильтра
    admins_result = await db.execute(select(AdminUser).order_by(AdminUser.username))
    admins = admins_result.scalars().all()

    return templates.TemplateResponse(
        "admin/audit_logs.html",
        {
            "request": request,
            "admin": admin,
            "admins": admins
        }
    )


# ==================== API ====================

@router.get("/api/audit-logs")
async def api_audit_logs_list(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    entity_type: Optional[str] = Query(None),
    admin_user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Получить логи аудита с пагинацией и фильтрами"""
    audit_service = AuditService(db)
    logs, total = await audit_service.get_logs(
        page=page,
        per_page=per_page,
        entity_type=entity_type,
        admin_user_id=admin_user_id,
        action=action,
        entity_id=entity_id
    )

    items = [
        AuditLogListItem(
            id=log.id,
            action=log.action,
            action_display=log.action_display,
            entity_type=log.entity_type,
            entity_type_display=log.entity_type_display,
            entity_id=log.entity_id,
            entity_name=log.entity_name,
            admin_username=log.admin_user.username if log.admin_user else None,
            created_at=log.created_at.isoformat() if log.created_at else "",
            old_data=log.old_data,
            new_data=log.new_data
        )
        for log in logs
    ]

    return PaginatedResponse.create(items=items, total=total, page=page, per_page=per_page)
