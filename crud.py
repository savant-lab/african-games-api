"""Database operations, kept separate from HTTP concerns so they are easy to test."""

from __future__ import annotations

import math
import re
import unicodedata
from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from . import models, schemas


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "item"


def _unique_slug(db: Session, model, base: str) -> str:
    slug, n = base, 2
    while db.scalar(select(model.id).where(model.slug == slug)) is not None:
        slug, n = f"{base}-{n}", n + 1
    return slug


def _get_or_create_tags(db: Session, model, names: list[str]):
    if not names:
        return []
    existing = {t.name.lower(): t for t in db.scalars(select(model).where(func.lower(model.name).in_([n.lower() for n in names])))}
    tags = []
    for name in names:
        tag = existing.get(name.lower())
        if tag is None:
            tag = model(name=name)
            db.add(tag)
            existing[name.lower()] = tag
        tags.append(tag)
    return tags


# ---------- Studios ----------


def list_studios(db: Session, country: str | None = None) -> list[models.Studio]:
    stmt = select(models.Studio).order_by(models.Studio.name)
    if country:
        stmt = stmt.where(func.lower(models.Studio.country) == country.lower())
    return list(db.scalars(stmt))


def get_studio(db: Session, slug: str) -> models.Studio | None:
    return db.scalar(select(models.Studio).where(models.Studio.slug == slug))


def create_studio(db: Session, data: schemas.StudioCreate) -> models.Studio:
    studio = models.Studio(
        name=data.name.strip(),
        slug=_unique_slug(db, models.Studio, slugify(data.name)),
        country=data.country.strip(),
        city=data.city,
        website=str(data.website) if data.website else None,
    )
    db.add(studio)
    db.commit()
    db.refresh(studio)
    return studio


# ---------- Games ----------


def search_games(
    db: Session,
    *,
    q: str | None = None,
    country: str | None = None,
    genre: str | None = None,
    platform: str | None = None,
    released_from: date | None = None,
    released_to: date | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[models.Game], int]:
    stmt = select(models.Game).join(models.Game.studio)

    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(func.lower(models.Game.title).like(like), func.lower(models.Game.description).like(like)))
    if country:
        stmt = stmt.where(func.lower(models.Studio.country) == country.lower())
    if genre:
        stmt = stmt.where(models.Game.genres.any(func.lower(models.Genre.name) == genre.lower()))
    if platform:
        stmt = stmt.where(models.Game.platforms.any(func.lower(models.Platform.name) == platform.lower()))
    if released_from:
        stmt = stmt.where(models.Game.release_date >= released_from)
    if released_to:
        stmt = stmt.where(models.Game.release_date <= released_to)

    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    stmt = stmt.order_by(models.Game.release_date.desc().nulls_last(), models.Game.title).offset((page - 1) * size).limit(size)
    return list(db.scalars(stmt).unique()), total


def get_game(db: Session, slug: str) -> models.Game | None:
    return db.scalar(select(models.Game).where(models.Game.slug == slug))


def create_game(db: Session, data: schemas.GameCreate, studio: models.Studio) -> models.Game:
    game = models.Game(
        title=data.title.strip(),
        slug=_unique_slug(db, models.Game, slugify(data.title)),
        studio=studio,
        release_date=data.release_date,
        description=data.description,
        price_usd=data.price_usd,
        cover_image_url=str(data.cover_image_url) if data.cover_image_url else None,
        trailer_url=str(data.trailer_url) if data.trailer_url else None,
        store_url=str(data.store_url) if data.store_url else None,
    )
    game.genres = _get_or_create_tags(db, models.Genre, data.genres)
    game.platforms = _get_or_create_tags(db, models.Platform, data.platforms)
    db.add(game)
    db.commit()
    db.refresh(game)
    return game


def update_game(db: Session, game: models.Game, data: schemas.GameUpdate) -> models.Game:
    changes = data.model_dump(exclude_unset=True)
    genres = changes.pop("genres", None)
    platforms = changes.pop("platforms", None)
    for field, value in changes.items():
        if field.endswith("_url") and value is not None:
            value = str(value)
        setattr(game, field, value)
    if genres is not None:
        game.genres = _get_or_create_tags(db, models.Genre, genres)
    if platforms is not None:
        game.platforms = _get_or_create_tags(db, models.Platform, platforms)
    db.commit()
    db.refresh(game)
    return game


def delete_game(db: Session, game: models.Game) -> None:
    db.delete(game)
    db.commit()


def stats(db: Session) -> schemas.Stats:
    def counts(stmt) -> dict[str, int]:
        return {name: n for name, n in db.execute(stmt).all()}

    by_country = (
        select(models.Studio.country, func.count(models.Game.id))
        .select_from(models.Game)
        .join(models.Game.studio)
        .group_by(models.Studio.country)
        .order_by(func.count(models.Game.id).desc())
    )
    by_genre = (
        select(models.Genre.name, func.count()).select_from(models.Genre).join(models.game_genres).group_by(models.Genre.name).order_by(func.count().desc())
    )
    by_platform = (
        select(models.Platform.name, func.count())
        .select_from(models.Platform)
        .join(models.game_platforms)
        .group_by(models.Platform.name)
        .order_by(func.count().desc())
    )
    return schemas.Stats(
        games=db.scalar(select(func.count(models.Game.id))) or 0,
        studios=db.scalar(select(func.count(models.Studio.id))) or 0,
        countries=counts(by_country),
        genres=counts(by_genre),
        platforms=counts(by_platform),
    )


def page_count(total: int, size: int) -> int:
    return max(1, math.ceil(total / size)) if size else 1
