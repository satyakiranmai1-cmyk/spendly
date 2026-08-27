import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash

DB_PATH = Path(__file__).parent.parent / "spendly.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            username TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            environment TEXT NOT NULL DEFAULT 'production',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
        """
    )
    _migrate_users_table(conn)
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users (username)")
    conn.commit()
    conn.close()


def _migrate_users_table(conn):
    """Add columns introduced after the original users table to pre-existing databases."""
    existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)")}
    added_columns = {
        "username": "ALTER TABLE users ADD COLUMN username TEXT",
        "status": "ALTER TABLE users ADD COLUMN status TEXT NOT NULL DEFAULT 'active'",
        "environment": "ALTER TABLE users ADD COLUMN environment TEXT NOT NULL DEFAULT 'production'",
    }
    for column, statement in added_columns.items():
        if column not in existing_columns:
            conn.execute(statement)


def get_user_by_email(email):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return row


def get_user_by_id(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row


def create_user(name, email, password_hash):
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def seed_db():
    conn = get_db()

    existing = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()
    if existing["count"] > 0:
        conn.close()
        return

    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
    )
    user_id = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
    ).fetchone()["id"]

    sample_expenses = [
        (user_id, 62.40, "Food", "Grocery run", "2026-08-02"),
        (user_id, 15.00, "Transport", "Metro card top-up", "2026-08-04"),
        (user_id, 89.99, "Bills", "Electricity bill", "2026-08-06"),
        (user_id, 45.00, "Health", "Pharmacy", "2026-08-09"),
        (user_id, 30.00, "Entertainment", "Movie night", "2026-08-12"),
        (user_id, 74.25, "Shopping", "New shoes", "2026-08-15"),
        (user_id, 20.00, "Other", "Miscellaneous", "2026-08-18"),
        (user_id, 38.50, "Food", "Dinner out", "2026-08-21"),
    ]
    conn.executemany(
        """
        INSERT INTO expenses (user_id, amount, category, description, date)
        VALUES (?, ?, ?, ?, ?)
        """,
        sample_expenses,
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    seed_db()
    print(f"Database initialized and seeded at {DB_PATH}")
