from datetime import date, timedelta

import pytest

from database import db as db_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Patch DB_PATH before importing app so its module-level init_db()/seed_db()
    # never touch the real spendly.db.
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test_spendly.db")
    monkeypatch.delenv("APP_ENV", raising=False)

    import app as app_module

    db_module.init_db()

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client


def register(client, email="ada@example.com"):
    client.post(
        "/register", data={"name": "Ada Lovelace", "email": email, "password": "supersecret"}
    )
    return db_module.get_user_by_email(email)["id"]


def valid_form(**overrides):
    form = {
        "amount": "42.50",
        "category": "Food",
        "date": date.today().isoformat(),
        "description": "Lunch",
    }
    form.update(overrides)
    return form


def expense_rows():
    conn = db_module.get_db()
    rows = conn.execute("SELECT * FROM expenses ORDER BY id").fetchall()
    conn.close()
    return rows


def test_signed_out_get_redirects_to_login(client):
    resp = client.get("/expenses/add")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/login"


def test_signed_out_post_redirects_and_inserts_nothing(client):
    resp = client.post("/expenses/add", data=valid_form())
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/login"
    assert expense_rows() == []


def test_get_shows_form_with_categories_and_today(client):
    register(client)
    resp = client.get("/expenses/add")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Add an expense" in body
    for category in ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]:
        assert f'<option value="{category}"' in body
    assert f'value="{date.today().isoformat()}"' in body


def test_valid_post_inserts_expense_and_flashes(client):
    user_id = register(client)

    resp = client.post("/expenses/add", data=valid_form(amount="42.5"))
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/profile"

    rows = expense_rows()
    assert len(rows) == 1
    row = rows[0]
    assert row["user_id"] == user_id
    assert row["amount"] == 42.5
    assert row["category"] == "Food"
    assert row["date"] == date.today().isoformat()
    assert row["description"] == "Lunch"

    assert "Expense added." in client.get("/profile").get_data(as_text=True)


def test_trailing_zero_decimals_are_accepted(client):
    register(client)
    resp = client.post("/expenses/add", data=valid_form(amount="5.500"))
    assert resp.status_code == 302
    assert expense_rows()[0]["amount"] == 5.5


def test_deleted_user_get_redirects_to_login(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 9999

    resp = client.get("/expenses/add")

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/login"
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_blank_description_is_stored_as_null(client):
    register(client)
    client.post("/expenses/add", data=valid_form(description="   "))
    assert expense_rows()[0]["description"] is None


@pytest.mark.parametrize(
    "overrides",
    [
        {"amount": ""},
        {"amount": "0"},
        {"amount": "-5"},
        {"amount": "abc"},
        {"amount": "nan"},
        {"amount": "Infinity"},
        {"amount": "1.234"},
        {"amount": "10000000.01"},
        {"category": "Rent"},
        {"category": ""},
        {"date": ""},
        {"date": "2026-02-30"},
        {"date": "25/09/2026"},
        {"date": (date.today() + timedelta(days=1)).isoformat()},
        {"description": "x" * 201},
    ],
)
def test_invalid_input_is_rejected_and_values_kept(client, overrides):
    register(client)
    form = valid_form(**overrides)

    resp = client.post("/expenses/add", data=form)

    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'class="auth-error"' in body
    assert expense_rows() == []
    if form["description"] and len(form["description"]) <= 200:
        assert f'value="{form["description"]}"' in body


def test_user_id_in_form_is_ignored(client):
    other_id = register(client, email="other@example.com")
    with client.session_transaction() as sess:
        sess.clear()
    user_id = register(client, email="ada@example.com")

    client.post("/expenses/add", data=valid_form(user_id=str(other_id)))

    assert expense_rows()[0]["user_id"] == user_id


def test_deleted_user_session_redirects_to_login(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 9999

    resp = client.post("/expenses/add", data=valid_form())

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/login"
    assert expense_rows() == []
    with client.session_transaction() as sess:
        assert "user_id" not in sess
