# Step 08 - Edit Expenses

## Branch

`feature/edit-expenses` (created from `feature/add-expenses`, not `main`. `main` does not have the Step 06 add-expense code yet, and this step builds on it. Merge `feature/add-expenses` into `main` first, or open this branch's PR against it.)

## Objective

Let a signed-in Spendly user fix a mistake in one of their own expenses (amount, category, date or description) from the profile's transaction list. This replaces the `/expenses/<id>/edit` placeholder (`"Edit expense — coming in Step 8"`) in `app.py` with a working, validated, login-protected feature. A user must never be able to see or change another user's expense.

## Assumptions requiring confirmation

1. **Entry point.** Each row in the profile's transaction list (`expense_day_list` in `templates/_macros.html`) gets a small "Edit" link. There is no separate expense list page, so this is the only entry point.
2. **Other users' expenses return 404, not 403.** A 404 for an expense that doesn't exist *or* belongs to someone else stops users from guessing which expense IDs exist.
3. **One shared form template.** `templates/add_expense.html` is renamed to `templates/expense_form.html` and used by both routes. The heading, subtitle, submit label and form `action` are passed in, so the fields, error box and date script live in one place. The alternative is a copy of the template for editing, which would duplicate about 60 lines.
4. **Same validation rules as adding.** `_validate_expense_form()` is reused unchanged: amount `> 0`, `<= 10,000,000`, at most 2 decimals; category from `EXPENSE_CATEGORIES`; date no later than `latest_expense_date()`; description at most 200 characters, empty stored as `NULL`.
5. **Old dates are allowed.** Editing an expense from months ago keeps its date, and the date can be moved to any past day. Only future dates are rejected, as in Step 06.
6. **Redirect after saving.** Save sends the user to `/profile` with the flash message "Expense updated.", like adding does.
7. **Categories not in the list.** If an older row has a category that is not in `EXPENSE_CATEGORIES`, the form shows the placeholder and the user must pick a valid category before saving. There are none in the local DB today, but seed scripts could add some.

## Database Impact

**No schema changes required.**

- **Existing table used:** `expenses` (`id`, `user_id`, `amount`, `category`, `description`, `date`, `created_at`). The local `spendly.db` also has a `source` column added by `database/seed_expenses.py`.
- **Relationship:** `expenses.user_id → users.id` (`ON DELETE CASCADE`), unchanged.
- **New tables / columns / indexes:** none. Lookups are by primary key `id`.
- **Migration:** none. The feature only runs a `SELECT` and an `UPDATE` on one row. `id`, `user_id`, `created_at` and `source` are never written, so existing data (3 users, 99 expenses in the local DB) is kept.
- **Data validation:** same as Step 06 (see assumption 4), done in the app before the `UPDATE`. Ownership is also enforced in SQL: every query filters on both `id` and `user_id`.

## UI / Webpage Impact

- **`templates/_macros.html`:** add an "Edit" link to each `statement-row`, pointing to `url_for('edit_expense', id=expense.id)`, next to the amount. Give it an `aria-label` such as "Edit Food expense of $12.50" so screen readers can tell the links apart. `get_expenses_by_day()` already returns `id`, so no query change is needed.
- **`templates/add_expense.html` → `templates/expense_form.html`** (rename, see assumption 3). Add template variables:
  - `title` / `heading` / `subtitle`: "Add an expense" / "Record what you spent" for adding, "Edit expense" / "Update the details" for editing
  - `form_action`: `url_for('add_expense')` or `url_for('edit_expense', id=...)`
  - `submit_label`: "Add expense" or "Save changes"
  - Keep everything else: the fields, error box, "Cancel" link to `/profile`, and the date script. For editing, `fresh_form` is not set, so the script never replaces the stored date with today.
- **Edit form content:** pre-filled from the stored row. The amount is shown with 2 decimals (for example `12.50`, not `12.5`), and a `NULL` description shows as an empty field. After a validation error, the submitted values are shown again, not the stored ones.
- **`static/css/style.css`:** add only a small `.statement-edit` link style (muted colour, underline on hover, visible focus ring). The row must still fit at phone width. The link sits under the amount or wraps, and nothing scrolls sideways.

## Backend Impact

- **Route:** `/expenses/<int:id>/edit`, `methods=["GET", "POST"]`, decorated with `@login_required`. The placeholder has no auth check today, so this fixes that too.
  - `GET` loads the expense with `get_expense_for_user(id, session["user_id"])`. If there's no row, it returns `abort(404)`. Otherwise it renders `expense_form.html` with the stored values.
  - `POST` loads the expense the same way (404 if missing or not owned), then runs `_validate_expense_form(request.form)`.
    - If invalid, it re-renders with `error=` and the submitted values (HTTP 200).
    - If valid, it calls `update_expense(...)`, flashes "Expense updated." and redirects (302) to `/profile`.
    - If `update_expense` returns 0 rows (the row was deleted in between), it returns 404.
- **`add_expense()`:** switch it to `expense_form.html` and pass the new template variables. There is no change to how it behaves.
- **Database queries (`database/db.py`):**
  ```python
  def get_expense_for_user(expense_id, user_id):
      # SELECT id, amount, category, description, date FROM expenses WHERE id = ? AND user_id = ?
      # returns sqlite3.Row or None

  def update_expense(expense_id, user_id, amount, category, date, description=None):
      # UPDATE expenses SET amount = ?, category = ?, description = ?, date = ?
      # WHERE id = ? AND user_id = ?
      # returns cursor.rowcount (1 on success, 0 if missing / not owned)
  ```
  Both follow the existing `get_db()` / `try` / `commit` / `finally: close()` pattern and use parameterized SQL only.
- **Validation:** reuse `_validate_expense_form()` unchanged. Only the four editable fields are read from the form. Any `user_id`, `id` or `source` field in the POST body is ignored.
- **Error handling:**
  - Invalid input shows a friendly message and keeps the values (no 500 error).
  - An unknown expense, another user's expense, or a row deleted before save returns 404.
  - If the session's user has been deleted, `ON DELETE CASCADE` has removed their expenses, so the lookup returns 404. Accessing `/profile` afterwards already sends them to `/login`.
- **Auth / authorization:** login is required (signed-out users go to `/login`), and ownership is checked in both the SELECT and the UPDATE `WHERE` clause. The ownership check doesn't depend on a Python `if` alone.
- **CSRF:** the app still has no CSRF protection. This remains out of scope, as in Step 06.

## Implementation Steps

1. Review `app.py`, `database/db.py`, `templates/add_expense.html`, `templates/_macros.html`, `templates/profile.html` and `style.css` (done while writing this spec).
2. Check the `expenses` schema in `spendly.db`. There are no schema changes.
3. Add `get_expense_for_user()` and `update_expense()` to `database/db.py`.
4. Rename `add_expense.html` to `expense_form.html` (`git mv`) and add the template variables. Update `add_expense()` to use it.
5. Replace the `edit_expense` placeholder with the real GET/POST handler. Import `abort`.
6. Add the "Edit" link to `_macros.html` and the `.statement-edit` style to `style.css`.
7. Write `tests/test_edit_expense.py`, using the same `client` fixture and `register()` helper pattern as `tests/test_add_expense.py`.
8. Run the full `pytest` suite. Pay particular attention to `test_add_expense.py`, since its template was renamed.
9. Test by hand in the browser as `demo@spendly.com`: edit an expense from the profile, check the row in `spendly.db`, and confirm another user's expense ID returns 404.

## Testing Requirements

`tests/test_edit_expense.py` should cover:

- A signed-out `GET` or `POST` to `/expenses/<id>/edit` redirects to `/login` and the row is unchanged.
- A signed-in `GET` for one's own expense returns 200, shows the stored amount (2 decimals), category (selected), date and description, and says "Save changes".
- A `GET` or `POST` for another user's expense returns 404, and their row is unchanged.
- A `GET` or `POST` for an ID that doesn't exist returns 404.
- A valid `POST` returns a 302 to `/profile`, updates all four fields, leaves `user_id`, `created_at` and the row count unchanged, and shows "Expense updated." on the next page.
- Clearing the description stores `NULL`.
- The same invalid inputs as `test_add_expense.py` (amount, category, date, description) are rejected with the row unchanged and the submitted values re-filled.
- `user_id` or `id` fields in the POST body are ignored.
- An old date (for example a year ago) is accepted. A date more than one day past the server's today is rejected.
- The profile page shows an "Edit" link for each expense, pointing to the right URL.
- All existing tests still pass, including `test_add_expense.py` after the template rename.

## Acceptance Criteria

- A signed-in user can edit any of their own expenses from the profile, and the change is saved to `spendly.db`.
- A user cannot view or change another user's expense (404), and signed-out users are redirected to `/login`.
- All fields are validated on the server with the same rules as adding, with clear errors and the values kept.
- No schema changes. Columns that aren't edited (`user_id`, `created_at`, `source`) and all other rows are kept.
- The add and edit forms share one template and one validator, with no duplicated form or validation logic.
- The page and the "Edit" links work at phone width.
- Existing features (landing, register, login, logout, profile, add expense, seed scripts) still work, and the full `pytest` suite passes.

## Deliverables

- This specification.
- `get_expense_for_user()` and `update_expense()` in `database/db.py`.
- A working `/expenses/<id>/edit` GET/POST route in `app.py`.
- The shared `templates/expense_form.html`, and the "Edit" link in `_macros.html`.
- The `.statement-edit` style in `static/css/style.css`.
- `tests/test_edit_expense.py`.

## Files Expected to Be Created or Modified

| File | Change |
|---|---|
| `database/db.py` | modify: add `get_expense_for_user()`, `update_expense()` |
| `app.py` | modify: real `edit_expense` route, `add_expense` uses the shared template, `abort` import |
| `templates/add_expense.html` → `templates/expense_form.html` | **rename** + add heading/action/submit variables |
| `templates/_macros.html` | modify: "Edit" link per expense row |
| `static/css/style.css` | modify: `.statement-edit` style |
| `tests/test_edit_expense.py` | **create** |
| `tests/test_add_expense.py` | no change expected: it checks page content, not the template name |
| `.claude/specs/08-edit-expenses.md` | **create** (this file) |
