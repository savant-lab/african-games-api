"""Request and response shapes (Pydantic v2)."""

from __future__ import annotations

from datetime import date
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

T = TypeVar("T")


def _clean_tags(values: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for v in values:
        tag = " ".join(v.split()).strip()
        if tag:
            seen.setdefault(tag.title() if tag.islower() else tag, None)
    return list(seen)


# ---------- Studios ----------


class StudioBase(BaseModel):
    name: str = Field(min_length=2, max_length=120, examples=["Lagos Pixel Works"])
    country: str = Field(min_length=2, max_length=60, examples=["Nigeria"])
    city: str | None = Field(default=None, max_length=80, examples=["Lagos"])
    website: HttpUrl | None = None


class StudioCreate(StudioBase):
    pass


class StudioRead(StudioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    website: str | None = None


class StudioSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    slug: str
    country: str


# ---------- Games ----------


class GameBase(BaseModel):
    title: str = Field(min_length=1, max_length=160, examples=["Harmattan Run"])
    release_date: date | None = Field(default=None, examples=["2026-11-14"])
    description: str | None = Field(default=None, max_length=5000)
    price_usd: float | None = Field(default=None, ge=0, examples=[4.99])
    cover_image_url: HttpUrl | None = None
    trailer_url: HttpUrl | None = None
    store_url: HttpUrl | None = None
    genres: list[str] = Field(default_factory=list, max_length=10, examples=[["Platformer", "Action"]])
    platforms: list[str] = Field(default_factory=list, max_length=10, examples=[["Android", "PC"]])

    @field_validator("genres", "platforms")
    @classmethod
    def tidy_tags(cls, values: list[str]) -> list[str]:
        return _clean_tags(values)


class GameCreate(GameBase):
    studio_slug: str = Field(examples=["lagos-pixel-works"])


class GameUpdate(BaseModel):
    """Every field optional: send only what changes (PATCH)."""

    title: str | None = Field(default=None, min_length=1, max_length=160)
    release_date: date | None = None
    description: str | None = Field(default=None, max_length=5000)
    price_usd: float | None = Field(default=None, ge=0)
    cover_image_url: HttpUrl | None = None
    trailer_url: HttpUrl | None = None
    store_url: HttpUrl | None = None
    genres: list[str] | None = None
    platforms: list[str] | None = None

    @field_validator("genres", "platforms")
    @classmethod
    def tidy_tags(cls, values: list[str] | None) -> list[str] | None:
        return None if values is None else _clean_tags(values)


class GameRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    release_date: date | None
    description: str | None
    price_usd: float | None
    cover_image_url: str | None
    trailer_url: str | None
    store_url: str | None
    studio: StudioSummary
    genres: list[str]
    platforms: list[str]

    @field_validator("genres", "platforms", mode="before")
    @classmethod
    def names_only(cls, values):
        return [getattr(v, "name", v) for v in values]


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int


class Stats(BaseModel):
    games: int
    studios: int
    countries: dict[str, int]
    genres: dict[str, int]
    platforms: dict[str, int]
