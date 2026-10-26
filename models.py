"""Database tables: studios, games, and the genres/platforms they are tagged with."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Numeric, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


game_genres = Table(
    "game_genres",
    Base.metadata,
    Column("game_id", ForeignKey("games.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)

game_platforms = Table(
    "game_platforms",
    Base.metadata,
    Column("game_id", ForeignKey("games.id", ondelete="CASCADE"), primary_key=True),
    Column("platform_id", ForeignKey("platforms.id", ondelete="CASCADE"), primary_key=True),
)


class Studio(Base):
    __tablename__ = "studios"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True)
    country: Mapped[str] = mapped_column(String(60), index=True)
    city: Mapped[str | None] = mapped_column(String(80))
    website: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    games: Mapped[list[Game]] = relationship(back_populates="studio")


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)


class Platform(Base):
    __tablename__ = "platforms"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    studio_id: Mapped[int] = mapped_column(ForeignKey("studios.id", ondelete="RESTRICT"), index=True)
    release_date: Mapped[date | None] = mapped_column(Date, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    price_usd: Mapped[float | None] = mapped_column(Numeric(8, 2))
    cover_image_url: Mapped[str | None] = mapped_column(String(500))
    trailer_url: Mapped[str | None] = mapped_column(String(500))
    store_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    studio: Mapped[Studio] = relationship(back_populates="games", lazy="joined")
    genres: Mapped[list[Genre]] = relationship(secondary=game_genres, lazy="selectin", order_by="Genre.name")
    platforms: Mapped[list[Platform]] = relationship(secondary=game_platforms, lazy="selectin", order_by="Platform.name")
