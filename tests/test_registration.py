from werkzeug.security import check_password_hash

import pytest

from database import db as db_module
from database import seed_dummy_user


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Patch DB_PATH before importing app, so that if this is the first test
    # in the session to `import app`, its module-level init_db()/seed_db()
    # call builds/seeds the tmp database rather than the real spendly.db.
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test_spendly.db")
    monkeypatch.delenv("APP_ENV", raising=False)

    import app as app_module

    # Every DB call reads db_module.DB_PATH fresh at call time (not at import
    # time), so re-running init_db() here guarantees the schema exists in
    # *this* test's tmp file regardless of whether `app` was already imported
    # by an earlier test against a different tmp_path.
    db_module.init_db()

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client


def test_get_register_still_renders_form(client):
    resp = client.get("/register")
    assert resp.status_code == 200
    assert b"Create your account" in resp.data


def test_successful_registration_creates_session_and_redirects(client):
    resp = client.post(
        "/register",
        data={"name": "Ada Lovelace", "email": "ada@example.com", "password": "supersecret"},
    )

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/profile"

    user = db_module.get_user_by_email("ada@example.com")
    assert user is not None
    assert user["name"] == "Ada Lovelace"
    assert check_password_hash(user["password_hash"], "supersecret")
    assert user["password_hash"] != "supersecret"

    with client.session_transaction() as sess:
        assert sess["user_id"] == user["id"]


def test_duplicate_email_rejected_without_creating_second_row(client):
    client.post(
        "/register",
        data={"name": "Ada Lovelace", "email": "ada@example.com", "password": "supersecret"},
    )

    resp = client.post(
        "/register",
        data={"name": "Someone Else", "email": "ada@example.com", "password": "anotherpass"},
    )

    assert resp.status_code == 200
    assert b"That email is already in use." in resp.data

    conn = db_module.get_db()
    count = conn.execute(
        "SELECT COUNT(*) AS count FROM users WHERE email = ?", ("ada@example.com",)
    ).fetchone()["count"]
    conn.close()
    assert count == 1


def test_empty_name_rejected(client):
    resp = client.post(
        "/register",
        data={"name": "", "email": "noname@example.com", "password": "supersecret"},
    )

    assert resp.status_code == 200
    assert b"Please enter your full name." in resp.data
    assert db_module.get_user_by_email("noname@example.com") is None


def test_invalid_email_rejected(client):
    resp = client.post(
        "/register",
        data={"name": "Bad Email", "email": "not-an-email", "password": "supersecret"},
    )

    assert resp.status_code == 200
    assert b"Please enter a valid email address." in resp.data
    assert db_module.get_user_by_email("not-an-email") is None


def test_short_password_rejected(client):
    resp = client.post(
        "/register",
        data={"name": "Short Pass", "email": "shortpass@example.com", "password": "short12"},
    )

    assert resp.status_code == 200
    assert b"Password must be at least 8 characters long." in resp.data
    assert db_module.get_user_by_email("shortpass@example.com") is None


def test_name_and_email_preserved_on_error_password_not(client):
    resp = client.post(
        "/register",
        data={"name": "Preserve Me", "email": "preserve@example.com", "password": "short"},
    )

    assert resp.status_code == 200
    assert b'value="Preserve Me"' in resp.data
    assert b'value="preserve@example.com"' in resp.data
    assert b"short" not in resp.data


def test_profile_redirects_when_not_authenticated(client):
    resp = client.get("/profile")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/login"


def test_profile_shows_correct_user_when_authenticated(client):
    client.post(
        "/register",
        data={"name": "Ada Lovelace", "email": "ada@example.com", "password": "supersecret"},
    )

    resp = client.get("/profile")

    assert resp.status_code == 200
    assert b"Ada Lovelace" in resp.data
    assert b"ada@example.com" in resp.data


def test_existing_demo_and_dummy_users_unaffected_by_registration(client):
    db_module.seed_db()
    seed_dummy_user.seed_dummy_user()

    demo_before = dict(db_module.get_user_by_email("demo@spendly.com"))
    dummy_before = dict(db_module.get_user_by_email(seed_dummy_user.DUMMY_EMAIL))

    conn = db_module.get_db()
    demo_expenses_before = conn.execute(
        "SELECT COUNT(*) AS count FROM expenses WHERE user_id = ?", (demo_before["id"],)
    ).fetchone()["count"]
    conn.close()

    client.post(
        "/register",
        data={"name": "New Person", "email": "newperson@example.com", "password": "supersecret"},
    )

    demo_after = dict(db_module.get_user_by_email("demo@spendly.com"))
    dummy_after = dict(db_module.get_user_by_email(seed_dummy_user.DUMMY_EMAIL))

    conn = db_module.get_db()
    demo_expenses_after = conn.execute(
        "SELECT COUNT(*) AS count FROM expenses WHERE user_id = ?", (demo_before["id"],)
    ).fetchone()["count"]
    conn.close()

    assert demo_after == demo_before
    assert dummy_after == dummy_before
    assert demo_expenses_after == demo_expenses_before
