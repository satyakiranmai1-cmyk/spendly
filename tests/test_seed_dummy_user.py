import pytest

from database import db as db_module
from database import seed_dummy_user as seed_module


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    """Point the app at a throwaway database file for each test."""
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test_spendly.db")
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("DUMMY_USER_PASSWORD", raising=False)


def test_seed_creates_dummy_user(isolated_db, monkeypatch, capsys):
    monkeypatch.setenv("APP_ENV", "development")

    user_id = seed_module.seed_dummy_user()

    conn = db_module.get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (seed_module.DUMMY_EMAIL,)
    ).fetchone()
    conn.close()

    assert row is not None
    assert row["id"] == user_id
    assert row["email"] == seed_module.DUMMY_EMAIL
    assert row["username"] == seed_module.DUMMY_USERNAME
    assert row["status"] == seed_module.DUMMY_STATUS
    assert row["environment"] == seed_module.DUMMY_ENVIRONMENT
    assert row["password_hash"] != seed_module.DEFAULT_DUMMY_PASSWORD
    assert "Dummy user created." in capsys.readouterr().out


def test_seed_is_idempotent(isolated_db, monkeypatch, capsys):
    monkeypatch.setenv("APP_ENV", "development")

    first_id = seed_module.seed_dummy_user()
    capsys.readouterr()
    second_id = seed_module.seed_dummy_user()

    assert first_id == second_id
    assert "Dummy user already exists." in capsys.readouterr().out

    conn = db_module.get_db()
    count = conn.execute(
        "SELECT COUNT(*) AS count FROM users WHERE email = ?",
        (seed_module.DUMMY_EMAIL,),
    ).fetchone()["count"]
    conn.close()
    assert count == 1


def test_dummy_user_resolves_for_slash_commands(isolated_db, monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    seed_module.seed_dummy_user()

    resolved = seed_module.get_dummy_user()

    assert resolved is not None
    assert resolved["email"] == seed_module.DUMMY_EMAIL
    assert resolved["username"] == seed_module.DUMMY_USERNAME


def test_seed_refuses_in_production(isolated_db, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")

    with pytest.raises(SystemExit) as exc_info:
        seed_module.seed_dummy_user()
    assert exc_info.value.code == 1

    db_module.init_db()
    conn = db_module.get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (seed_module.DUMMY_EMAIL,)
    ).fetchone()
    conn.close()
    assert row is None
