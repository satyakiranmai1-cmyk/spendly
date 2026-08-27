"""Idempotent dummy-user seed for local development and slash-command testing.

Never run this against a production database — see the APP_ENV guard below.
"""

import os
import sys

from werkzeug.security import generate_password_hash

from database.db import get_db, init_db

DUMMY_NAME = "Dummy User"
DUMMY_EMAIL = "dummy@spendify.local"
DUMMY_USERNAME = "dummy_user"
DUMMY_STATUS = "active"
DUMMY_ENVIRONMENT = "development"
DEFAULT_DUMMY_PASSWORD = "dummy-dev-only-password"


def seed_dummy_user():
    app_env = os.environ.get("APP_ENV", "development").lower()
    if app_env == "production":
        print("ERROR: Dummy users cannot be created in production.", file=sys.stderr)
        sys.exit(1)

    init_db()
    conn = get_db()

    existing = conn.execute(
        "SELECT id, email, username FROM users WHERE email = ?", (DUMMY_EMAIL,)
    ).fetchone()

    if existing is not None:
        conn.close()
        print("Dummy user already exists.")
        print("Dummy user ready.")
        print(f"User ID: {existing['id']}")
        print(f"Email: {existing['email']}")
        print(f"Username: {existing['username']}")
        return existing["id"]

    password = os.environ.get("DUMMY_USER_PASSWORD", DEFAULT_DUMMY_PASSWORD)
    password_hash = generate_password_hash(password)

    conn.execute(
        """
        INSERT INTO users (name, email, password_hash, username, status, environment)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (DUMMY_NAME, DUMMY_EMAIL, password_hash, DUMMY_USERNAME, DUMMY_STATUS, DUMMY_ENVIRONMENT),
    )
    conn.commit()

    user_id = conn.execute(
        "SELECT id FROM users WHERE email = ?", (DUMMY_EMAIL,)
    ).fetchone()["id"]
    conn.close()

    print("Dummy user created.")
    print("Dummy user ready.")
    print(f"User ID: {user_id}")
    print(f"Email: {DUMMY_EMAIL}")
    print(f"Username: {DUMMY_USERNAME}")
    return user_id


def get_dummy_user():
    """Resolve the dummy user record, e.g. for development slash-command authentication."""
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (DUMMY_EMAIL,)).fetchone()
    conn.close()
    return row


if __name__ == "__main__":
    seed_dummy_user()
