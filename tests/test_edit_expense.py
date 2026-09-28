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


def sign_out(client):
    with client.session_transaction() as sess:
        sess.clear()


def add_expense_row(user_id, amount=12.5, category="Food", expense_date="2026-09-01",
                    description="Lunch"):
    return db_module.create_expense(user_id, amount, category, expense_date, description)


def valid_form(**overrides):
    form = {
        "amount": "20.00",
        "category": "Transport",
        "date": date.today().isoformat(),
        "description": "Taxi",
    }
    form.update(overrides)
    return form


def expense_row(expense_id):
    conn = db_module.get_db()
    row = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    conn.close()
    return dict(row)


def expense_count():
    conn = db_module.get_db()
    count = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
    conn.close()
    return count


def test_signed_out_get_redirects_to_login(client):
    expense_id = add_expense_row(register(client))
    sign_out(client)

    resp = client.get(f"/expenses/{expense_id}/edit")

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/login"


def test_signed_out_post_redirects_and_changes_nothing(client):
    expense_id = add_expense_row(register(client))
    before = expense_row(expense_id)
    sign_out(client)

    resp = client.post(f"/expenses/{expense_id}/edit", data=valid_form())

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/login"
    assert expense_row(expense_id) == before


def test_get_shows_form_filled_with_stored_values(client):
    expense_id = add_expense_row(register(client))

    resp = client.get(f"/expenses/{expense_id}/edit")

    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Edit expense" in body
    assert "Save changes" in body
    assert f'action="/expenses/{expense_id}/edit"' in body
    assert 'value="12.50"' in body
    assert '<option value="Food" selected>' in body
    assert 'value="2026-09-01"' in body
    assert 'value="Lunch"' in body
    date_input = re.search(r'<input type="date"[^>]*>', body).group(0)
    assert "data-default-to-local-today" not in date_input


def test_get_shows_null_description_as_empty(client):
    expense_id = add_expense_row(register(client), description=None)

    body = client.get(f"/expenses/{expense_id}/edit").get_data(as_text=True)

    assert "None" not in body
    assert 'name="description"' in body


@pytest.mark.parametrize("method", ["get", "post"])
def test_other_users_expense_returns_404(client, method):
    other_expense = add_expense_row(register(client, email="other@example.com"))
    before = expense_row(other_expense)
    sign_out(client)
    register(client)

    resp = getattr(client, method)(f"/expenses/{other_expense}/edit", data=valid_form())

    assert resp.status_code == 404
    assert expense_row(other_expense) == before


@pytest.mark.parametrize("method", ["get", "post"])
def test_missing_expense_returns_404(client, method):
    register(client)

    resp = getattr(client, method)("/expenses/9999/edit", data=valid_form())

    assert resp.status_code == 404
    assert expense_count() == 0


def test_valid_post_updates_expense_and_flashes(client):
    user_id = register(client)
    expense_id = add_expense_row(user_id)
    before = expense_row(expense_id)

    resp = client.post(f"/expenses/{expense_id}/edit", data=valid_form())

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/profile"
    row = expense_row(expense_id)
    assert row["amount"] == 20.0
    assert row["category"] == "Transport"
    assert row["date"] == date.today().isoformat()
    assert row["description"] == "Taxi"
    assert row["user_id"] == user_id
    assert row["created_at"] == before["created_at"]
    assert expense_count() == 1
    assert "Expense updated." in client.get("/profile").get_data(as_text=True)


def test_only_the_edited_expense_changes(client):
    user_id = register(client)
    edited = add_expense_row(user_id)
    untouched = add_expense_row(user_id, description="Coffee")
    before = expense_row(untouched)

    client.post(f"/expenses/{edited}/edit", data=valid_form())

    assert expense_row(untouched) == before


def test_blank_description_is_stored_as_null(client):
    expense_id = add_expense_row(register(client))

    client.post(f"/expenses/{expense_id}/edit", data=valid_form(description="   "))

    assert expense_row(expense_id)["description"] is None


@pytest.mark.parametrize(
    "days_from_today, accepted",
    [(-365, True), (1, True), (2, False)],
)
def test_date_limits(client, days_from_today, accepted):
    expense_id = add_expense_row(register(client))
    new_date = (date.today() + timedelta(days=days_from_today)).isoformat()

    resp = client.post(f"/expenses/{expense_id}/edit", data=valid_form(date=new_date))

    assert (resp.status_code == 302) is accepted
    assert (expense_row(expense_id)["date"] == new_date) is accepted


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
        {"description": "x" * 201},
    ],
)
def test_invalid_input_is_rejected_and_values_kept(client, overrides):
    expense_id = add_expense_row(register(client))
    before = expense_row(expense_id)
    form = valid_form(**overrides)

    resp = client.post(f"/expenses/{expense_id}/edit", data=form)

    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'class="auth-error"' in body
    assert expense_row(expense_id) == before
    if len(form["description"]) <= 200:
        assert f'value="{form["description"]}"' in body


def test_user_id_and_id_in_form_are_ignored(client):
    other_id = register(client, email="other@example.com")
    sign_out(client)
    user_id = register(client)
    expense_id = add_expense_row(user_id)

    client.post(
        f"/expenses/{expense_id}/edit",
        data=valid_form(user_id=str(other_id), id="9999"),
    )

    row = expense_row(expense_id)
    assert row["user_id"] == user_id
    assert row["description"] == "Taxi"


def test_profile_shows_edit_link_for_each_expense(client):
    user_id = register(client)
    first = add_expense_row(user_id)
    second = add_expense_row(user_id, category="Bills", amount=80)

    body = client.get("/profile").get_data(as_text=True)

    assert f'href="/expenses/{first}/edit"' in body
    assert f'href="/expenses/{second}/edit"' in body
    assert 'aria-label="Edit Bills expense of $80.00"' in body
