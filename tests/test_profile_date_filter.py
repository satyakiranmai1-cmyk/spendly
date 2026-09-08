from datetime import date, timedelta

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


def insert_expense(user_id, amount, category, expense_date, description=""):
    conn = db_module.get_db()
    conn.execute(
        """
        INSERT INTO expenses (user_id, amount, category, description, date)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, amount, category, description, expense_date),
    )
    conn.commit()
    conn.close()


def test_profile_date_filter_requires_login(client):
    resp = client.get("/profile?start_date=2026-08-01&end_date=2026-08-31")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_profile_default_view_shows_current_month_range(client):
    register(client)
    user_id = db_module.get_user_by_email("ada@example.com")["id"]

    today = date.today()
    prev_month_last_day = today.replace(day=1) - timedelta(days=1)

    insert_expense(user_id, 10.00, "Food", today.isoformat(), "This month")
    insert_expense(user_id, 99.00, "Shopping", prev_month_last_day.isoformat(), "Last month")

    client.post("/login", data={"email": "ada@example.com", "password": "supersecret"})
    resp = client.get("/profile")
    body = resp.data.decode()

    assert resp.status_code == 200
    assert "$10.00" in body
    assert "This month" in body
    assert "Last month" not in body


def test_profile_explicit_range_filters_expenses(client):
    register(client)
    user_id = db_module.get_user_by_email("ada@example.com")["id"]

    insert_expense(user_id, 20.00, "Food", "2026-05-10", "In range")
    insert_expense(user_id, 50.00, "Food", "2026-06-10", "Out of range")

    client.post("/login", data={"email": "ada@example.com", "password": "supersecret"})
    resp = client.get("/profile?start_date=2026-05-01&end_date=2026-05-31")
    body = resp.data.decode()

    assert resp.status_code == 200
    assert "In range" in body
    assert "Out of range" not in body
    assert "$20.00" in body


def test_profile_invalid_range_falls_back_to_default(client):
    register(client)
    user_id = db_module.get_user_by_email("ada@example.com")["id"]

    today = date.today()
    insert_expense(user_id, 15.00, "Food", today.isoformat(), "This month")

    client.post("/login", data={"email": "ada@example.com", "password": "supersecret"})

    malformed = client.get("/profile?start_date=not-a-date&end_date=also-bad")
    assert malformed.status_code == 200
    assert "$15.00" in malformed.data.decode()

    out_of_order = client.get("/profile?start_date=2026-08-31&end_date=2026-08-01")
    assert out_of_order.status_code == 200
    assert "$15.00" in out_of_order.data.decode()


def test_profile_all_time_preset_shows_all_expenses(client):
    register(client)
    user_id = db_module.get_user_by_email("ada@example.com")["id"]

    insert_expense(user_id, 20.00, "Food", "2026-01-05")
    insert_expense(user_id, 30.00, "Food", "2026-06-15")

    client.post("/login", data={"email": "ada@example.com", "password": "supersecret"})
    resp = client.get("/profile?range=all")

    assert resp.status_code == 200
    assert "$50.00" in resp.data.decode()


def test_profile_empty_range_shows_empty_state_with_range_context(client):
    register(client)
    user_id = db_module.get_user_by_email("ada@example.com")["id"]

    insert_expense(user_id, 20.00, "Food", "2026-01-05")

    client.post("/login", data={"email": "ada@example.com", "password": "supersecret"})
    resp = client.get("/profile?start_date=2026-03-01&end_date=2026-03-31")
    body = resp.data.decode()

    assert resp.status_code == 200
    assert "No expenses between" in body
    assert "Mar 01, 2026" in body
    assert "Mar 31, 2026" in body


def test_profile_filter_only_queries_own_user_expenses(client):
    register(client, name="Ada Lovelace", email="ada@example.com")
    register(client, name="Grace Hopper", email="grace@example.com")

    ada_id = db_module.get_user_by_email("ada@example.com")["id"]
    grace_id = db_module.get_user_by_email("grace@example.com")["id"]

    insert_expense(ada_id, 20.00, "Food", "2026-05-10", "Ada lunch")
    insert_expense(grace_id, 500.00, "Shopping", "2026-05-10", "Grace laptop")

    client.post("/login", data={"email": "ada@example.com", "password": "supersecret"})
    resp = client.get("/profile?start_date=2026-05-01&end_date=2026-05-31")
    body = resp.data.decode()

    assert resp.status_code == 200
    assert "Ada lunch" in body
    assert "Grace laptop" not in body
    assert "$20.00" in body


def test_get_expense_summary_by_user_with_date_range(client):
    conn = db_module.get_db()
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Test User", "range-summary@example.com", "hash"),
    )
    conn.commit()
    user_id = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("range-summary@example.com",)
    ).fetchone()["id"]
    conn.close()

    insert_expense(user_id, 10.00, "Food", "2026-05-10")
    insert_expense(user_id, 90.00, "Food", "2026-06-10")

    summary = db_module.get_expense_summary_by_user(user_id, "2026-05-01", "2026-05-31")
    assert summary == {"total_spent": 10.00, "expense_count": 1}

    summary_no_range = db_module.get_expense_summary_by_user(user_id)
    assert summary_no_range == {"total_spent": 100.00, "expense_count": 2}


def test_get_expenses_by_day_with_date_range(client):
    conn = db_module.get_db()
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Test User", "range-days@example.com", "hash"),
    )
    conn.commit()
    user_id = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("range-days@example.com",)
    ).fetchone()["id"]
    conn.close()

    insert_expense(user_id, 10.00, "Food", "2026-05-10")
    insert_expense(user_id, 90.00, "Food", "2026-06-10")

    days_in_range = db_module.get_expenses_by_day(user_id, "2026-05-01", "2026-05-31")
    assert len(days_in_range) == 1
    assert days_in_range[0]["date"] == "2026-05-10"

    days_no_range = db_module.get_expenses_by_day(user_id)
    assert len(days_no_range) == 2
