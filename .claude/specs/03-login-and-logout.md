# Step 03 - Login And Logout

## Step Number

03

## Feature Name

Login and Logout

## Objective

Wire up real authentication for existing users on the Spendly expenses-tracker webpage. Today `templates/login.html` already POSTs `email`/`password` to `/login`, but `app.py` only defines `GET /login` — there is no credential check, no session is ever established for a returning user, and `/logout` is a literal placeholder (`"Logout — coming in Step 3"`). This step makes login authenticate an existing account (created via registration, or one of the seeded demo/dummy users) and establish a session, and makes logout actually clear that session. It also makes the nav bar in `templates/base.html` reflect whether a visitor is signed in, since that was explicitly deferred from the registration step (`.claude/specs/02-registration.md`) until login/logout existed.

## Database Impact

- **Existing tables to use**: `users` (id, name, email, password_hash, username, status, environment, created_at) — schema defined in `database/db.py::init_db()`. No new tables, columns, relationships, or indexes are needed; login only needs to read a row by email and verify its `password_hash`.
- **New tables required**: None.
- **New columns required**: None.
- **Relationships / foreign keys**: No change.
- **Indexes**: None needed beyond the existing `UNIQUE` index on `users.email`.
- **Migration requirements**: None — no schema change in this step.
- **Data validation requirements**:
  - `email`: required, must match an existing user (via `get_user_by_email()`, already implemented).
  - `password`: required, checked against the stored hash with `werkzeug.security.check_password_hash` (the counterpart to `generate_password_hash`, which is already the project's hashing convention).
  - Do not reveal whether the failure was "no such email" vs. "wrong password" — a single generic error avoids leaking which emails are registered.

## UI / Webpage Impact

- **`templates/login.html`**: no structural changes needed. It already posts `email`/`password` to `/login` and renders `{{ error }}` (same `auth-error` markup pattern as `register.html`) — the backend now needs to populate that on failed login, and preserve the submitted `email` (never the password) on re-render.
- **`templates/base.html`**: the nav currently always shows "Sign in" / "Get started", even for an authenticated session. Update it to show "Profile" / "Sign out" (linking to `/profile` and `/logout`) when `session.get("user_id")` is set, and the current "Sign in" / "Get started" links otherwise. This requires the session to be readable in the template context (Flask exposes `session` to Jinja by default, so no new context processor is required).
- **`/logout`**: replace the placeholder text response with a redirect (to `landing`, matching the pattern of `/register` and `/login` redirecting to a named route rather than returning raw text).
- **`/profile`**: no changes; still the authenticated landing page after sign-in.
- **Landing / register pages**: no template changes beyond the shared `base.html` nav update.

## Backend Impact

- **Routes**:
  - `GET /login` — unchanged (renders form).
  - `POST /login` — new. Look up the user by email via `get_user_by_email()`. If no user, or `check_password_hash(user["password_hash"], password)` fails, re-render `login.html` with a generic `error` ("Invalid email or password.") and the submitted `email` preserved (not the password). On success, set `session["user_id"] = user["id"]` and redirect to `/profile`.
  - `GET /logout` — new logic (route already exists as a placeholder). Clear the session (`session.pop("user_id", None)` or `session.clear()`) and redirect to `landing`.
- **Business logic**: reuse the existing `login_required` decorator (`app.py`) unchanged — it already redirects unauthenticated `/profile` requests to `/login`. No new decorators needed for this step.
- **Database queries**: reuse `get_db()` and `get_user_by_email()` from `database/db.py`; no new queries needed (login only reads, never writes).
- **Validation**: server-side check for empty email/password in addition to the `required` attributes already on the HTML inputs (client-side only, not sufficient alone).
- **Error handling**: a single generic invalid-credentials message for both "unknown email" and "wrong password" cases, never leaking which one occurred or any raw exception text.
- **Authentication / authorization considerations**:
  - Passwords are only ever compared via `check_password_hash` against the stored hash — never compared or logged in plaintext.
  - Logging in must work for both self-registered users and the seeded `demo@spendly.com` / dummy users, since they share the same `users` table and hashing convention.
  - Logging out must fully invalidate the session so a subsequent `/profile` request redirects to `/login` again.

## Implementation Steps

1. Review the existing Spendly project structure (`app.py`, `templates/login.html`, `templates/base.html`, `database/db.py`) — done as part of writing this spec.
2. Inspect `spendly.db` and confirm the `users` table already has everything login needs (`email`, `password_hash`) — confirmed, no migration required.
3. Define the required database changes — none; reuse existing schema and `get_user_by_email()`.
4. Define the backend changes — add `POST` handling to `/login`, replace the `/logout` placeholder with real session-clearing logic.
5. Define the frontend/UI changes — update `templates/base.html` nav to be session-aware; no changes to `login.html` structure.
6. Implement the feature without breaking existing functionality — landing, registration, and `/profile` protection must keep working exactly as today.
7. Update database migrations or initialization scripts when required — not required this step.
8. Test the feature with representative data — verify login succeeds for a registered user and for the seeded `demo@spendly.com` user, fails clearly for a wrong password and for an unknown email, and that logout clears the session.
9. Test existing Spendly functionality for regressions — registration flow, `/profile` protection, and all existing seed scripts still work unmodified.
10. Document the completed feature — update this spec's checkboxes once implemented (no schema changes to document).

## Acceptance Criteria

- [x] A registered user can log in via `/login` with the correct email/password and is redirected to `/profile` with a session established.
- [x] The seeded `demo@spendly.com` (and dummy) user can also log in successfully using the existing seed credentials.
- [x] An unknown email or an incorrect password shows the same generic "Invalid email or password." error and does not reveal which case occurred.
- [x] The submitted email (never the password) is preserved on a failed login re-render.
- [x] `/logout` clears the session and redirects to the landing page; a subsequent `/profile` request then redirects to `/login`.
- [x] `templates/base.html` nav shows "Profile" / "Sign out" when authenticated and "Sign in" / "Get started" when not, across landing/login/register/profile pages.
- [x] Existing registration flow and existing demo/dummy users and their expenses are unaffected.
- [x] No plaintext passwords are ever stored, logged, or compared.
- [x] No new tables/columns/duplicate logic are introduced beyond what's listed above.

## Deliverables

- This feature specification (`.claude/specs/03-login-and-logout.md`).
- Backend changes in `app.py` (`POST /login`, real `/logout` logic).
- Session-aware nav in `templates/base.html`.
- Tests covering login success (registered + seeded users), invalid credentials, error preservation, and logout behavior (e.g. `tests/test_login_logout.py`).
- Confirmation that existing landing/register/profile pages and all existing seed scripts still work unmodified.

## Files Expected to Be Created or Modified

- **Modify**: `app.py`
- **Modify**: `templates/base.html`
- **Create**: `tests/test_login_logout.py`
- **Create**: `.claude/specs/03-login-and-logout.md` (this file)

## Assumptions Requiring Confirmation

- **Generic invalid-credentials message**: assumed to avoid distinguishing "unknown email" from "wrong password," for basic security hygiene. Confirm if a more specific message is preferred instead.
- **Logout redirect target**: assumed to be the landing page (`/`), consistent with there being no dashboard. Confirm if `/login` is preferred instead.
- **Nav auth-awareness**: assumed to belong in this step (it was explicitly deferred here by the registration spec) rather than being treated as a separate UI-only step.
- **"Remember me" / persistent sessions and password reset**: assumed out of scope for this step, consistent with the same assumption made in the registration spec.
