"""A simple API-key check for write operations. Reading the catalogue stays public."""

from __future__ import annotations

import secrets

from fastapi import Header, HTTPException, status

from .config import settings


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if not x_api_key or not secrets.compare_digest(x_api_key, settings.admin_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid X-API-Key header")
