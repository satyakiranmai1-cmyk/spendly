# Step 06 - Add Expenses

## Branch

`feature/add-expenses` (created from `main`)

## Objective

Let a signed-in Spendly user record a new expense (amount, category, date, optional description) through a form, saving it against their own account in `spendly.db`. This replaces the `/expenses/add` placeholder (`"Add expense — coming in Step 7"`) in `app.py` with a working, validated, login-protected feature.

## Assumptions requiring confirmation

1. **Where to redirect after a successful add.** On `main`, `/profile` only shows name and email — the expense summary/list lives on the unmerged branches `feature/profile-page-design` and `feature/profile-page-date-filter`. This spec redirects to `/profile` with a flash message ("Expense added.") so the feature works on `main` today. Once the profile expense list is merged, the new expense will show up there with no further change to this route.
2. **Fixed category list.** Categories are a fixed set matching the existing seed data: `Food`, `Transport`, `Bills`, `Health`, `Entertainment`, `Shopping`, `Other`. No user-defined categories in this step.
3. **Future dates are rejected.** An expense records money already spent, so `date` must be the user's today or earlier. The server can't know the user's timezone, so it allows up to one day past its own date. The browser limits the date field to the user's own today. (Changed after code review: using only the server's date blocked users ahead of it, e.g. in India on a UTC server, from logging today's expenses between 00:00 and 05:30.)
4. **Flash messages.** The app does not use `flash()` yet. This spec adds a small flash-message block to `base.html` so the success message can be shown on any page.
5. **Amount limits.** Amount must be `> 0` and `<= 10,000,000`, with at most 2 decimal places.

## Database Impact

**No schema changes required.**

- **Existing table used:** `expenses` (`id`, `user_id`, `amount REAL NOT NULL`, `category TEXT NOT NULL`, `description TEXT`, `date TEXT NOT NULL`, `created_at` default `datetime('now')`).
- **Relationship:** `expenses.user_id → users.id` (`ON DELETE CASCADE`), already enforced with `PRAGMA foreign_keys = ON` in `get_db()`.
- **New tables / columns / indexes:** none.
- **Migration:** none. Existing data (3 users, 93 expenses in the local DB) is untouched. The feature only runs `INSERT`s.
- **Data validation (enforced in the app, before the INSERT):**
  - `amount`: required, numeric, `> 0`, `<= 10,000,000`, at most 2 decimal places. Stored rounded to 2 decimals.
  - `category`: required, must be one of the fixed categories.
  - `date`: required, valid `YYYY-MM-DD`, and no later than the server's today plus one day (see assumption 3).
  - `description`: optional, trimmed, max 200 characters. An empty string is stored as `NULL`.
  - `user_id`: always taken from `session["user_id"]`, never from form input.

## UI / Webpage Impact

- **New template `templates/add_expense.html`** (extends `base.html`) reuses the existing `auth-section` / `auth-container` / `auth-card` / `form-group` / `form-input` / `btn-submit` / `auth-error` classes, so no new visual language is needed:
  - Header: "Add an expense" / "Record what you spent".
  - `amount`: `<input type="number" step="0.01" min="0.01" required>`
  - `category`: `<select required>` with the fixed categories and a disabled "Choose a category" placeholder.
  - `date`: `<input type="date" required>`. The server sets `max` to its today plus one day. A small script then sets `max` to the browser's own today and, on a fresh form, the default value too. After an error, the value the user entered is kept.
  - `description`: `<input type="text" maxlength="200">`, optional.
  - Submit button: "Add expense". A secondary "Cancel" link goes back to `/profile`.
  - On a validation error, show the error in the existing `.auth-error` box and re-fill all submitted values.
- **`templates/base.html`:**
  - Add an "Add expense" link to the signed-in navbar (between "Profile" and "Sign out").
  - Add a flash-message block above `{% block content %}`.
- **`templates/profile.html`:** add an "Add expense" button (`btn-primary`) below the account-details card.
- **`static/css/style.css`:** add only what is new — a `.flash` / `.flash-success` style and a `select.form-input` tweak (native arrow, same height as the text inputs). The layout must still work at phone width.

## Backend Impact

- **Route:** `/expenses/add`, `methods=["GET", "POST"]`, decorated with `@login_required`. The placeholder currently has **no** auth check, so adding it fixes that gap.
  - `GET` renders `add_expense.html` with `categories`, `today`, and empty form values.
  - `POST` validates the form. On failure it re-renders with `error=` and the submitted values (HTTP 200, matching how `/register` and `/login` handle errors). On success it calls `create_expense(...)`, flashes "Expense added.", and redirects (302) to `/profile`.
- **Business logic:** add a validation helper in `app.py` (for example `_validate_expense_form(form)`) that returns `(cleaned_data, error)` and returns the first error only, like `register()` does. Keep `EXPENSE_CATEGORIES` as a module-level constant in `app.py` so the template and the validator share one list.
- **Database query (`database/db.py`):** add
  ```python
  def create_expense(user_id, amount, category, date, description=None):
      # INSERT INTO expenses (user_id, amount, category, description, date) VALUES (?, ?, ?, ?, ?)
      # returns cursor.lastrowid
  ```
  following the same `get_db()` / `try` / `commit` / `finally: close()` pattern as `create_user`. Use parameterized SQL only.
- **Validation:** all checks run on the server. The HTML attributes (`required`, `min`, `max`, `maxlength`) are only a convenience for the user. Parse the amount with `decimal.Decimal` to check decimal places and reject `NaN`/`Infinity`. Parse the date with `datetime.date.fromisoformat`.
- **Error handling:**
  - Invalid input shows a friendly message and keeps the form values (no 500 error).
  - If the session's user no longer exists, the `sqlite3.IntegrityError` from the foreign key is caught, the session is cleared, and the user is sent to `/login` (same idea as `profile()`).
- **Auth / authorization:** only signed-in users can reach the route, and the expense is always written for `session["user_id"]`. Any `user_id` field in the POST body is ignored.
- **CSRF:** the app has no CSRF protection anywhere yet. This is out of scope for this step and is noted as a follow-up, not added here.

## Implementation Steps

1. Review `app.py`, `database/db.py`, `base.html`, `profile.html`, `style.css` (done while writing this spec).
2. Check the `expenses` schema in `spendly.db`. It already has everything needed, so there are no schema changes.
3. Add `create_expense()` to `database/db.py`.
4. Add `EXPENSE_CATEGORIES`, the validation helper, and the real `add_expense` GET/POST handler to `app.py`. Import `flash` and `date`.
5. Create `templates/add_expense.html`.
6. Add the flash block and the navbar link to `base.html`, and the "Add expense" button to `profile.html`.
7. Add the flash and select styles to `style.css`.
8. Write `tests/test_add_expense.py`, using the same `client` fixture pattern as `tests/test_login_logout.py` (temporary DB via `monkeypatch`).
9. Run the full test suite (`pytest`) to check for regressions in registration, login/logout and the seed scripts.
10. Test by hand in the browser as `demo@spendly.com`: add an expense, then check the row in `spendly.db`.

## Testing Requirements

`tests/test_add_expense.py` should cover:

- A signed-out `GET` or `POST` to `/expenses/add` redirects to `/login`, and nothing is inserted.
- A signed-in `GET` returns 200, shows the form with all 7 categories, and defaults the date to today.
- A valid `POST` returns a 302 to `/profile`, inserts one row with the correct `user_id`, amount (rounded to 2 dp), category, date and description, and shows the flash message on the next page.
- Leaving out the description stores `NULL`.
- Rejected, with no row inserted and values re-filled:
  - amount missing, `0`, negative, non-numeric, `nan`, more than 2 decimals, or over the limit
  - a category not in the list
  - a date that is missing, malformed, or more than one day past the server's today (the server's tomorrow is accepted)
  - a description longer than 200 characters
- A `user_id` field in the POST body is ignored; the row belongs to the session user.
- A session pointing at a deleted user is sent to `/login` instead of getting a 500 error.
- Existing test files still pass.

## Acceptance Criteria

- A signed-in user can add an expense from `/expenses/add`, and it is saved to `spendly.db` under their account.
- The route is login-protected, and signed-out users are redirected to `/login`.
- All fields are validated on the server, with clear error messages and the form values kept.
- No schema changes, and all existing expense and user data is kept.
- The "Add expense" entry points (navbar, profile) work, and the page is usable at phone width.
- Existing features (landing, register, login, logout, profile, seed scripts) still work, and the full `pytest` suite passes.
- No duplicated category lists, tables, or insert logic.

## Deliverables

- This specification.
- `create_expense()` in `database/db.py`.
- Working `/expenses/add` GET/POST route with validation in `app.py`.
- `templates/add_expense.html`, plus the updates to `base.html` and `profile.html`.
- CSS additions in `static/css/style.css`.
- `tests/test_add_expense.py`.

## Files Expected to Be Created or Modified

| File | Change |
|---|---|
| `database/db.py` | modify: add `create_expense()` |
| `app.py` | modify: `EXPENSE_CATEGORIES`, validator, real `add_expense` route, `flash` import |
| `templates/add_expense.html` | **create** |
| `templates/base.html` | modify: flash block, "Add expense" nav link |
| `templates/profile.html` | modify: "Add expense" button |
| `static/css/style.css` | modify: flash + select styles |
| `tests/test_add_expense.py` | **create** |
| `.claude/specs/06-add-expenses.md` | **create** (this file) |
