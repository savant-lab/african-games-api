from datetime import date, timedelta

from tests.conftest import API_KEY, make_game


def test_health_and_root(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/").json()["docs"] == "/docs"


# ---------- Studios ----------


def test_create_and_fetch_studio(client, studio):
    assert studio["slug"] == "lagos-pixel-works"
    assert client.get("/studios/lagos-pixel-works").json()["country"] == "Nigeria"


def test_duplicate_studio_names_get_unique_slugs(client, studio):
    res = client.post("/studios", json={"name": "Lagos Pixel Works", "country": "Nigeria"}, headers=API_KEY)
    assert res.json()["slug"] == "lagos-pixel-works-2"


def test_filter_studios_by_country(client, studio):
    client.post("/studios", json={"name": "Accra Arcade", "country": "Ghana"}, headers=API_KEY)
    names = [s["name"] for s in client.get("/studios", params={"country": "ghana"}).json()]
    assert names == ["Accra Arcade"]


def test_write_endpoints_need_api_key(client):
    assert client.post("/studios", json={"name": "No Key", "country": "Kenya"}).status_code == 401
    assert client.post("/studios", json={"name": "Bad Key", "country": "Kenya"}, headers={"X-API-Key": "wrong"}).status_code == 401


def test_unknown_studio_is_404(client):
    assert client.get("/studios/does-not-exist").status_code == 404


# ---------- Games ----------


def test_create_game_tidies_tags(client, studio):
    game = make_game(client, studio["slug"])
    assert game["slug"] == "harmattan-run"
    assert game["studio"]["country"] == "Nigeria"
    assert game["genres"] == ["Action", "Platformer"]
    assert game["platforms"] == ["Android", "PC"]


def test_game_needs_existing_studio(client):
    res = client.post("/games", json={"title": "Orphan", "studio_slug": "nobody"}, headers=API_KEY)
    assert res.status_code == 422


def test_invalid_payload_is_rejected(client, studio):
    res = client.post("/games", json={"title": "", "studio_slug": studio["slug"], "price_usd": -1}, headers=API_KEY)
    assert res.status_code == 422


def test_search_filters(client, studio):
    ghana = client.post("/studios", json={"name": "Accra Arcade", "country": "Ghana"}, headers=API_KEY).json()
    make_game(client, studio["slug"], title="Harmattan Run", genres=["Platformer"], platforms=["Android"])
    make_game(client, ghana["slug"], title="Kente Tactics", genres=["Strategy"], platforms=["PC"], description="Turn-based weaving battles")

    def titles(**params):
        return [g["title"] for g in client.get("/games", params=params).json()["items"]]

    assert titles(country="Ghana") == ["Kente Tactics"]
    assert titles(genre="strategy") == ["Kente Tactics"]
    assert titles(platform="android") == ["Harmattan Run"]
    assert titles(q="weaving") == ["Kente Tactics"]
    assert sorted(titles()) == ["Harmattan Run", "Kente Tactics"]


def test_pagination(client, studio):
    for i in range(5):
        make_game(client, studio["slug"], title=f"Game {i}", release_date=f"2026-0{i + 1}-01")
    page = client.get("/games", params={"size": 2, "page": 2}).json()
    assert page["total"] == 5
    assert page["pages"] == 3
    assert len(page["items"]) == 2
    # newest first
    assert page["items"][0]["title"] == "Game 2"


def test_launches_today_and_upcoming(client, studio):
    today = date.today()
    make_game(client, studio["slug"], title="Out Today", release_date=today.isoformat())
    make_game(client, studio["slug"], title="Next Week", release_date=(today + timedelta(days=7)).isoformat())
    make_game(client, studio["slug"], title="Last Year", release_date=(today - timedelta(days=365)).isoformat())

    assert [g["title"] for g in client.get("/games/launches/today").json()] == ["Out Today"]
    assert [g["title"] for g in client.get("/games/launches/upcoming", params={"days": 14}).json()] == ["Next Week"]


def test_update_and_delete_game(client, studio):
    make_game(client, studio["slug"])
    res = client.patch("/games/harmattan-run", json={"price_usd": 2.5, "genres": ["Runner"]}, headers=API_KEY)
    assert res.status_code == 200
    assert res.json()["price_usd"] == 2.5
    assert res.json()["genres"] == ["Runner"]

    assert client.delete("/games/harmattan-run", headers=API_KEY).status_code == 204
    assert client.get("/games/harmattan-run").status_code == 404


def test_stats(client, studio):
    make_game(client, studio["slug"], title="A", genres=["Action"])
    make_game(client, studio["slug"], title="B", genres=["Action", "Puzzle"])
    s = client.get("/stats").json()
    assert s["games"] == 2
    assert s["studios"] == 1
    assert s["countries"] == {"Nigeria": 2}
    assert s["genres"]["Action"] == 2
