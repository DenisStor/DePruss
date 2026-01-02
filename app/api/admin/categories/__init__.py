"""Categories management module for admin panel."""
from fastapi import APIRouter

from .crud import router as crud_router
from .api import router as api_router
from .bulk import router as bulk_router

router = APIRouter()

# Include all sub-routers
router.include_router(crud_router)
router.include_router(api_router)
router.include_router(bulk_router)
