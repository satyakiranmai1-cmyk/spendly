import os
import re
import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import (
    create_expense,
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

EXPENSE_CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]
MAX_EXPENSE_AMOUNT = Decimal("10000000")
MAX_DESCRIPTION_LENGTH = 200


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped_view


def _validate_expense_form(form):
    """Return (cleaned_data, error) for a submitted expense form; error is None when valid."""
    raw_amount = form.get("amount", "").strip()
    category = form.get("category", "").strip()
    raw_date = form.get("date", "").strip()
    description = form.get("description", "").strip()

    try:
        amount = Decimal(raw_amount)
    except InvalidOperation:
        amount = None

    try:
        expense_date = date.fromisoformat(raw_date)
    except ValueError:
        expense_date = None

    if amount is None or not amount.is_finite():
        return None, "Please enter a valid amount."
    if amount <= 0:
        return None, "Amount must be greater than zero."
    if amount > MAX_EXPENSE_AMOUNT:
        return None, "Amount must be 10,000,000 or less."
    if amount != amount.quantize(Decimal("0.01")):
        return None, "Amount can have at most 2 decimal places."
    if category not in EXPENSE_CATEGORIES:
        return None, "Please choose a category."
    if expense_date is None:
        return None, "Please enter a valid date."
    if expense_date > date.today():
        return None, "Date can't be in the future."
    if len(description) > MAX_DESCRIPTION_LENGTH:
        return None, f"Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer."

    return {
        "amount": float(amount),
        "category": category,
        "date": expense_date.isoformat(),
        "description": description or None,
    }, None

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
    summary = get_expense_summary_by_user(user["id"])
    days = get_expenses_by_day(user["id"])
    for day in days:
        try:
            day["display_date"] = date.fromisoformat(day["date"]).strftime("%A, %B %d, %Y")
        except ValueError:
            day["display_date"] = day["date"]
    return render_template("profile.html", user=user, summary=summary, days=days)


@app.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    today = date.today().isoformat()

    if request.method == "GET":
        if get_user_by_id(session["user_id"]) is None:
            session.pop("user_id", None)
            return redirect(url_for("login"))
        return render_template(
            "add_expense.html", categories=EXPENSE_CATEGORIES, today=today, form={"date": today}
        )

    expense, error = _validate_expense_form(request.form)
    if error:
        return render_template(
            "add_expense.html",
            categories=EXPENSE_CATEGORIES,
            today=today,
            form=request.form,
            error=error,
        )

    try:
        create_expense(session["user_id"], **expense)
    except sqlite3.IntegrityError:
        session.pop("user_id", None)
        return redirect(url_for("login"))

    flash("Expense added.", "success")
    return redirect(url_for("profile"))


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8" 


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
