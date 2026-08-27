# Create a Single Dummy User for Slash Command Development

## Objective

Create exactly **one dummy user** in the database/db.py for understanding and testing of slash commands.

The dummy user must be deterministic, easy to identify, and safe to use during local development and automated testing.

This user is intended **only for development/testing** and must never be treated as a production user.

---

## Requirements

### 1. Create exactly one user

Create a single dummy user in the application's users table.

Do not create multiple dummy users.

The operation must be **idempotent**:

* If the dummy user does not exist, create it.
* If the dummy user already exists, do not create another record.
* Running the seed operation multiple times must result in exactly one dummy user.

### 2. Dummy User Details

Use the following fixed values:

| Field       | Value                                       |
| ----------- | ------------------------------------------- |
| Name        | `Dummy User`                                |
| Email       | `dummy@spendify.local`                      |
| Username    | `dummy_user`                                |
| Password    | A securely hashed development-only password |
| Status      | `active`                                    |
| Environment | `development`                               |

If the existing database schema uses different column names, map these values to the appropriate fields.

Do **not** store the password in plain text.

---

## 3. Stable User ID

The dummy user should have a predictable identifier if the database design permits it.

Preferred identifier:

```text
dummy-user
```

If the database requires a UUID or automatically generated numeric ID, allow the database to generate the ID and identify the user using the unique email:

```text
dummy@spendify.local
```

The implementation must not depend on a hard-coded auto-generated database ID.

---

## 4. Database Constraints

The following values should be unique:

```text
email = dummy@spendify.local
username = dummy_user
```

Before inserting the record, check whether the user already exists.

Preferred approach:

```text
Find user by email
        |
        +-- Exists --> Reuse existing user
        |
        +-- Does not exist --> Create dummy user
```

Avoid creating duplicate records when the seed/setup command is executed repeatedly.

---

## 5. Slash Command Purpose

The dummy user will be used to add a dummy record in user table of db.py file using slash commands.

Examples of commands that may use this user include:

```text
/expense
/income
/balance
/expenses
/categories
/report
/help
```

The slash command implementation should be able to resolve the authenticated/requesting user to the dummy user's database record during development.

---

## 6. Development Seed

Create a database seed or initialization mechanism that can be executed during local development.

Suggested command:

```bash
python -m database.seed_dummy_user
```

If the project uses another database/ORM framework, use the project's existing migration and seeding conventions instead.

The seed operation should:

1. Connect to the configured development database.
2. Check for `dummy@db.local`.
3. Create the user if it does not exist.
4. Reuse the existing user if it already exists.
5. Commit the transaction.
6. Display the resulting user ID and email.
7. Exit successfully.

Example expected output:

```text
Dummy user ready.
User ID: <database-generated-id>
Email: dummy@db.local
Username: dummy_user
```

---

## 7. Password Handling

The password must never be stored directly in the database.

Use the same password hashing mechanism used by the application's normal user-registration/authentication system.

For local development, the password may be supplied through an environment variable:

```text
DUMMY_USER_PASSWORD
```

Example:

```bash
export DUMMY_USER_PASSWORD="development-only-password"
```

If the project already has a standard authentication configuration, reuse it rather than introducing a second password-hashing implementation.

Do not commit the actual password to Git.

---

## 8. Slash Command Authentication

For development purposes, slash commands should resolve requests to the dummy user without creating additional users.

The development flow should conceptually be:

```text
Slash Command Request
        |
        v
Identify requesting user
        |
        v
Development authentication
        |
        v
dummy@spendify.local
        |
        v
Database User
        |
        v
Execute Slash Command
```

Production authentication behavior must remain unchanged.

Do not add a permanent dummy-user bypass to production authentication.

---

## 9. Environment Protection

The dummy user must only be created when the application is running in a development/test environment.

Example:

```text
APP_ENV=development
```

The seed operation must refuse to create the dummy user when:

```text
APP_ENV=production
```

Example behavior:

```text
ERROR: Dummy users cannot be created in production.
```

This protection is mandatory.

---

## 10. Testing Requirements

Verify the following:

### Test 1 — First execution

Run:

```bash
python -m database.seed_dummy_user
```

Expected result:

```text
Dummy user created.
```

### Test 2 — Second execution

Run the same command again:

```bash
python -m database.seed_dummy_user
```

Expected result:

```text
Dummy user already exists.
```

The database must still contain exactly one dummy user.

### Test 3 — Database verification

Verify:

```text
email = dummy@spendify.local
```

Only one matching record should exist.

### Test 4 — Slash command

Execute a development slash command using the dummy user.

The command must successfully resolve:

```text
dummy@spendify.local
```

to the corresponding database user.

### Test 5 — Production protection

Attempt to run the seed operation with:

```text
APP_ENV=production
```

The operation must fail without creating or modifying the dummy user.

---

## 11. Files to Create or Modify

Follow the existing Spendify project structure.

Possible files include:

```text
database/
    seed_dummy_user.py
```

and, if required:

```text
database/
    __init__.py
```

Add or update tests according to the project's existing test structure.

Do not create duplicate database configuration files.

Do not modify unrelated application functionality.

---

## 12. Acceptance Criteria

The implementation is complete when all of the following are true:

* [ ] Exactly one dummy user can exist.
* [ ] Dummy user email is `dummy@spendify.local`.
* [ ] Dummy username is `dummy_user`.
* [ ] Password is securely hashed.
* [ ] Seed operation is idempotent.
* [ ] Re-running the seed does not create duplicates.
* [ ] The dummy user can be resolved by slash commands.
* [ ] Slash commands can use the dummy user's database ID.
* [ ] Dummy user creation is restricted to development/test environments.
* [ ] Production execution cannot create the dummy user.
* [ ] No hard-coded production credentials are introduced.
* [ ] No plaintext password is committed to the repository.
* [ ] Existing authentication/database conventions are reused.
* [ ] Tests verify creation, duplicate prevention, slash-command resolution, and production protection.

---

## Definition of Done

A developer should be able to clone the Spendify repository, configure the development database, run the dummy-user seed command once, and immediately use the resulting user for testing slash commands.

The implementation must be safe to execute repeatedly and must not introduce any production authentication bypass.
