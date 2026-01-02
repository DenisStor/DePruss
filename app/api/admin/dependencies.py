"""Common dependencies for admin routes."""
from fastapi.templating import Jinja2Templates
from app.config import get_settings

templates = Jinja2Templates(directory="app/templates")
settings = get_settings()
