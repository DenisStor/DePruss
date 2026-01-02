"""Admin panel API routes.

This module combines all admin panel routes into a single router.
"""
from fastapi import APIRouter

from .auth import router as auth_router
from .dashboard import router as dashboard_router
from .categories import router as categories_router
from .dishes import router as dishes_router
from .users import router as users_router
from .audit import router as audit_router
from .search import router as search_router
from .data_exchange import router as data_exchange_router

# Main admin router
router = APIRouter(prefix="/admin")

# Include all sub-routers
router.include_router(auth_router, tags=["auth"])
router.include_router(dashboard_router, tags=["dashboard"])
router.include_router(categories_router, tags=["categories"])
router.include_router(dishes_router, tags=["dishes"])
router.include_router(users_router, tags=["users"])
router.include_router(audit_router, tags=["audit"])
router.include_router(search_router, tags=["search"])
router.include_router(data_exchange_router, tags=["data-exchange"])

__all__ = ["router"]
