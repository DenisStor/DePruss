"""
List item schemas for API responses.
"""
from typing import Optional, Any
from pydantic import BaseModel


class DishListItem(BaseModel):
    """Dish list item."""
    id: int
    name: str
    slug: str
    price: float
    weight: Optional[str] = None
    calories: Optional[int] = None
    is_available: bool = True
    sort_order: int = 0
    image_thumbnail: Optional[str] = None
    category_id: int
    category_name: str

    class Config:
        from_attributes = True


class CategoryListItem(BaseModel):
    """Category list item."""
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0
    dishes_count: int = 0

    class Config:
        from_attributes = True


class AdminUserListItem(BaseModel):
    """Admin user list item."""
    id: int
    username: str
    is_active: bool = True
    last_login: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class AuditLogListItem(BaseModel):
    """Audit log list item."""
    id: int
    action: str
    action_display: str
    entity_type: str
    entity_type_display: str
    entity_id: Optional[int] = None
    entity_name: Optional[str] = None
    admin_username: Optional[str] = None
    created_at: str
    old_data: Optional[Any] = None
    new_data: Optional[Any] = None

    class Config:
        from_attributes = True
