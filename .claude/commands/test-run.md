---
description: Run the Spendly test suite (all tests, one file, or a keyword) and report results
argument-hint: "[all | <test file> | <keyword>] [--smoke]"
allowed-tools: Bash(.venv/bin/pytest:*), Bash(.venv/bin/python -m pytest:*), Bash(git status:*), Bash(git diff:*), Bash(git branch:*), Bash(curl:*), Bash(lsof:*), Read, Grep, Glob
---

# Test Run

Run Spendly's automated tests and report the results clearly. This command **only runs and reports**. It must not change code, tests, or data.

Arguments: `$ARGUMENTS`

## Step 1: Pick what to run

Read `$ARGUMENTS`:

| Argument | Command |
|---|---|
| empty or `all` | `.venv/bin/pytest -q` |
| a test file, e.g. `test_add_expense` or `tests/test_add_expense.py` | `.venv/bin/pytest -q tests/test_add_expense.py` (add `tests/` and `.py` if they're missing) |
| any other word, e.g. `profile` or `login` | `.venv/bin/pytest -q -k "<word>"` |
| also contains `--smoke` | run the tests, then do Step 4 |

If a named test file doesn't exist, list the files in `tests/` and stop.

## Step 2: Check the setup

- Use the project virtualenv, `.venv/bin/pytest`. If `.venv` is missing, stop and tell the user to create it (`python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`).
- `pytest.ini` sets `pythonpath = .`. If you see `No module named 'database'`, `pytest.ini` is missing or was changed; say so.
- Tests use a temporary database through the `client` fixture (`monkeypatch` on `db_module.DB_PATH`). Never point tests at the real `spendly.db`.

## Step 3: Run and report

Run the command from Step 1. Then report:

1. **Result line**: e.g. `67 passed in 5.6s` or `2 failed, 65 passed`.
2. **Branch**: the current branch (`git branch --show-current`) and whether there are uncommitted changes (`git status --short`), so it's clear what was tested.
3. **For each failure**:
   - the test name and file:line
   - the assertion or error, in one or two lines
   - the likely cause, found by reading the test and the code it calls. Say whether it looks like a bug in the app, a test that's out of date, or an environment problem.
4. **Warnings**: mention only the ones that point at a real problem (e.g. deprecations in our own code). Skip third-party noise.

If everything passes, keep the report to the result line and the branch info.

## Step 4: Live smoke check (only with `--smoke`)

1. Check that the app is running: `lsof -nP -i :5001 | grep LISTEN`. If it isn't, tell the user to start it with `.venv/bin/python app.py`, and skip this step. Don't start it yourself.
2. Use `curl` to check that these pages respond: `/`, `/login` and `/register` should return 200. `/logout` should return a 302 to `/`. A signed-out `/profile` and `/expenses/add` should return a 302 to `/login`.
3. Don't sign in and don't submit forms. The live app writes to the real `spendly.db`.
4. Report each URL with its status code.

## Rules

- Do **not** edit code or tests to make a failing test pass, and do not skip, delete, or mark tests `xfail`. Report the failure and suggest a fix. Apply the fix only if the user asks.
- Do not change `spendly.db`.
- Do not commit anything.
