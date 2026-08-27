# Step 02 - Registration

## Step Number

02

## Feature Name

Registration

## Objective

Wire up real account creation for the Spendly expenses-tracker webpage. Today `templates/register.html` already POSTs `name`/`email`/`password` to `/register`, but `app.py` only renders that template on `GET` — there is no validation, no password hashing at signup, and no row is ever inserted into `users`. This step makes registration actually create an account and immediately establish a session for the new user, so the very next request (e.g. `/profile`) is tied to that specific user. Login for *existing* users and `/logout` are intentionally **out of scope** here — that becomes a follow-on step (see Assumptions) once registration is solid.

## Database Impact

- **Existing tables to use**: `users` (id, name, email, password_hash, username, status, environment, created_at) — schema already defined in `database/db.py::init_db()`. `email` already has a `UNIQUE NOT NULL` constraint, and password hashing already has a project convention (`werkzeug.security.generate_password_hash`, used in `seed_db()` and `seed_dummy_user.py`) that registration must reuse.
- **New tables required**: None.
- **New columns required**: None. `username`, `status`, and `environment` already exist (added for the dummy-user seed) but are not required for real registrations — leave them `NULL`/default for normal signups.
- **Relationships / foreign keys**: No change. `expenses.user_id → users.id` is unaffected by this step.
- **Indexes**: None needed beyond the existing `UNIQUE` constraint on `users.email`.
- **Migration requirements**: None — no schema change in this step.
- **Data validation requirements**:
  - `name`: required, non-empty after trimming.
  - `email`: required, basic format check, checked for existing use via `get_user_by_email()` (already implemented in `database/db.py`) before insert.
  - `password`: required, minimum 8 characters (matches the existing `register.html` placeholder copy "Min. 8 characters").
  - Duplicate email at insert time (race condition) must be caught as a fallback via the existing `UNIQUE` constraint (`sqlite3.IntegrityError`), not just the pre-check.

## UI / Webpage Impact

- **`templates/register.html`**: no structural changes needed. It already posts `name`/`email`/`password` to `/register` and renders `{{ error }}` — the backend now needs to actually populate that on validation/duplicate-email failure, and preserve the submitted `name`/`email` (never the password) on re-render.
- **`templates/base.html`**: no changes in this step. Auth-aware nav (showing "Profile"/"Sign out" vs. "Sign in"/"Get started") depends on login/logout existing too, so it's deferred to that follow-on step rather than half-wired here.
- **`/profile`**: replace the plain-text placeholder with a minimal view (name + email) so there's something real to land on right after registering and prove the session works. Full profile editing is out of scope.
- **Landing / login pages**: no changes.

## Backend Impact

- **Routes**:
  - `GET /register` — unchanged (renders form).
  - `POST /register` — validate input, reject on existing email, hash password with `generate_password_hash`, insert into `users`, start a session (`session["user_id"]`), redirect to `/profile`. On validation failure, re-render `register.html` with `error` set and the submitted `name`/`email` preserved.
  - `GET /profile` — require an active session (via a new `login_required` decorator); unauthenticated requests redirect to `/login` (the existing `GET`-only login page — submitting it does nothing yet, which is expected until the login step lands). Loads the current user via `session["user_id"]`.
- **Business logic**:
  - Introduce a `login_required` decorator (small helper in `app.py`, reusable later by `/expenses/*` and the eventual login-protected routes) that checks `session.get("user_id")` and redirects to `/login` if absent.
  - `app.secret_key` must be set for Flask sessions to work at all — read from an environment variable (e.g. `FLASK_SECRET_KEY`) with a clearly-labeled development-only fallback, never a hardcoded production secret. This is a one-time setup needed regardless of which auth step lands first.
- **Database queries**: reuse `get_db()` and `get_user_by_email()` from `database/db.py`. Add one new parameterized insert for registration (`INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)`), matching the pattern already used in `seed_db()`.
- **Validation**: server-side checks for empty fields, email format, minimum password length, and duplicate email — in addition to the `required` attributes already on the HTML inputs (client-side only, not sufficient alone).
- **Error handling**: catch `sqlite3.IntegrityError` on duplicate email as a race-condition fallback and surface it as the same "email already in use" error; never leak raw exception text to the rendered page.
- **Authentication / authorization considerations**:
  - Passwords are only ever stored hashed (`generate_password_hash`) — never logged or stored in plaintext, consistent with `seed_db()` and `seed_dummy_user.py`.
  - Since there's no `/logout` yet, a session established at registration simply persists until the cookie expires/is cleared manually — acceptable for this step, but call it out clearly so it isn't mistaken for a finished auth system.
  - This step must **not** introduce any development-only auth bypass (e.g. auto-login as the dummy user) into the registration path.

## Implementation Steps

1. Review the existing Spendly project structure (`app.py`, `templates/register.html`, `database/db.py`) — done as part of writing this spec.
2. Inspect `spendly.db` and confirm the `users` table already has everything registration needs (`name`, `email`, `password_hash`) — confirmed, no migration required.
3. Define the required database changes — none; reuse existing schema and `get_user_by_email()`.
4. Define the backend changes — add `POST` handling to `/register`, add `app.secret_key`, add a `login_required` decorator, protect `/profile`.
5. Define the frontend/UI changes — give `/profile` a minimal real view; no other template changes.
6. Implement the feature without breaking existing functionality — landing, login (`GET`), and the expense placeholders must keep working exactly as today.
7. Update database migrations or initialization scripts when required — not required this step.
8. Test the feature with representative data — verify a new registration creates exactly one row, establishes a session, and `/profile` reflects that user; confirm it doesn't disturb the existing demo (`demo@spendly.com`) or dummy (`dummy@spendify.local`) users/expenses.
9. Test existing Spendly functionality for regressions — landing/register/login `GET` pages still render, `init_db()`/`seed_db()`/`seed_dummy_user.py`/`seed_expenses.py` still run cleanly.
10. Document the completed feature — update this spec's checkboxes once implemented (no schema changes to document).

## Acceptance Criteria

- [ ] A new user can register via `/register` with name, email, and password, and is logged in (session established) immediately after.
- [ ] Registration rejects a duplicate email with a clear on-page error and does not create a second row.
- [ ] Registration rejects an empty name, invalid email, or password under 8 characters with a clear on-page error, and preserves the submitted name/email (not the password) on re-render.
- [ ] `/profile` redirects unauthenticated visitors to `/login` and shows the correct newly-registered user's name/email otherwise.
- [ ] Existing `demo@spendly.com` and `dummy@spendify.local` users and their expenses are unaffected.
- [ ] No plaintext passwords are ever stored or logged.
- [ ] No new tables/columns/duplicate logic are introduced beyond what's listed above.
- [ ] `spendly.db` changes (none expected) are documented here if that assumption turns out to be wrong during implementation.

## Deliverables

- This feature specification (`.claude/specs/02-registration.md`).
- Backend changes in `app.py` (`POST /register`, `app.secret_key`, `login_required` decorator, protected `/profile`).
- Any small reusable helper added to `database/db.py` (e.g. `create_user()`), reusing existing connection/hashing conventions — no schema changes anticipated.
- Minimal real `/profile` view (inline render or a small `templates/profile.html`).
- Tests covering registration success, validation failures, duplicate email, and `/profile` route protection (e.g. `tests/test_registration.py`).
- Confirmation that existing landing/register/login `GET` pages and all existing seed scripts still work unmodified.

## Files Expected to Be Created or Modified

- **Modify**: `app.py`
- **Modify**: `database/db.py` (optional small helper addition only — no schema change)
- **Create** (optional, if `/profile` gets a real template instead of inline text): `templates/profile.html`
- **Create**: `tests/test_registration.py`
- **Create**: `.claude/specs/02-registration.md` (this file)

## Assumptions Requiring Confirmation

- **Login and logout are a separate, later step.** This spec deliberately does not implement `POST /login` or `/logout` — confirm that's the intended split rather than doing all of auth in one step.
- **Password minimum length**: assumed 8 characters, based on the existing placeholder text in `register.html` ("Min. 8 characters"). Confirm before implementing if a different minimum or complexity rule is wanted.
- **Post-registration redirect target**: assumed `/profile`, since there is no dashboard yet.
- **`SECRET_KEY` handling**: assumed to come from an environment variable with a dev-only fallback constant in code. Confirm the intended production deployment story if different.
- **Scope of `/profile`**: assumed to be a minimal "it works" view (name + email) for this step, with full profile editing/password-change treated as a separate future feature.
- **"Remember me" / persistent sessions and email verification**: assumed out of scope for this step.
