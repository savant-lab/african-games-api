"""Settings read from environment variables (see .env.example)."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./games.db")
    admin_api_key: str = os.getenv("ADMIN_API_KEY", "change-me")
    app_name: str = os.getenv("APP_NAME", "African Games API")
    max_page_size: int = int(os.getenv("MAX_PAGE_SIZE", "100"))


settings = Settings()
