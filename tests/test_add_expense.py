import re
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


def date_input(body):
    return re.search(r'<input type="date"[^>]*>', body).group(0)


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


def test_profile_totals_include_added_expenses(client):
    register(client)
    resp = client.get("/profile")
    assert b"$0.00" in resp.data
    assert b'mock-total">0</span>' in resp.data

    client.post("/expenses/add", data=valid_form(amount="42.50"))
    client.post("/expenses/add", data=valid_form(amount="7.25", category="Transport"))

    resp = client.get("/profile")
    assert b"$49.75" in resp.data
    assert b'mock-total">2</span>' in resp.data


def test_profile_lists_expenses_grouped_by_day_newest_first(client):
    register(client)
    today = date.today()
    yesterday = today - timedelta(days=1)
    client.post("/expenses/add", data=valid_form(amount="10", date=yesterday.isoformat(), description="Old one"))
    client.post("/expenses/add", data=valid_form(amount="4.50", date=today.isoformat(), description="Coffee"))
    client.post("/expenses/add", data=valid_form(amount="5.50", date=today.isoformat(), description="Bus", category="Transport"))

    body = client.get("/profile").get_data(as_text=True)

    today_label = today.strftime("%A, %B %d, %Y")
    yesterday_label = yesterday.strftime("%A, %B %d, %Y")
    assert body.index(today_label) < body.index(yesterday_label)
    assert body.index("Bus") < body.index("Coffee") < body.index("Old one")
    assert 'statement-day-total">$10.00' in body  # today's 4.50 + 5.50, and yesterday's 10


def test_profile_shows_empty_state_without_expenses(client):
    register(client)
    assert b"No expenses logged yet." in client.get("/profile").data


def test_profile_totals_only_count_own_expenses(client):
    register(client, email="other@example.com")
    client.post("/expenses/add", data=valid_form(amount="100"))
    with client.session_transaction() as sess:
        sess.clear()
    register(client, email="ada@example.com")

    resp = client.get("/profile")
    assert b"$0.00" in resp.data


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
        {"date": (date.today() + timedelta(days=2)).isoformat()},
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


# ------------------------------------------------------------------ #
# Coverage added from .claude/specs/06-add-expenses.md               #
# ------------------------------------------------------------------ #


@pytest.mark.parametrize(
    "amount, stored",
    [("0.01", 0.01), ("10000000", 10000000.0), ("10000000.00", 10000000.0), ("19.99", 19.99)],
)
def test_amounts_at_the_limits_are_accepted(client, amount, stored):
    register(client)

    resp = client.post("/expenses/add", data=valid_form(amount=amount))

    assert resp.status_code == 302
    assert expense_rows()[0]["amount"] == stored


def test_description_of_exactly_200_characters_is_accepted(client):
    register(client)

    resp = client.post("/expenses/add", data=valid_form(description="x" * 200))

    assert resp.status_code == 302
    assert expense_rows()[0]["description"] == "x" * 200


def test_description_is_stored_trimmed(client):
    register(client)

    client.post("/expenses/add", data=valid_form(description="  Lunch with team  "))

    assert expense_rows()[0]["description"] == "Lunch with team"


def test_past_date_is_accepted(client):
    register(client)
    last_year = (date.today() - timedelta(days=365)).isoformat()

    resp = client.post("/expenses/add", data=valid_form(date=last_year))

    assert resp.status_code == 302
    assert expense_rows()[0]["date"] == last_year


@pytest.mark.parametrize("category", ["food", "FOOD", "Foods"])
def test_category_must_match_the_list_exactly(client, category):
    register(client)

    resp = client.post("/expenses/add", data=valid_form(category=category))

    assert resp.status_code == 200
    assert "Please choose a category." in resp.get_data(as_text=True)
    assert expense_rows() == []


@pytest.mark.parametrize("category", ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"])
def test_every_listed_category_is_accepted(client, category):
    register(client)

    resp = client.post("/expenses/add", data=valid_form(category=category))

    assert resp.status_code == 302
    assert expense_rows()[0]["category"] == category


def test_all_submitted_values_are_kept_after_an_error(client):
    register(client)
    past = (date.today() - timedelta(days=3)).isoformat()

    resp = client.post(
        "/expenses/add",
        data={"amount": "12.345", "category": "Health", "date": past, "description": "Pharmacy"},
    )
    body = resp.get_data(as_text=True)

    assert "at most 2 decimal places" in body
    assert 'value="12.345"' in body
    assert '<option value="Health" selected>' in body
    assert f'value="{past}"' in body
    assert 'value="Pharmacy"' in body


def test_date_input_max_allows_one_day_for_timezones(client):
    register(client)

    body = client.get("/expenses/add").get_data(as_text=True)

    assert f'max="{(date.today() + timedelta(days=1)).isoformat()}"' in body


def test_servers_tomorrow_is_accepted_for_users_ahead_of_the_server(client):
    register(client)
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    resp = client.post("/expenses/add", data=valid_form(date=tomorrow))

    assert resp.status_code == 302
    assert expense_rows()[0]["date"] == tomorrow


def test_fresh_form_defaults_to_the_browsers_today(client):
    register(client)

    body = client.get("/expenses/add").get_data(as_text=True)

    assert "data-default-to-local-today" in date_input(body)


def test_form_after_an_error_keeps_the_entered_date(client):
    register(client)
    past = (date.today() - timedelta(days=10)).isoformat()

    body = client.post("/expenses/add", data=valid_form(amount="0", date=past)).get_data(as_text=True)

    assert "data-default-to-local-today" not in date_input(body)
    assert f'value="{past}"' in date_input(body)


def test_success_message_is_shown_only_once(client):
    register(client)
    client.post("/expenses/add", data=valid_form())

    assert "Expense added." in client.get("/profile").get_data(as_text=True)
    assert "Expense added." not in client.get("/profile").get_data(as_text=True)


def test_nav_shows_add_expense_link_only_when_signed_in(client):
    assert 'href="/expenses/add"' not in client.get("/").get_data(as_text=True)

    register(client)

    assert 'href="/expenses/add"' in client.get("/").get_data(as_text=True)


def test_profile_has_add_expense_button(client):
    register(client)

    body = client.get("/profile").get_data(as_text=True)

    assert 'href="/expenses/add" class="btn-primary"' in body
