"""Test fixtures.

Tests run against an in-memory SQLite database by default. Set TEST_DATABASE_URL
(for example to a PostgreSQL URL, as CI does) to run the same suite against it.
"""

import os

os.environ.setdefault("ADMIN_API_KEY", "test-key")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

TEST_URL = os.getenv("TEST_DATABASE_URL", "sqlite://")
API_KEY = {"X-API-Key": os.environ["ADMIN_API_KEY"]}

if TEST_URL.startswith("sqlite"):
    engine = create_engine(TEST_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
else:
    engine = create_engine(TEST_URL)
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    # Not used as a context manager on purpose: the app's start-up hook would create
    # tables on the real database, and the tests only touch the test engine.
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def studio(client):
    res = client.post("/studios", json={"name": "Lagos Pixel Works", "country": "Nigeria", "city": "Lagos"}, headers=API_KEY)
    assert res.status_code == 201, res.text
    return res.json()


def make_game(client, studio_slug: str, **overrides):
    body = {
        "title": "Harmattan Run",
        "studio_slug": studio_slug,
        "release_date": "2026-11-14",
        "genres": ["platformer", "Action"],
        "platforms": ["Android", "PC"],
        "price_usd": 4.99,
    }
    body.update(overrides)
    res = client.post("/games", json=body, headers=API_KEY)
    assert res.status_code == 201, res.text
    return res.json()
