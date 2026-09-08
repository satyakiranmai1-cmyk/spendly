import calendar
import os
import re
import sqlite3
from datetime import date, datetime, timedelta
from functools import wraps

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import (
    create_user,
    get_db,
    get_expense_summary_by_user,
    get_expenses_by_day,
    get_user_by_email,
    get_user_by_id,
    init_db,
    seed_db,
)

app = Flask(__name__)
# WARNING: fallback is for local dev only — always set FLASK_SECRET_KEY in any real deployment.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-insecure-secret-key-change-me")

with app.app_context():
    init_db()
    seed_db()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _parse_date_param(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _current_month_range(today):
    start = today.replace(day=1)
    last_day = calendar.monthrange(today.year, today.month)[1]
    end = date(today.year, today.month, last_day)
    return start, end


def _build_date_presets(today):
    month_start, month_end = _current_month_range(today)
    return [
        {"key": "this_month", "label": "This month", "start": month_start, "end": month_end},
        {"key": "last_30", "label": "Last 30 days", "start": today - timedelta(days=29), "end": today},
        {"key": "last_6_months", "label": "Last 6 months", "start": today - timedelta(days=181), "end": today},
        {"key": "all", "label": "All time", "start": None, "end": None},
    ]


def _attach_display_dates(days):
    for day in days:
        try:
            day["display_date"] = datetime.strptime(day["date"], "%Y-%m-%d").strftime(
                "%A, %B %d, %Y"
            )
        except ValueError:
            day["display_date"] = day["date"]


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped_view

# ------------------------------------------------------------------ #
# Routs                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not name:
        error = "Please enter your full name."
    elif not EMAIL_RE.match(email):
        error = "Please enter a valid email address."
    elif len(password) < 8:
        error = "Password must be at least 8 characters long."
    elif get_user_by_email(email) is not None:
        error = "That email is already in use."
    else:
        error = None

    if error:
        return render_template("register.html", error=error, name=name, email=email)

    password_hash = generate_password_hash(password)
    try:
        user_id = create_user(name, email, password_hash)
    except sqlite3.IntegrityError:
        return render_template(
            "register.html",
            error="That email is already in use.",
            name=name,
            email=email,
        )

    session["user_id"] = user_id
    return redirect(url_for("profile"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    user = get_user_by_email(email) if email else None

    if not email or not password or user is None or not check_password_hash(
        user["password_hash"], password
    ):
        return render_template(
            "login.html", error="Invalid email or password.", email=email
        )

    session["user_id"] = user["id"]
    return redirect(url_for("profile"))


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("landing"))


@app.route("/expenses")
@login_required
def expenses_statement():
    user = get_user_by_id(session["user_id"])
    if user is None:
        session.pop("user_id", None)
        return redirect(url_for("login"))

    days = get_expenses_by_day(user["id"])
    _attach_display_dates(days)

    summary = get_expense_summary_by_user(user["id"])
    return render_template("expenses.html", days=days, summary=summary)


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/profile")
@login_required
def profile():
    user = get_user_by_id(session["user_id"])
    if user is None:
        session.pop("user_id", None)
        return redirect(url_for("login"))

    today = date.today()
    presets = _build_date_presets(today)
    month_start, month_end = _current_month_range(today)

    if request.args.get("range") == "all":
        start_date, end_date = None, None
    else:
        raw_start = request.args.get("start_date", "")
        raw_end = request.args.get("end_date", "")
        parsed_start = _parse_date_param(raw_start)
        parsed_end = _parse_date_param(raw_end)
        if not raw_start and not raw_end:
            start_date, end_date = month_start, month_end
        elif parsed_start and parsed_end and parsed_start <= parsed_end:
            start_date, end_date = parsed_start, parsed_end
        else:
            start_date, end_date = month_start, month_end

    db_start = start_date.isoformat() if start_date else None
    db_end = end_date.isoformat() if end_date else None

    summary = get_expense_summary_by_user(user["id"], db_start, db_end)
    days = get_expenses_by_day(user["id"], db_start, db_end)
    _attach_display_dates(days)

    for preset in presets:
        if preset["key"] == "all":
            preset["href"] = url_for("profile", range="all")
        else:
            preset["href"] = url_for(
                "profile", start_date=preset["start"].isoformat(), end_date=preset["end"].isoformat()
            )

    active_preset = next(
        (p["key"] for p in presets if p["start"] == start_date and p["end"] == end_date), None
    )

    member_since = None
    if user["created_at"]:
        try:
            member_since = datetime.strptime(user["created_at"], "%Y-%m-%d %H:%M:%S").strftime(
                "%B %d, %Y"
            )
        except ValueError:
            member_since = user["created_at"]
    return render_template(
        "profile.html",
        user=user,
        summary=summary,
        member_since=member_since,
        days=days,
        filter_start=start_date,
        filter_end=end_date,
        presets=presets,
        active_preset=active_preset,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8" 


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
