"""
Request and response schemas for API operations.
"""
from typing import List, Optional, Any
from pydantic import BaseModel, Field


class DishFilters(BaseModel):
    """Dish filters."""
    category_id: Optional[int] = None
    is_available: Optional[bool] = None


class CategoryFilters(BaseModel):
    """Category filters."""
    is_active: Optional[bool] = None


class AuditLogFilters(BaseModel):
    """Audit log filters."""
    entity_type: Optional[str] = None
    admin_user_id: Optional[int] = None
    action: Optional[str] = None
    entity_id: Optional[int] = None


class BulkActionRequest(BaseModel):
    """Bulk action request."""
    ids: List[int] = Field(min_length=1, description="Item IDs")
    action: str = Field(description="Action: delete, activate, deactivate")


class BulkActionResponse(BaseModel):
    """Bulk action response."""
    success: bool
    affected: int = Field(description="Number of affected records")
    message: str


class ReorderItem(BaseModel):
    """Reorder item."""
    id: int
    sort_order: int


class ReorderRequest(BaseModel):
    """Reorder request."""
    items: List[ReorderItem]


class InlineEditRequest(BaseModel):
    """Inline edit request."""
    field: str = Field(description="Field name")
    value: Any = Field(description="New value")


class InlineEditResponse(BaseModel):
    """Inline edit response."""
    success: bool
    field: str
    value: Any
    message: Optional[str] = None
