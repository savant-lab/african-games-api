from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..config import settings
from ..database import get_db
from ..security import require_api_key

router = APIRouter(prefix="/games", tags=["Games"])


def _page(items, total: int, page: int, size: int) -> schemas.Page[schemas.GameRead]:
    return schemas.Page[schemas.GameRead](
        items=[schemas.GameRead.model_validate(g) for g in items],
        total=total,
        page=page,
        size=size,
        pages=crud.page_count(total, size),
    )


@router.get("", response_model=schemas.Page[schemas.GameRead], summary="Search the catalogue")
def search_games(
    q: str | None = Query(default=None, description="Text to find in the title or description"),
    country: str | None = Query(default=None, examples=["Ghana"]),
    genre: str | None = Query(default=None, examples=["Strategy"]),
    platform: str | None = Query(default=None, examples=["Android"]),
    released_from: date | None = None,
    released_to: date | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1),
    db: Session = Depends(get_db),
):
    size = min(size, settings.max_page_size)
    items, total = crud.search_games(
        db,
        q=q,
        country=country,
        genre=genre,
        platform=platform,
        released_from=released_from,
        released_to=released_to,
        page=page,
        size=size,
    )
    return _page(items, total, page, size)


@router.get("/launches/today", response_model=list[schemas.GameRead], summary="Games launching today")
def launches_today(db: Session = Depends(get_db)):
    today = date.today()
    items, _ = crud.search_games(db, released_from=today, released_to=today, size=settings.max_page_size)
    return items


@router.get("/launches/upcoming", response_model=list[schemas.GameRead], summary="Games launching soon")
def launches_upcoming(days: int = Query(default=30, ge=1, le=365), db: Session = Depends(get_db)):
    start = date.today() + timedelta(days=1)
    items, _ = crud.search_games(db, released_from=start, released_to=start + timedelta(days=days - 1), size=settings.max_page_size)
    return sorted(items, key=lambda g: (g.release_date, g.title))


@router.get("/{slug}", response_model=schemas.GameRead, summary="Get one game")
def get_game(slug: str, db: Session = Depends(get_db)):
    game = crud.get_game(db, slug)
    if game is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Game not found")
    return game


@router.post(
    "",
    response_model=schemas.GameRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
    summary="Add a game (API key required)",
)
def create_game(data: schemas.GameCreate, db: Session = Depends(get_db)):
    studio = crud.get_studio(db, data.studio_slug)
    if studio is None:
        raise HTTPException(422, f"No studio with slug '{data.studio_slug}'")
    return crud.create_game(db, data, studio)


@router.patch("/{slug}", response_model=schemas.GameRead, dependencies=[Depends(require_api_key)], summary="Update a game (API key required)")
def update_game(slug: str, data: schemas.GameUpdate, db: Session = Depends(get_db)):
    game = crud.get_game(db, slug)
    if game is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Game not found")
    return crud.update_game(db, game, data)


@router.delete(
    "/{slug}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
    summary="Remove a game (API key required)",
)
def delete_game(slug: str, db: Session = Depends(get_db)):
    game = crud.get_game(db, slug)
    if game is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Game not found")
    crud.delete_game(db, game)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
