import sqlite3
from datetime import date, timedelta

import pytest

from database import db as db_module
from database import seed_dummy_user
from database import seed_expenses as seed_module


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test_spendly.db")
    monkeypatch.delenv("APP_ENV", raising=False)
    db_module.init_db()
    seed_dummy_user.seed_dummy_user()
    return db_module.get_user_by_email(seed_dummy_user.DUMMY_EMAIL)["id"]


def _expense_count(email=seed_dummy_user.DUMMY_EMAIL):
    conn = db_module.get_db()
    row = conn.execute(
        """
        SELECT COUNT(*) AS count FROM expenses
        JOIN users ON users.id = expenses.user_id
        WHERE users.email = ?
        """,
        (email,),
    ).fetchone()
    conn.close()
    return row["count"]


def test_number_selection_creates_requested_count(isolated_db):
    result = seed_module.seed_expenses(count=25, duration="30d", seed=1)

    assert result["created"] == 25
    assert _expense_count() == 25


def test_duration_selection_confines_dates_to_range(isolated_db):
    result = seed_module.seed_expenses(count=20, duration="3m", seed=2)

    start = date.fromisoformat(result["start_date"])
    end = date.fromisoformat(result["end_date"])
    assert (end - start).days == 89
    assert result["duration"] == "Last 3 months"

    conn = db_module.get_db()
    dates = [
        date.fromisoformat(row["date"])
        for row in conn.execute("SELECT date FROM expenses WHERE source = ?", (seed_module.SEED_SOURCE,))
    ]
    conn.close()
    assert all(start <= d <= end for d in dates)


def test_custom_date_range(isolated_db):
    start = (date.today() - timedelta(days=10)).isoformat()
    end = date.today().isoformat()

    result = seed_module.seed_expenses(count=5, duration="custom", start=start, end=end, seed=3)

    assert result["start_date"] == start
    assert result["end_date"] == end
    assert _expense_count() == 5


@pytest.mark.parametrize("count", [0, -5, 100000])
def test_invalid_number_is_rejected(isolated_db, count):
    with pytest.raises(seed_module.SeedExpensesError):
        seed_module.seed_expenses(count=count, duration="30d")
    assert _expense_count() == 0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"duration": "custom", "start": "2026-05-10", "end": "2026-05-01"},
        {"duration": "custom", "start": "not-a-date", "end": "2026-05-01"},
        {"duration": "custom", "start": "2026-05-01", "end": None},
        {"duration": "unknown-period"},
    ],
)
def test_invalid_date_range_is_rejected(isolated_db, kwargs):
    with pytest.raises(seed_module.SeedExpensesError):
        seed_module.seed_expenses(count=10, **kwargs)
    assert _expense_count() == 0


def test_successful_insertion_uses_dummy_user_and_tags_source(isolated_db):
    seed_module.seed_expenses(count=8, duration="7d", seed=4)

    conn = db_module.get_db()
    rows = conn.execute(
        "SELECT user_id, amount, category, source FROM expenses WHERE source = ?",
        (seed_module.SEED_SOURCE,),
    ).fetchall()
    conn.close()

    assert len(rows) == 8
    for row in rows:
        assert row["user_id"] == isolated_db
        assert row["amount"] > 0
        assert row["category"] in seed_module.CATEGORIES
        assert row["source"] == seed_module.SEED_SOURCE


def test_transaction_rollback_on_failure(isolated_db, monkeypatch):
    baseline = _expense_count()

    def broken_rows(count, start_date, end_date, user_id, rng):
        return [(None, 10.0, "Food", "broken row", start_date.isoformat(), "seed-expenses")]

    monkeypatch.setattr(seed_module, "generate_expense_rows", broken_rows)

    with pytest.raises(sqlite3.IntegrityError):
        seed_module.seed_expenses(count=1, duration="7d")

    assert _expense_count() == baseline


def test_existing_records_remain_unchanged(isolated_db):
    conn = db_module.get_db()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, description, date) VALUES (?, ?, ?, ?, ?)",
        (isolated_db, 42.0, "Food", "pre-existing manual entry", "2026-01-01"),
    )
    conn.commit()
    conn.close()

    seed_module.seed_expenses(count=15, duration="30d", seed=5)

    conn = db_module.get_db()
    preexisting = conn.execute(
        "SELECT * FROM expenses WHERE description = 'pre-existing manual entry'"
    ).fetchone()
    total = conn.execute("SELECT COUNT(*) AS count FROM expenses").fetchone()["count"]
    conn.close()

    assert preexisting is not None
    assert preexisting["amount"] == 42.0
    assert total == 16  # 1 pre-existing + 15 seeded


def test_duration_wise_aggregation(isolated_db):
    seed_module.seed_expenses(count=50, duration="6m", seed=6)

    conn = db_module.get_db()
    row = conn.execute(
        """
        SELECT COUNT(*) AS count, SUM(amount) AS total, AVG(amount) AS avg
        FROM expenses WHERE source = ?
        """,
        (seed_module.SEED_SOURCE,),
    ).fetchone()
    monthly = conn.execute(
        """
        SELECT strftime('%Y-%m', date) AS month, COUNT(*) AS count, SUM(amount) AS total
        FROM expenses WHERE source = ?
        GROUP BY month
        ORDER BY month
        """,
        (seed_module.SEED_SOURCE,),
    ).fetchall()
    conn.close()

    assert row["count"] == 50
    assert row["total"] > 0
    assert row["avg"] > 0
    assert len(monthly) >= 1
    assert sum(m["count"] for m in monthly) == 50


def test_seed_refuses_in_production(isolated_db, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")

    with pytest.raises(seed_module.SeedExpensesError):
        seed_module.seed_expenses(count=10, duration="30d")

    assert _expense_count() == 0
