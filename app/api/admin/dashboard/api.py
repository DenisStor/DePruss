"""API endpoints for dashboard - activity feed."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import AdminUser, AuditLog
from app.services.auth import get_current_admin
from .constants import ACTION_DISPLAY, ENTITY_TYPE_DISPLAY

router = APIRouter()


@router.get("/api/activity")
async def get_activity(
    request: Request,
    period: str = Query("all", description="Period: today, week, month, all"),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """API endpoint for AJAX loading activity history with filters."""
    query = select(AuditLog).options(selectinload(AuditLog.admin_user))

    # Period filter
    now = datetime.now()
    if period == "today":
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        query = query.where(AuditLog.created_at >= start_of_day)
    elif period == "week":
        week_ago = now - timedelta(days=7)
        query = query.where(AuditLog.created_at >= week_ago)
    elif period == "month":
        month_ago = now - timedelta(days=30)
        query = query.where(AuditLog.created_at >= month_ago)

    # Sort and limit
    query = query.order_by(AuditLog.created_at.desc()).limit(15)

    result = await db.execute(query)
    logs = result.scalars().all()

    # Build JSON response
    items = []
    for log in logs:
        # Format diff for update actions
        diff_data = None
        if log.action == "update" and log.new_data:
            diff_data = {}
            for key, value in log.new_data.items():
                if isinstance(value, dict) and "old" in value and "new" in value:
                    diff_data[key] = {"old": value["old"], "new": value["new"]}

        items.append({
            "id": log.id,
            "admin_username": log.admin_user.username if log.admin_user else "Система",
            "action": log.action,
            "action_display": ACTION_DISPLAY.get(log.action, log.action),
            "entity_type": log.entity_type,
            "entity_type_display": ENTITY_TYPE_DISPLAY.get(log.entity_type, log.entity_type),
            "entity_id": log.entity_id,
            "entity_name": log.entity_name or "",
            "diff": diff_data,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })

    return JSONResponse(content={"items": items})
