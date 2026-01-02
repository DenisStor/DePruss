"""
Pagination schemas for API responses.
"""
from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class SortOrder(str, Enum):
    """Sort direction."""
    asc = "asc"
    desc = "desc"


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(default=None, description="Search query")
    sort_by: Optional[str] = Field(default=None, description="Sort field")
    sort_order: SortOrder = Field(default=SortOrder.asc, description="Sort direction")


# Generic type for list items
T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response."""
    items: List[T] = Field(description="List of items")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page")
    per_page: int = Field(description="Items per page")
    pages: int = Field(description="Total pages")
    has_next: bool = Field(description="Has next page")
    has_prev: bool = Field(description="Has previous page")

    @classmethod
    def create(cls, items: List[T], total: int, page: int, per_page: int) -> "PaginatedResponse[T]":
        """Factory method for creating response."""
        pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )
