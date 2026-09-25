---
description: Write pytest tests for a Spendly feature from its spec, run them, and report spec mismatches
argument-hint: "<spec number or feature name, e.g. 06 or add-expenses>"
allowed-tools: Read, Grep, Glob, Write, Edit, Bash(.venv/bin/pytest:*), Bash(.venv/bin/python -m pytest:*), Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git branch:*), Bash(ls:*)
---

# Test Feature

Write or extend the automated tests for one Spendly feature, based on its spec. Then run them and report whether the code does what the spec says.

Arguments: `$ARGUMENTS`

**The spec is the source of truth, not the code.** Tests describe what the spec requires. If the code disagrees, the test should fail and you report the mismatch. Never weaken a test so it passes.

## Step 1: Find the spec

- Look in `.claude/specs/` for a file matching `$ARGUMENTS`: either the number (`06` → `06-*.md`) or words from the name (`add-expenses`, `login`).
- If `$ARGUMENTS` is empty, use the spec for the current branch (e.g. `feature/add-expenses` → `*-add-expenses.md`). If that's unclear, list the specs and ask which one.
- If more than one file matches, list them and ask.
- Read the whole spec. Pay special attention to **Backend Impact** (routes, validation, errors, auth), **Testing Requirements** and **Acceptance Criteria**.

## Step 2: Understand what exists

- Read the code the spec names: the route in `app.py`, the helpers in `database/db.py`, and the templates.
- Read the existing tests for this feature (e.g. `tests/test_add_expense.py`), plus one other test file for conventions.
- Build a checklist: each requirement in the spec, and whether a test already covers it. Don't write duplicate tests.

## Step 3: Write the missing tests

Put them in `tests/test_<feature>.py`, adding to the file if it already exists. Follow the project's conventions:

- **Fixture:** use the `client` fixture pattern from the existing tests. It patches `db_module.DB_PATH` to a `tmp_path` database **before** `import app`, then calls `db_module.init_db()`. Tests must never touch the real `spendly.db`.
- **Helpers:** small module-level helpers like `register(client, ...)` and `valid_form(**overrides)` rather than repeated setup.
- **Style:** plain `assert`s, one behavior per test, and names that describe the behavior (`test_future_date_is_rejected`). Use `@pytest.mark.parametrize` for lists of invalid inputs.
- **What to check:** the status code, the redirect `Location`, what's rendered on the page (`resp.get_data(as_text=True)`), **and the database state**. For example, a rejected form inserts no row, and an accepted form stores exactly the right values.
- **Dates:** build them from `date.today()` and `timedelta`, never hard-coded dates that go stale.

Cover, where the spec asks for them:
- the main success path
- each validation rule, both just inside and just outside its limit
- signed-out access, and one user trying to reach or write another user's data
- error handling, such as a stale session or a missing record
- the empty state
- values being kept in the form after an error

Don't test Flask or Jinja themselves. Don't test CSS or how the page looks.

## Step 4: Run

1. Run the feature's test file: `.venv/bin/pytest -q tests/test_<feature>.py`.
2. Run the full suite, `.venv/bin/pytest -q`, to check the new tests don't break or interfere with others.

If a new test fails, work out which side is wrong:
- **The test is wrong** (a typo, a wrong fixture, the wrong expected text for something the spec doesn't pin down): fix the test.
- **The code doesn't match the spec:** leave the test failing and report it. Do **not** change `app.py`, `database/`, or the templates unless the user asks.

## Step 5: Report

1. **Spec:** which file you used.
2. **Coverage table:** one row per spec requirement, showing the test that covers it and ✅ passes / ❌ fails / ⚠️ can't be tested automatically (say why).
3. **Tests added:** how many, and in which file.
4. **Results:** the output of the feature file run and the full-suite run.
5. **Spec mismatches:** for each one, what the spec says, what the code does, the failing test, and a suggested fix.

## Rules

- Only create or edit files under `tests/`.
- Don't delete, skip, or `xfail` existing tests.
- Don't change `spendly.db`, and don't commit. Leave that to the user.
- To only re-run tests without writing new ones, use `/test-run`.
