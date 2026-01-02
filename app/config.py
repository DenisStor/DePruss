from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
import os
import secrets
import warnings


class Settings(BaseSettings):
    app_name: str = "Кухня Де Прусс"
    debug: bool = False
    secret_key: str = ""  # Should be set via environment variable

    @field_validator('secret_key', mode='before')
    @classmethod
    def validate_secret_key(cls, v):
        if not v or v in ('change-me-in-production', 'your-secret-key'):
            # Generate random key for development but warn
            warnings.warn(
                "SECRET_KEY not set! Using random key. Set SECRET_KEY environment variable in production.",
                UserWarning
            )
            return secrets.token_urlsafe(32)
        if len(v) < 32:
            warnings.warn("SECRET_KEY should be at least 32 characters for security", UserWarning)
        return v
    database_url: str = "sqlite+aiosqlite:///./data/cafe.db"

    # JWT
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Image processing
    upload_dir: str = "static/uploads/dishes"
    max_image_size: int = 500 * 1024 * 1024  # 500MB - no practical limit
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
