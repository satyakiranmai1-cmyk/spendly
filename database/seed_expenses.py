"""Seed realistic dummy expense records into the existing spendly.db for local
development, UI testing, and duration-wise dashboard/chart validation.

Reuses database.db's connection layer and expenses schema — no separate
database or parallel table is created. Never run against production data;
see the APP_ENV guard below.
"""

import argparse
import os
import random
import sys
from datetime import date, datetime, timedelta

from database.db import get_db, get_user_by_email, init_db

DEFAULT_USER_EMAIL = "dummy@spendify.local"
SEED_SOURCE = "seed-expenses"
MAX_COUNT = int(os.environ.get("SEED_EXPENSES_MAX_COUNT", "5000"))

DURATION_DAYS = {
    "7d": 7,
    "30d": 30,
    "3m": 90,
    "6m": 182,
    "12m": 365,
}

DURATION_LABELS = {
    "7d": "Last 7 days",
    "30d": "Last 30 days",
    "3m": "Last 3 months",
    "6m": "Last 6 months",
    "12m": "Last 12 months",
    "custom": "Custom range",
}

# (description/merchant, min amount, max amount) per existing app category.
CATEGORY_TEMPLATES = {
    "Food": [
        ("Restaurant dinner", 12.0, 60.0),
        ("Coffee shop", 3.5, 12.0),
        ("Lunch with colleagues", 8.0, 25.0),
        ("Fast food", 6.0, 20.0),
        ("Bakery treats", 4.0, 15.0),
    ],
    "Transport": [
        ("Ride share", 6.0, 35.0),
        ("Metro card top-up", 10.0, 40.0),
        ("Gas fill-up", 25.0, 80.0),
        ("Parking fee", 3.0, 20.0),
        ("Bike rental", 5.0, 25.0),
    ],
    "Bills": [
        ("Electricity bill", 40.0, 150.0),
        ("Internet bill", 30.0, 90.0),
        ("Water bill", 15.0, 60.0),
        ("Phone bill", 25.0, 85.0),
        ("Insurance premium", 50.0, 200.0),
    ],
    "Health": [
        ("Pharmacy", 8.0, 60.0),
        ("Doctor visit", 30.0, 150.0),
        ("Gym membership", 20.0, 70.0),
        ("Dental checkup", 40.0, 180.0),
        ("Vitamins", 10.0, 35.0),
    ],
    "Entertainment": [
        ("Movie night", 10.0, 40.0),
        ("Concert tickets", 30.0, 120.0),
        ("Streaming subscription", 8.0, 20.0),
        ("Video game", 15.0, 70.0),
        ("Bowling", 12.0, 45.0),
    ],
    "Shopping": [
        ("New shoes", 30.0, 120.0),
        ("Clothing", 20.0, 100.0),
        ("Electronics accessory", 10.0, 90.0),
        ("Home decor", 15.0, 80.0),
        ("Books", 8.0, 40.0),
    ],
    "Other": [
        ("Miscellaneous", 5.0, 50.0),
        ("Gift", 10.0, 80.0),
        ("Donation", 5.0, 100.0),
        ("Repair service", 15.0, 120.0),
        ("Misc supplies", 5.0, 40.0),
    ],
}

CATEGORIES = list(CATEGORY_TEMPLATES)


class SeedExpensesError(ValueError):
    """Raised for invalid seeding input; message is safe to show to the user."""


def _migrate_expenses_table(conn):
    existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(expenses)")}
    if "source" not in existing_columns:
        conn.execute("ALTER TABLE expenses ADD COLUMN source TEXT")


def _resolve_duration(duration, start, end):
    if duration == "custom":
        if not start or not end:
            raise SeedExpensesError("Custom duration requires both a start and an end date.")
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d").date()
        except ValueError:
            raise SeedExpensesError(f"Invalid start date '{start}'; expected YYYY-MM-DD.")
        try:
            end_date = datetime.strptime(end, "%Y-%m-%d").date()
        except ValueError:
            raise SeedExpensesError(f"Invalid end date '{end}'; expected YYYY-MM-DD.")
        if start_date > end_date:
            raise SeedExpensesError("Start date must not be after end date.")
        label = f"Custom ({start_date} to {end_date})"
        return start_date, end_date, label

    if duration not in DURATION_DAYS:
        valid = ", ".join(list(DURATION_DAYS) + ["custom"])
        raise SeedExpensesError(f"Unknown duration '{duration}'. Valid options: {valid}.")

    end_date = date.today()
    start_date = end_date - timedelta(days=DURATION_DAYS[duration] - 1)
    return start_date, end_date, DURATION_LABELS[duration]


def _resolve_user_id(conn, user_email, user_id):
    if user_id is not None:
        row = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None:
            raise SeedExpensesError(f"No user found with id {user_id}.")
        return row["id"]

    email = user_email or DEFAULT_USER_EMAIL
    row = get_user_by_email(email)
    if row is None:
        raise SeedExpensesError(
            f"No user found with email '{email}'. Run the seed-user command first, "
            "or pass --user-email/--user-id for an existing user."
        )
    return row["id"]


def _random_date(start_date, end_date, rng):
    span_days = (end_date - start_date).days
    offset = rng.randint(0, span_days) if span_days > 0 else 0
    return start_date + timedelta(days=offset)


def generate_expense_rows(count, start_date, end_date, user_id, rng):
    rows = []
    for _ in range(count):
        category = rng.choice(CATEGORIES)
        description, low, high = rng.choice(CATEGORY_TEMPLATES[category])
        amount = round(rng.uniform(low, high), 2)
        expense_date = _random_date(start_date, end_date, rng)
        rows.append(
            (user_id, amount, category, description, expense_date.isoformat(), SEED_SOURCE)
        )
    return rows


def seed_expenses(
    count,
    duration="30d",
    start=None,
    end=None,
    user_email=None,
    user_id=None,
    seed=None,
    max_count=MAX_COUNT,
):
    app_env = os.environ.get("APP_ENV", "development").lower()
    if app_env == "production":
        raise SeedExpensesError("Dummy expenses cannot be seeded in production.")

    if not isinstance(count, int) or isinstance(count, bool):
        raise SeedExpensesError("Number of expenses must be a positive integer.")
    if count <= 0:
        raise SeedExpensesError("Number of expenses must be a positive integer.")
    if count > max_count:
        raise SeedExpensesError(f"Number of expenses must not exceed {max_count}.")

    start_date, end_date, duration_label = _resolve_duration(duration, start, end)

    init_db()
    conn = get_db()
    try:
        _migrate_expenses_table(conn)
        resolved_user_id = _resolve_user_id(conn, user_email, user_id)

        rng = random.Random(seed)
        rows = generate_expense_rows(count, start_date, end_date, resolved_user_id, rng)

        conn.executemany(
            """
            INSERT INTO expenses (user_id, amount, category, description, date, source)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {
        "created": count,
        "duration": duration_label,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "user_id": resolved_user_id,
    }


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Seed dummy expenses into spendly.db")
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument(
        "--duration", choices=list(DURATION_DAYS) + ["custom"], default="30d"
    )
    parser.add_argument("--start", help="Start date (YYYY-MM-DD), required for --duration custom")
    parser.add_argument("--end", help="End date (YYYY-MM-DD), required for --duration custom")
    parser.add_argument("--user-email", default=None)
    parser.add_argument("--user-id", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    try:
        result = seed_expenses(
            count=args.count,
            duration=args.duration,
            start=args.start,
            end=args.end,
            user_email=args.user_email,
            user_id=args.user_id,
            seed=args.seed,
        )
    except SeedExpensesError as exc:
        print("Expense seeding failed.\n")
        print("No expense records were added.")
        print(f"Reason: {exc}")
        sys.exit(1)

    print("Expense seeding completed.\n")
    print(f"Expenses created: {result['created']}")
    print(f"Duration: {result['duration']}")
    print(f"Date range: {result['start_date']} to {result['end_date']}")
    print()
    print("The new expenses are now available in the Spendly expense tracker.")


if __name__ == "__main__":
    main()
