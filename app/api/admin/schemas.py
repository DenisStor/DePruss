"""Pydantic schemas for admin API requests."""
from pydantic import BaseModel
from typing import List


class ReorderItem(BaseModel):
    id: int
    sort_order: int


class ReorderRequest(BaseModel):
    items: List[ReorderItem]


class BulkActionRequest(BaseModel):
    ids: List[int]
    action: str  # delete, activate, deactivate
