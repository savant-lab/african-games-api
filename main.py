"""Application entry point: `uvicorn app.main:app --reload`."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from . import __version__, crud, schemas
from .config import settings
from .database import Base, engine, get_db
from .routers import games, studios

DESCRIPTION = """
A public catalogue of **video games made by African studios**, with a focus on
what is launching *today* and *soon*.

* **Read** endpoints are open to everyone.
* **Write** endpoints (add, update, remove) need an `X-API-Key` header.
"""


@asynccontextmanager
async def lifespan(_: FastAPI):
    # For a portfolio-sized project, creating tables on start-up keeps setup to one command.
    # A production deployment would manage schema changes with Alembic migrations.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description=DESCRIPTION,
    lifespan=lifespan,
    contact={"name": "Savant. Adetayo Adeyemi — Digital Alchemy Solutions", "email": "dalchemysolutions@gmail.com"},
    license_info={"name": "MIT"},
)
app.include_router(games.router)
app.include_router(studios.router)


@app.get("/", tags=["Meta"], summary="Service information")
def root():
    return {"name": settings.app_name, "version": __version__, "docs": "/docs"}


@app.get("/health", tags=["Meta"], summary="Health check")
def health():
    return {"status": "ok"}


@app.get("/stats", response_model=schemas.Stats, tags=["Meta"], summary="Catalogue statistics")
def stats(db: Session = Depends(get_db)):
    return crud.stats(db)
