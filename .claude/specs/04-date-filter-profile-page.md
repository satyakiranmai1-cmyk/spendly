# Step 04 - Date Filter for Profile Page

## Objective

Let a signed-in Spendly user filter the expense activity shown on their profile page to a specific date range (e.g. this month, last 30 days, or a custom start/end date), so the totals and expense list reflect only the selected window instead of all-time data.

## Assumption requiring confirmation

The current `main` branch's `/profile` route and `profile.html` only show the user's name and email — there is no expense summary or day-wise expense list on the profile page yet. That work exists on the unmerged branch `feature/profile-page-design` (`get_expense_summary_by_user`, `get_expenses_by_day`, a stats block in `profile.html`, and a separate `/expenses` statement page).

This spec assumes `feature/profile-page-design` is merged to `main` (or its relevant pieces — `get_expense_summary_by_user`, `get_expenses_by_day`, the profile stats UI — are ported into this branch) **before** implementation starts, since the date filter extends that existing summary/list rather than introducing it. **Confirm this dependency before implementation begins.**

## Database Impact

No schema changes required.

- Existing table: `expenses` (`user_id`, `amount`, `category`, `description`, `date`, `created_at`) already has a `date` column (`TEXT`, `YYYY-MM-DD`) suitable for range filtering.
- Existing table: `users` — unchanged.
- No new tables, columns, foreign keys, or indexes are required for correctness. Optional: an index on `expenses (user_id, date)` would speed up range-filtered queries as data grows, but is not required at current data volumes.
- No migration required.
- Data validation: incoming `start_date`/`end_date` query parameters must be validated as `YYYY-MM-DD` strings and `start_date <= end_date` before being used in a query; invalid or missing values fall back to a sensible default range (see UI section) rather than erroring.

## UI / Webpage Impact

- **Profile page (`templates/profile.html`)**: add a date-range filter control above the expense summary/list — a small form with `start_date` and `end_date` inputs (`<input type="date">`) plus a set of quick-range preset links/buttons: "This month", "Last 30 days", "Last 6 months", "All time".
- The submitted range is reflected in the URL as query parameters (e.g. `/profile?start_date=2026-08-01&end_date=2026-08-31`) so the filtered view is shareable/bookmarkable and survives a page refresh.
- The existing stats block (total spent, expense count) and the day-wise expense list recalculate against the filtered range instead of all-time data.
- When the filtered range has no expenses, show the existing "no expenses" empty state, plus the active date range so the user understands why it's empty.
- Default view (no query params): keep existing default range — decide at implementation time whether that's "all time" or "current month"; recommend "current month" as the default since that matches the primary use case of a profile filter, with "All time" available as a preset.
- Filter control should be reusable — implemented so it can also be dropped onto the `/expenses` statement page in a future step without duplicating markup/logic.

## Backend Impact

- **Route**: `/profile` (existing `GET`) — read optional `start_date` and `end_date` query parameters via `request.args`.
- **Business logic**: parse and validate the two dates (format check, ordering check); on invalid input, ignore the bad values and fall back to the default range rather than raising an error.
- **Database queries** (`database/db.py`):
  - Extend `get_expense_summary_by_user(user_id)` → `get_expense_summary_by_user(user_id, start_date=None, end_date=None)`, adding an optional `AND date BETWEEN ? AND ?` clause when both bounds are provided.
  - Extend `get_expenses_by_day(user_id)` → `get_expenses_by_day(user_id, start_date=None, end_date=None)` the same way.
  - Keep both functions backward-compatible (existing no-arg calls, e.g. from `/expenses`, keep returning all-time data) by defaulting the new params to `None`.
- **Validation**: reject/ignore malformed dates (non-`YYYY-MM-DD`, `start_date > end_date`) server-side; never trust the client-supplied range blindly in the SQL (use parameterized queries — no string-built SQL).
- **Error handling**: an invalid range degrades gracefully to the default view rather than a 500; no user-facing error page needed for bad query params.
- **Auth**: no change — route stays behind `@login_required`; the filter only ever queries `session["user_id"]`'s own expenses.

## Implementation Steps

1. Confirm the `feature/profile-page-design` dependency (see Assumption) is available on this branch — merge or port `get_expense_summary_by_user`, `get_expenses_by_day`, and the profile stats UI first if not already present.
2. Inspect `spendly.db` expense date range for the seeded demo user (currently `2026-03-14` to `2026-09-07`, 68 rows) to design realistic presets.
3. Add `start_date`/`end_date` parameters to `get_expense_summary_by_user` and `get_expenses_by_day` in `database/db.py`.
4. Update the `/profile` route in `app.py` to read, validate, and pass the date range through to those two functions and to the template.
5. Add the date-range filter form and preset links to `templates/profile.html`.
6. Style the filter control in `static/css/style.css`, consistent with the existing `statement-*`/profile styling.
7. Test with the seeded demo data across multiple ranges (a month with expenses, a month with none, a custom range, an invalid/malformed range).
8. Regression-test the unfiltered profile view and the `/expenses` statement page (which reuses the same `db.py` functions) to confirm default behavior is unchanged.
9. Document the new query parameters and function signatures.

## Acceptance Criteria

- Profile page shows a date-range filter with working presets and a custom start/end date form.
- Submitting a range updates the URL query params and re-renders the stats and expense list scoped to that range.
- Default (no params) view matches the agreed default range with no regressions to existing profile content.
- Invalid/out-of-order dates fall back gracefully to the default range, no server error.
- `get_expense_summary_by_user` and `get_expenses_by_day` remain backward-compatible for existing no-arg callers (e.g. `/expenses`).
- Only the requesting user's own expenses are ever queried (no cross-user data leakage via manipulated params).
- Feature tested against the realistic seeded dataset (68 expenses, Mar–Sep 2026) covering populated and empty ranges.
- No unnecessary duplicate tables, columns, or filtering logic introduced — reuses existing `expenses.date` column and existing query functions.

## Deliverables

- This feature implementation specification.
- Updated `get_expense_summary_by_user` / `get_expenses_by_day` signatures in `database/db.py`.
- Updated `/profile` route in `app.py`.
- Updated `templates/profile.html` with filter UI.
- Updated `static/css/style.css` for filter styling.
- Tests covering the new date-filtering behavior (extend `tests/test_expenses_statement.py` or add a sibling test module).
- This spec's acceptance criteria, verified against seeded data.

## Files Expected to Be Created or Modified

- `database/db.py` (modify)
- `app.py` (modify)
- `templates/profile.html` (modify)
- `static/css/style.css` (modify)
- `tests/test_expenses_statement.py` or new `tests/test_profile_date_filter.py` (modify/create)
- `.claude/specs/04-date-filter-profile-page.md` (this file)
