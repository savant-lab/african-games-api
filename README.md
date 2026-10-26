<div align="center">

# 🎮 African Games API

**A REST API that catalogues video games made by African studios, and what is launching today.**

![Python](https://img.shields.io/badge/Python-3.10%2B-1b1b20?logo=python&logoColor=fe7b50)
![FastAPI](https://img.shields.io/badge/FastAPI-REST-1b1b20?logo=fastapi&logoColor=fe7b50)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-1b1b20)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-1b1b20?logo=postgresql&logoColor=fe7b50)
![Docker](https://img.shields.io/badge/Docker-ready-1b1b20?logo=docker&logoColor=fe7b50)
![License](https://img.shields.io/badge/license-MIT-fe7b50)

</div>

---

African game studios ship new titles every week, but there is no single, searchable place to find them. This API is the backend for that place: studios, games, genres and platforms in a clean relational model, with endpoints for **search**, **today's launches**, **upcoming releases** and **catalogue statistics**.

It is built the way a production service should be: typed request and response schemas, a separate data-access layer, API-key protection on writes, automated tests against both SQLite and PostgreSQL, and a one-command Docker setup.

## Endpoints

| Method | Path | What it does | Auth |
|---|---|---|---|
| `GET` | `/games` | Search with `q`, `country`, `genre`, `platform`, `released_from`, `released_to`, `page`, `size` | – |
| `GET` | `/games/launches/today` | Games released today | – |
| `GET` | `/games/launches/upcoming?days=30` | Games coming in the next *n* days | – |
| `GET` | `/games/{slug}` | One game | – |
| `POST` | `/games` | Add a game | 🔑 |
| `PATCH` | `/games/{slug}` | Update only the fields you send | 🔑 |
| `DELETE` | `/games/{slug}` | Remove a game | 🔑 |
| `GET` | `/studios?country=` | List studios | – |
| `GET` | `/studios/{slug}` | One studio | – |
| `POST` | `/studios` | Add a studio | 🔑 |
| `GET` | `/stats` | Counts by country, genre and platform | – |
| `GET` | `/health` | Health check | – |

🔑 = send an `X-API-Key` header. Interactive documentation is generated automatically at **`/docs`** (Swagger UI) and **`/redoc`**.

### Example

```bash
curl "http://localhost:8000/games?country=Ghana&genre=strategy"
```

```json
{
  "items": [
    {
      "id": 3,
      "title": "Kente Tactics",
      "slug": "kente-tactics",
      "release_date": "2026-10-26",
      "price_usd": 9.99,
      "studio": { "name": "Accra Arcade", "slug": "accra-arcade", "country": "Ghana" },
      "genres": ["Strategy"],
      "platforms": ["PC"],
      "description": "Example entry: Kente Tactics (placeholder data for the demo).",
      "cover_image_url": null,
      "trailer_url": null,
      "store_url": null
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

## Run it

### With Docker (API + PostgreSQL)

```bash
git clone https://github.com/savant-lab/african-games-api.git
cd african-games-api
docker compose up --build
docker compose exec api python -m scripts.seed     # optional example data
```

Open <http://localhost:8000/docs>.

### Locally (SQLite, no setup)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m scripts.seed
uvicorn app.main:app --reload
```

Configuration comes from environment variables. See [`.env.example`](.env.example). Set `DATABASE_URL` to any PostgreSQL database (Neon, Supabase, RDS…) to go beyond SQLite.

## Design

```text
app/
├── main.py        FastAPI app, routers, metadata
├── config.py      settings from environment variables
├── database.py    engine, session, request-scoped dependency
├── models.py      SQLAlchemy 2.0 tables: Studio, Game, Genre, Platform (+ link tables)
├── schemas.py     Pydantic v2 request/response models and validation
├── crud.py        all database queries, independent of HTTP
├── security.py    constant-time API-key check for write operations
└── routers/       /games and /studios endpoints
```

- **Normalised tags.** Genres and platforms are their own tables, so filtering is an indexed join, not a text search, and `"rpg"`, `"RPG"` and `" Rpg "` collapse into one tag.
- **Stable, readable URLs.** Every studio and game gets a unique slug (`harmattan-run`, `harmattan-run-2`…).
- **Partial updates.** `PATCH` changes only the fields that are sent.
- **Honest pagination.** Every list response includes `total` and `pages`.
- **Same code, two databases.** SQLite for development and tests, PostgreSQL in production. CI runs the suite against both.

## Tests

```bash
pytest -q
```

The suite covers creation, validation, auth, slug uniqueness, every search filter, pagination order, today/upcoming launches, partial updates, deletion and statistics. GitHub Actions runs it on Python 3.10, 3.12 and 3.13 with SQLite, and again against a real PostgreSQL 16 service.

## Data

`scripts/seed.py` loads **fictional placeholder** studios and games so the endpoints return something on first run. They are not real releases. Replace them with a curated catalogue before publishing.

## Roadmap

- [ ] Alembic migrations
- [ ] CSV / spreadsheet bulk import
- [ ] Image and trailer upload to object storage
- [ ] Daily "launching today" digest (email / WhatsApp)
- [ ] Public web front end

## Author

**Savant. Adetayo Adeyemi (SAA)** · [Digital Alchemy Solutions](https://github.com/savant-lab)
Python backends · data pipelines · AI strategy · technical writing

📧 dalchemysolutions@gmail.com

*It works. It scales. It is built with care.*
