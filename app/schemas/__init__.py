"""
Schemas module for API data structures.
"""
# Pagination
from app.schemas.pagination_new import (
    PaginatedResponse,
    PaginationParams,
    SortOrder,
)

# List items
from app.schemas.list_items import (
    DishListItem,
    CategoryListItem,
    AdminUserListItem,
    AuditLogListItem,
)

# Requests/Responses
from app.schemas.requests import (
    DishFilters,
    CategoryFilters,
    AuditLogFilters,
    BulkActionRequest,
    BulkActionResponse,
    ReorderItem,
    ReorderRequest,
    InlineEditRequest,
    InlineEditResponse,
)

__all__ = [
    # Pagination
    "PaginatedResponse",
    "PaginationParams",
    "SortOrder",
    # List items
    "DishListItem",
    "CategoryListItem",
    "AdminUserListItem",
    "AuditLogListItem",
    # Requests
    "DishFilters",
    "CategoryFilters",
    "AuditLogFilters",
    "BulkActionRequest",
    "BulkActionResponse",
    "ReorderItem",
    "ReorderRequest",
    "InlineEditRequest",
    "InlineEditResponse",
]
