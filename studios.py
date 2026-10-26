from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..security import require_api_key

router = APIRouter(prefix="/studios", tags=["Studios"])


@router.get("", response_model=list[schemas.StudioRead], summary="List studios")
def list_studios(country: str | None = Query(default=None, examples=["Nigeria"]), db: Session = Depends(get_db)):
    return crud.list_studios(db, country)


@router.get("/{slug}", response_model=schemas.StudioRead, summary="Get one studio")
def get_studio(slug: str, db: Session = Depends(get_db)):
    studio = crud.get_studio(db, slug)
    if studio is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Studio not found")
    return studio


@router.post(
    "",
    response_model=schemas.StudioRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
    summary="Add a studio (API key required)",
)
def create_studio(data: schemas.StudioCreate, db: Session = Depends(get_db)):
    return crud.create_studio(db, data)
