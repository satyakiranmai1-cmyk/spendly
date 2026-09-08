# Step 04 - Profile Page Design

## Objective

Redesign the Spendly profile page so a logged-in user sees a richer account
summary — their name, email, username, member-since date, total amount
spent, and number of expenses logged — instead of just a bare name/email
form-style view.

## Database Impact

- **Existing tables used:** `users` (name, email, username, created_at),
  `expenses` (amount, user_id).
- **New tables:** none.
- **New columns:** none — all fields needed already exist on `users`.
- **Relationships/foreign keys:** relies on the existing
  `expenses.user_id → users.id` foreign key.
- **Indexes:** none added.
- **Migration requirements:** none — no schema change.
- **Data validation requirements:** none — read-only aggregation query.
- **New query:** `get_expense_summary_by_user(user_id)` in `database/db.py`
  returns `{"total_spent": float, "expense_count": int}` via
  `SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM expenses WHERE user_id = ?`.

## UI / Webpage Impact

- `templates/profile.html`:
  - New profile header with a circular avatar badge (first letter of the
    user's name), display name, and email.
  - Account details card showing email, username (`"Not set"` when null),
    and member-since date.
  - New two-column stats row (`.stats-row` / `.stat-tile`) showing "Total
    spent" and "Expenses logged", stacking to one column on small screens.
- `static/css/style.css`: new `.profile-container`, `.profile-header`,
  `.avatar-badge`, `.profile-header-text`, `.profile-name`,
  `.profile-email`, `.stats-row`, `.stat-tile` rules, plus a mobile
  breakpoint tweak for the header and stats row.

## Backend Impact

- **Routes/endpoints:** `GET /profile` (`app.py`) — unchanged route, updated
  handler.
- **Business logic:**
  - Fetches the user's expense summary via `get_expense_summary_by_user`.
  - Formats `created_at` (`"%Y-%m-%d %H:%M:%S"`) into a human-readable
    `member_since` string (e.g. "August 29, 2026"), falling back to the raw
    value if parsing fails.
- **Database queries:** one additional read query per profile view
  (aggregate over `expenses`).
- **Validation:** none beyond existing login-required check.
- **Error handling:** unchanged — unauthenticated users are redirected to
  `/login`; malformed `created_at` values fall back gracefully instead of
  raising.
- **Authentication/authorization:** unchanged — `@login_required`-style
  session check already in place on `/profile`.

## Implementation Steps

1. Review existing Spendly project structure and profile route/template.
2. Inspect `spendly.db` schema — confirmed `users` and `expenses` tables
   already carry everything needed; no migration required.
3. Add `get_expense_summary_by_user` to `database/db.py`.
4. Update the `/profile` route in `app.py` to compute `summary` and
   `member_since` and pass them to the template.
5. Update `templates/profile.html` with the new header, avatar, and stats
   row.
6. Add corresponding styles to `static/css/style.css`.
7. Add `tests/test_profile.py` covering: zero-stats for a new user, "Not
   set" username, member-since rendering, and correct totals for the
   seeded demo user.
8. Run the test suite against representative seeded expense data.
9. Verify existing auth/login/registration flows are unaffected.

## Acceptance Criteria

- [x] Profile page displays name, email, username, and member-since date.
- [x] Profile page displays total spent and expense count for the logged-in
      user.
- [x] No `spendly.db` schema changes required; existing expense data is
      preserved.
- [x] Existing Spendly features (login, logout, registration, expenses)
      continue to work unmodified.
- [x] UI is responsive (stats row and header stack on narrow viewports).
- [x] New query and route logic covered by `tests/test_profile.py`.
- [x] No duplicate tables, columns, or logic introduced — reuses existing
      `users`/`expenses` tables and query patterns.

## Files Created or Modified

- `app.py` — modified (`/profile` route)
- `database/db.py` — modified (new `get_expense_summary_by_user`)
- `templates/profile.html` — modified (new header/stats layout)
- `static/css/style.css` — modified (new profile styles)
- `tests/test_profile.py` — created

## Assumptions

- "Member since" uses the existing `users.created_at` timestamp; no new
  tracking field was needed.
- Stats are computed live on each page load rather than cached/denormalized,
  consistent with the app's current no-cache query pattern.
