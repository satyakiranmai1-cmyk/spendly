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


def test_statement_requires_login(client):
    resp = client.get("/expenses")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_statement_shows_empty_state_for_new_user(client):
    register(client)

    resp = client.get("/expenses")

    assert resp.status_code == 200
    assert b"No expenses logged yet." in resp.data


def test_statement_groups_expenses_by_day_with_daily_totals(client):
    register(client)
    resp = client.post(
        "/register",
        data={"name": "Ada Lovelace", "email": "ada2@example.com", "password": "supersecret"},
    )
    user_id = db_module.get_user_by_email("ada2@example.com")["id"]

    conn = db_module.get_db()
    conn.executemany(
        """
        INSERT INTO expenses (user_id, amount, category, description, date)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (user_id, 10.00, "Food", "Breakfast", "2026-08-01"),
            (user_id, 5.50, "Transport", "Bus fare", "2026-08-01"),
            (user_id, 20.00, "Shopping", "Notebook", "2026-08-03"),
        ],
    )
    conn.commit()
    conn.close()

    client.post("/login", data={"email": "ada2@example.com", "password": "supersecret"})
    resp = client.get("/expenses")
    body = resp.data.decode()

    assert resp.status_code == 200
    assert "$15.50" in body
    assert "$20.00" in body
    assert body.index("August 03, 2026") < body.index("August 01, 2026")


def test_statement_matches_seeded_demo_user_total(client):
    db_module.seed_db()

    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    resp = client.get("/expenses")

    assert resp.status_code == 200
    assert b"8 expenses" in resp.data
    assert b"$375.14 total" in resp.data
