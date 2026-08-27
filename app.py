import os
import re
import sqlite3
from functools import wraps

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from database.db import create_user, get_db, get_user_by_email, get_user_by_id, init_db, seed_db

app = Flask(__name__)
# WARNING: fallback is for local dev only — always set FLASK_SECRET_KEY in any real deployment.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-insecure-secret-key-change-me")

with app.app_context():
    init_db()
    seed_db()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped_view


# ------------------------------------------------------------------ #
# Routes                                                              #
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


@app.route("/login")
def login():
    return render_template("login.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    return "Logout — coming in Step 3"


@app.route("/profile")
@login_required
def profile():
    user = get_user_by_id(session["user_id"])
    if user is None:
        session.pop("user_id", None)
        return redirect(url_for("login"))
    return render_template("profile.html", user=user)


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
