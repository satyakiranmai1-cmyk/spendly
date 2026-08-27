# Step 02 - User Authentication

## Step Number

02

## Feature Name

User Authentication

## Objective

Wire up real registration, login, and logout for the Spendly expenses-tracker webpage. Today `templates/register.html` and `templates/login.html` already POST to `/register` and `/login`, but `app.py` only renders those templates on `GET` — there is no account creation, no credential check, no session, and `/logout` and `/profile` are plain-text placeholders. This step makes those forms functional, introduces session-based login, and protects user-specific routes (starting with `/profile`, and any future `/expenses/*` routes) so a request is always tied to a specific logged-in user rather than a hardcoded demo user.

## Database Impact

- **Existing tables to use**: `users` (id, name, email, password_hash, username, status, environment, created_at) — schema already defined in `database/db.py::init_db()`. `email` already has a `UNIQUE NOT NULL` constraint and `password_hash` is already hashed via `werkzeug.security.generate_password_hash` in `seed_db()`/`seed_dummy_user.py`, so registration should reuse that exact hashing convention.
- **New tables required**: None.
- **New columns required**: None. `username`, `status`, and `environment` already exist (added for the dummy-user seed) but are not required for real user registration — leave them `NULL`/default for normal signups.
- **Relationships / foreign keys**: No change. `expenses.user_id → users.id` already exists and is what session-based auth will key off of for future expense routes.
- **Indexes**: None needed beyond the existing `UNIQUE` constraint on `users.email`, which already functions as an index for login lookups.
- **Migration requirements**: None — no schema change in this step.
- **Data validation requirements**:
  - `name`: required, non-empty after trimming.
  - `email`: required, basic format check, checked for existing use via `get_user_by_email()` (already implemented in `database/db.py`) before insert.
  - `password`: required, minimum 8 characters (matches the existing `register.html` placeholder copy "Min. 8 characters").
  - Duplicate email at insert time (race condition) must be caught as a fallback via the existing `UNIQUE` constraint (`sqlite3.IntegrityError`), not just the pre-check.

## UI / Webpage Impact

- **`templates/login.html`**: no structural changes. It already posts `email`/`password` to `/login` and renders `{{ error }}` — the backend now needs to actually populate that on failure.
- **`templates/register.html`**: no structural changes. It already posts `name`/`email`/`password` to `/register` and renders `{{ error }}` the same way.
- **`templates/base.html`**: the navbar currently always shows "Sign in" / "Get started" regardless of auth state. Update it to conditionally show "Profile" / "Sign out" when a session user exists, and "Sign in" / "Get started" otherwise. Requires exposing the current user to all templates (e.g. a small `@app.context_processor` in `app.py`).
- **`/profile`**: replace the plain-text placeholder with a minimal authenticated view (name + email at minimum) — full profile editing UI is out of scope for this step, just prove the session round-trips to a real page.
- **Landing page**: no changes.

## Backend Impact

- **Routes**:
  - `GET /register` — unchanged (renders form).
  - `POST /register` — validate input, reject on existing email, hash password with `generate_password_hash`, insert into `users`, start a session (`session["user_id"]`), redirect to `/profile`. On validation failure, re-render `register.html` with `error` set and the submitted `name`/`email` preserved (never the password).
  - `GET /login` — unchanged (renders form).
  - `POST /login` — look up user via `get_user_by_email()`, verify with `check_password_hash`, on success set `session["user_id"]` and redirect to `/profile`; on failure re-render `login.html` with a single generic error ("Invalid email or password") that does not reveal whether the email exists.
  - `GET /logout` — clear the session and redirect to `/` (landing page). Replaces the current plain-text placeholder.
  - `GET /profile` — require an active session; unauthenticated requests redirect to `/login`. Loads the current user via `session["user_id"]`.
- **Business logic**:
  - Introduce a `login_required` decorator (small helper in `app.py` or a new `auth.py`) that checks `session.get("user_id")` and redirects to `/login` if absent; apply it to `/profile` now and to future `/expenses/*` routes.
  - `app.secret_key` must be set for Flask sessions to work — read from an environment variable (e.g. `FLASK_SECRET_KEY`) with a clearly-labeled development-only fallback, never a hardcoded production secret.
- **Database queries**: reuse `get_db()` and `get_user_by_email()` from `database/db.py`. Add one new parameterized insert for registration (`INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)`), matching the pattern already used in `seed_db()`.
- **Validation**: server-side checks for empty fields, email format, minimum password length, and duplicate email — in addition to the `required` attributes already on the HTML inputs (client-side only, not sufficient alone).
- **Error handling**: catch `sqlite3.IntegrityError` on duplicate email as a race-condition fallback and surface it as the same "email already in use" error; never leak raw exception text to the rendered page.
- **Authentication / authorization considerations**:
  - Passwords are only ever stored hashed (`generate_password_hash`) — never logged or stored in plaintext, consistent with `seed_db()` and `seed_dummy_user.py`.
  - This step must **not** introduce any development-only auth bypass (e.g. auto-login as the dummy user) into the production login path — the dummy user from `/seed-user` should only ever be reachable by actually knowing its (dev-only) credentials, the same as any other user.
  - `/logout` must fully clear the session, not just one key.

## Implementation Steps

1. Review the existing Spendly project structure (`app.py`, `templates/`, `database/db.py`) — done as part of writing this spec.
2. Inspect `spendly.db` and confirm the `users` table already has everything registration/login need (`email`, `password_hash`) — confirmed, no migration required.
3. Define the required database changes — none; reuse existing schema and `get_user_by_email()`.
4. Define the backend changes — add `POST` handling to `/register` and `/login`, implement `/logout`, protect `/profile` with `login_required`, add `app.secret_key`, add a context processor exposing the current user.
5. Define the frontend/UI changes — update `base.html` nav to reflect auth state; give `/profile` a minimal real view.
6. Implement the feature without breaking existing functionality — landing page, existing GET routes, and the expense placeholders must keep working exactly as today.
7. Update database migrations or initialization scripts when required — not required this step.
8. Test the feature with representative expense data — verify a newly registered user can log in and that `/profile` reflects their own record, and that this doesn't disturb the existing demo (`demo@spendly.com`) or dummy (`dummy@spendify.local`) users/expenses.
9. Test existing Spendly functionality for regressions — landing/register/login `GET` pages still render, `init_db()`/`seed_db()`/`seed_dummy_user.py`/`seed_expenses.py` still run cleanly.
10. Document the completed feature and any database changes — update this spec's checkboxes / commit message once implemented (no schema changes to document beyond this file).

## Acceptance Criteria

- [ ] A new user can register via `/register` with name, email, and password, and is logged in immediately after.
- [ ] Registration rejects a duplicate email with a clear on-page error and does not create a second row.
- [ ] Registration rejects an empty name, invalid email, or password under 8 characters with a clear on-page error.
- [ ] A registered user can log in via `/login` with correct credentials and is redirected to `/profile`.
- [ ] Login with an incorrect password or unknown email shows a single generic error, without revealing which part was wrong.
- [ ] `/logout` clears the session and returns the user to the landing page as a signed-out visitor.
- [ ] `/profile` redirects unauthenticated visitors to `/login` and shows the correct logged-in user's name/email otherwise.
- [ ] The navbar in `base.html` reflects signed-in vs. signed-out state correctly.
- [ ] Existing `demo@spendly.com` and `dummy@spendify.local` users and their expenses are unaffected.
- [ ] No plaintext passwords are ever stored or logged.
- [ ] No new tables/columns/duplicate logic are introduced beyond what's listed above.
- [ ] `spendly.db` changes (none expected) are documented here if that assumption turns out to be wrong during implementation.

## Deliverables

- This feature specification (`.claude/specs/02-user-authentication.md`).
- Backend changes in `app.py` (POST `/register`, POST `/login`, real `/logout`, `login_required`-protected `/profile`, `app.secret_key`, current-user context processor).
- Any small reusable helpers added to `database/db.py` (e.g. `create_user()`), reusing existing connection/hashing conventions — no schema changes anticipated.
- Frontend changes to `templates/base.html` (auth-aware nav) and `templates/profile.html` if a dedicated template is introduced for `/profile` instead of inline text.
- Tests covering registration, login, logout, and route protection (e.g. `tests/test_auth.py`).
- Confirmation that existing landing/register/login GET pages and all existing seed scripts still work unmodified.

## Files Expected to Be Created or Modified

- **Modify**: `app.py`
- **Modify**: `database/db.py` (optional small helper additions only — no schema change)
- **Modify**: `templates/base.html`
- **Create** (optional, if `/profile` gets a real template instead of inline text): `templates/profile.html`
- **Create**: `tests/test_auth.py`
- **Create**: `.claude/specs/02-user-authentication.md` (this file)

## Assumptions Requiring Confirmation

- **Password minimum length**: assumed 8 characters, based on the existing placeholder text in `register.html` ("Min. 8 characters"). Confirm before implementing if a different minimum or complexity rule is wanted.
- **Post-login/register redirect target**: assumed `/profile`, since there is no dashboard yet. If a dashboard route is planned as the very next step, it may be worth redirecting there instead once it exists.
- **`SECRET_KEY` handling**: assumed to come from an environment variable with a dev-only fallback constant in code. Confirm the intended production deployment story (e.g. `.env` file, hosting platform secret) if different.
- **Scope of `/profile`**: assumed to be a minimal "it works" view (name + email) for this step, with full profile editing/password-change treated as a separate future feature.
- **"Remember me" / persistent sessions and email verification**: assumed out of scope for this step.
