"""Load example data so the API has something to show straight away.

The studios and games below are FICTIONAL placeholders, not real releases.
Replace them with your curated catalogue (or import from a CSV) before going live.

    python -m scripts.seed
"""

from __future__ import annotations

from datetime import date, timedelta

from app import crud, schemas
from app.database import Base, SessionLocal, engine

STUDIOS = [
    {"name": "Lagos Pixel Works", "country": "Nigeria", "city": "Lagos"},
    {"name": "Accra Arcade", "country": "Ghana", "city": "Accra"},
    {"name": "Savannah Signal Games", "country": "Kenya", "city": "Nairobi"},
    {"name": "Cape Current Interactive", "country": "South Africa", "city": "Cape Town"},
    {"name": "Douala Dreamforge", "country": "Cameroon", "city": "Douala"},
]

# (title, studio index, days from today, genres, platforms, price)
GAMES = [
    ("Harmattan Run", 0, 0, ["Platformer", "Action"], ["Android", "iOS"], 0),
    ("Danfo Dash", 0, -40, ["Racing", "Casual"], ["Android"], 0),
    ("Kente Tactics", 1, 0, ["Strategy"], ["PC"], 9.99),
    ("Market Queen", 1, 12, ["Simulation", "Management"], ["PC", "Android"], 4.99),
    ("Rift Valley Rangers", 2, 5, ["Adventure"], ["PC", "Nintendo Switch"], 14.99),
    ("Matatu Mayhem", 2, -120, ["Racing", "Action"], ["Android"], 0),
    ("Table Mountain Tales", 3, 21, ["RPG", "Adventure"], ["PC", "PlayStation"], 19.99),
    ("Ubuntu Builders", 3, -10, ["Puzzle", "Co-op"], ["PC"], 7.99),
    ("Spirits of the Forest", 4, 3, ["RPG"], ["PC"], 12.99),
    ("Ndolé Kitchen Rush", 4, -200, ["Casual", "Simulation"], ["Android", "iOS"], 1.99),
]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    today = date.today()
    with SessionLocal() as db:
        if crud.list_studios(db):
            print("Database already has data; skipping seed.")
            return
        studios = [crud.create_studio(db, schemas.StudioCreate(**s)) for s in STUDIOS]
        for title, si, offset, genres, platforms, price in GAMES:
            crud.create_game(
                db,
                schemas.GameCreate(
                    title=title,
                    studio_slug=studios[si].slug,
                    release_date=today + timedelta(days=offset),
                    genres=genres,
                    platforms=platforms,
                    price_usd=price,
                    description=f"Example entry: {title} (placeholder data for the demo).",
                ),
                studios[si],
            )
        print(f"Seeded {len(studios)} studios and {len(GAMES)} games.")


if __name__ == "__main__":
    main()
