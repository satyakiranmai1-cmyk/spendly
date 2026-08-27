import pytest

from database import db as db_module


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


def register(client, name="Ada Lovelace", email="ada@example.com", password="supersecret"):
    return client.post(
        "/register", data={"name": name, "email": email, "password": password}
    )


def test_get_login_still_renders_form(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"Welcome back" in resp.data


def test_successful_login_for_registered_user_creates_session_and_redirects(client):
    register(client, email="ada@example.com", password="supersecret")
    with client.session_transaction() as sess:
        sess.clear()

    resp = client.post(
        "/login", data={"email": "ada@example.com", "password": "supersecret"}
    )

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/profile"

    user = db_module.get_user_by_email("ada@example.com")
    with client.session_transaction() as sess:
        assert sess["user_id"] == user["id"]


def test_successful_login_for_seeded_demo_user(client):
    db_module.seed_db()

    resp = client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/profile"

    user = db_module.get_user_by_email("demo@spendly.com")
    with client.session_transaction() as sess:
        assert sess["user_id"] == user["id"]


def test_wrong_password_rejected_with_generic_error_and_email_preserved(client):
    register(client, email="ada@example.com", password="supersecret")
    with client.session_transaction() as sess:
        sess.clear()

    resp = client.post("/login", data={"email": "ada@example.com", "password": "wrongpass"})

    assert resp.status_code == 200
    assert b"Invalid email or password." in resp.data
    assert b'value="ada@example.com"' in resp.data
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_unknown_email_rejected_with_same_generic_error(client):
    resp = client.post(
        "/login", data={"email": "nobody@example.com", "password": "whatever1"}
    )

    assert resp.status_code == 200
    assert b"Invalid email or password." in resp.data
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_empty_email_rejected(client):
    resp = client.post("/login", data={"email": "", "password": "supersecret"})

    assert resp.status_code == 200
    assert b"Invalid email or password." in resp.data
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_empty_password_rejected(client):
    register(client, email="ada@example.com", password="supersecret")
    with client.session_transaction() as sess:
        sess.clear()

    resp = client.post("/login", data={"email": "ada@example.com", "password": ""})

    assert resp.status_code == 200
    assert b"Invalid email or password." in resp.data
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_logout_clears_session_and_redirects_to_landing(client):
    register(client, email="ada@example.com", password="supersecret")

    resp = client.get("/logout")

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/"
    with client.session_transaction() as sess:
        assert "user_id" not in sess

    profile_resp = client.get("/profile")
    assert profile_resp.status_code == 302
    assert profile_resp.headers["Location"] == "/login"


def test_nav_shows_signed_out_links_when_not_authenticated(client):
    resp = client.get("/")

    assert b"Sign in" in resp.data
    assert b"Get started" in resp.data
    assert b"Sign out" not in resp.data


def test_nav_shows_signed_in_links_when_authenticated(client):
    register(client, email="ada@example.com", password="supersecret")

    resp = client.get("/profile")

    assert b"Profile" in resp.data
    assert b"Sign out" in resp.data
    assert b"Get started" not in resp.data
