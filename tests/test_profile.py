import pytest

from database import db as db_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test_spendly.db")
    monkeypatch.delenv("APP_ENV", raising=False)

    import app as app_module

    db_module.init_db()

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client


def register(client, name="Ada Lovelace", email="ada@example.com", password="supersecret"):
    return client.post(
        "/register", data={"name": name, "email": email, "password": password}
    )


def test_profile_shows_zero_stats_for_new_user(client):
    register(client)

    resp = client.get("/profile")

    assert resp.status_code == 200
    assert b"$0.00" in resp.data
    assert b'mock-total">0</span>' in resp.data


def test_profile_shows_not_set_username_for_new_user(client):
    register(client)

    resp = client.get("/profile")

    assert resp.status_code == 200
    assert b"Not set" in resp.data


def test_profile_shows_member_since_for_new_user(client):
    register(client)

    resp = client.get("/profile")

    assert resp.status_code == 200
    assert b"Member since" in resp.data
    assert b"None" not in resp.data


def test_profile_shows_correct_totals_for_seeded_demo_user(client):
    db_module.seed_db()

    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    resp = client.get("/profile")

    assert resp.status_code == 200
    assert b"$375.14" in resp.data
    assert b'mock-total">8</span>' in resp.data
