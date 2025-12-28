from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    app_name: str = "Кухня Де Прусс"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    database_url: str = "sqlite+aiosqlite:///./data/cafe.db"

    # JWT
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Image processing
    upload_dir: str = "static/uploads/dishes"
    max_image_size: int = 50 * 1024 * 1024  # 50MB
    image_sizes: dict = {
        "thumbnail": (50, 50),
        "small": (200, 200),
        "medium": (400, 400),
        "large": (800, 800)
    }

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
