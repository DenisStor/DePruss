"""Dashboard module for admin panel."""
from fastapi import APIRouter

from .routes import router as routes_router
from .api import router as api_router
from .constants import ACTION_DISPLAY, ENTITY_TYPE_DISPLAY

router = APIRouter()

# Include all sub-routers
router.include_router(routes_router)
router.include_router(api_router)
