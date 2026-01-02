"""
Audit service for logging admin panel actions.
"""
from typing import Optional, Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from app.models import AuditLog
from .helpers import compute_changes


class AuditService:
    """Service for working with audit logs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        admin_user_id: Optional[int],
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        entity_name: Optional[str] = None,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        details: Optional[str] = None
    ) -> AuditLog:
        """
        Record an event in the audit log.

        Args:
            admin_user_id: Admin user ID
            action: Action type (create, update, delete, login, logout, etc.)
            entity_type: Entity type (dish, category, admin_user, system)
            entity_id: Entity ID
            entity_name: Entity name (for display)
            old_data: Previous data (for update/delete)
            new_data: New data (for create/update)
            details: Additional information
        """
        log_entry = AuditLog(
            admin_user_id=admin_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            old_data=old_data,
            new_data=new_data,
            details=details
        )

        self.db.add(log_entry)
        await self.db.commit()
        await self.db.refresh(log_entry)

        return log_entry

    async def log_create(
        self,
        admin_user_id: int,
        entity_type: str,
        entity_id: int,
        entity_name: str,
        new_data: Dict[str, Any]
    ) -> AuditLog:
        """Log entity creation."""
        return await self.log(
            admin_user_id=admin_user_id,
            action='create',
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            new_data=new_data
        )

    async def log_update(
        self,
        admin_user_id: int,
        entity_type: str,
        entity_id: int,
        entity_name: str,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any]
    ) -> AuditLog:
        """Log entity update."""
        changes = compute_changes(old_data, new_data)

        if not changes:
            return None  # No changes

        return await self.log(
            admin_user_id=admin_user_id,
            action='update',
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            old_data=old_data,
            new_data=changes  # Save only diff
        )

    async def log_delete(
        self,
        admin_user_id: int,
        entity_type: str,
        entity_id: int,
        entity_name: str,
        old_data: Dict[str, Any]
    ) -> AuditLog:
        """Log entity deletion."""
        return await self.log(
            admin_user_id=admin_user_id,
            action='delete',
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            old_data=old_data
        )

    async def log_login(
        self,
        admin_user_id: int,
        username: str,
        details: Optional[str] = None
    ) -> AuditLog:
        """Log system login."""
        return await self.log(
            admin_user_id=admin_user_id,
            action='login',
            entity_type='admin_user',
            entity_id=admin_user_id,
            entity_name=username,
            details=details
        )

    async def log_logout(
        self,
        admin_user_id: int,
        username: str
    ) -> AuditLog:
        """Log system logout."""
        return await self.log(
            admin_user_id=admin_user_id,
            action='logout',
            entity_type='admin_user',
            entity_id=admin_user_id,
            entity_name=username
        )

    async def log_bulk_action(
        self,
        admin_user_id: int,
        action: str,
        entity_type: str,
        entity_ids: List[int],
        entity_names: List[str]
    ) -> AuditLog:
        """Log bulk action."""
        return await self.log(
            admin_user_id=admin_user_id,
            action=f'bulk_{action}',
            entity_type=entity_type,
            entity_name=f'{len(entity_ids)} элементов',
            new_data={
                'ids': entity_ids,
                'names': entity_names
            }
        )

    async def get_logs(
        self,
        page: int = 1,
        per_page: int = 50,
        entity_type: Optional[str] = None,
        admin_user_id: Optional[int] = None,
        action: Optional[str] = None,
        entity_id: Optional[int] = None
    ) -> tuple[List[AuditLog], int]:
        """
        Get logs with filtering and pagination.

        Returns:
            Tuple of (log list, total count)
        """
        query = select(AuditLog).options(selectinload(AuditLog.admin_user))

        # Apply filters
        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        if admin_user_id:
            query = query.where(AuditLog.admin_user_id == admin_user_id)
        if action:
            query = query.where(AuditLog.action == action)
        if entity_id:
            query = query.where(AuditLog.entity_id == entity_id)

        # Sort by date (newest first)
        query = query.order_by(desc(AuditLog.created_at))

        # Get total count
        count_query = select(AuditLog)
        if entity_type:
            count_query = count_query.where(AuditLog.entity_type == entity_type)
        if admin_user_id:
            count_query = count_query.where(AuditLog.admin_user_id == admin_user_id)
        if action:
            count_query = count_query.where(AuditLog.action == action)
        if entity_id:
            count_query = count_query.where(AuditLog.entity_id == entity_id)

        total_result = await self.db.execute(
            select(func.count()).select_from(count_query.subquery())
        )
        total = total_result.scalar()

        # Pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await self.db.execute(query)
        logs = result.scalars().all()

        return list(logs), total

    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: int
    ) -> List[AuditLog]:
        """Get change history for specific entity."""
        query = (
            select(AuditLog)
            .options(selectinload(AuditLog.admin_user))
            .where(AuditLog.entity_type == entity_type)
            .where(AuditLog.entity_id == entity_id)
            .order_by(desc(AuditLog.created_at))
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_admin_activity(
        self,
        admin_user_id: int,
        limit: int = 20
    ) -> List[AuditLog]:
        """Get recent admin activity."""
        query = (
            select(AuditLog)
            .where(AuditLog.admin_user_id == admin_user_id)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())
