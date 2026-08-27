# seed-expenses.md

## Purpose

Define the specification for a slash command that seeds expense records into the **existing `spendly.db` database** used by the Spendly expenses-tracker webpage.

The command must allow the user to choose:

1. The **number of expenses** to create.
2. The **duration period** over which those expenses should be distributed.

The seeded data is intended for development, UI testing, dashboard validation, filtering, charts, and duration-wise expense analysis. It must work with the existing database/schema rather than creating a separate database.

---

## Slash Command

### Command

`/seed-expenses`

### Objective

Create a user-selected number of realistic dummy expense records in the existing `spendly.db`.

The command should be interactive and should not require the user to manually construct expense records.

### User Interaction

When `/seed-expenses` is invoked, prompt the user for:

#### 1. Number of expenses

Offer selectable choices and allow a custom number where supported.

Suggested choices:

* `10`
* `25`
* `50`
* `100`
* `250`
* `500`
* `Custom`

Validation:

* Must be a positive integer.
* Apply a configurable maximum to prevent accidental database flooding.
* Reject zero, negative numbers, non-numeric values, and excessively large values.

#### 2. Duration period

Offer common duration choices:

* `Last 7 days`
* `Last 30 days`
* `Last 3 months`
* `Last 6 months`
* `Last 12 months`
* `Custom`

For `Custom`, request a start date and end date.

Validation:

* Start date must not be after end date.
* Dates must be valid.
* The duration must be compatible with the application's date format.

---

## Data Generation Rules

Generate realistic development/test expense data.

Each generated record should use the fields already defined by the existing `spendly.db` schema.

Do **not** create a parallel expense table or replace the existing schema.

At minimum, generated expenses should represent:

* Expense date
* Expense amount
* Expense category
* Expense description/merchant
* Payment method, if supported by the existing schema
* User/owner identifier, if supported by the existing schema
* Created/updated timestamps, if supported by the existing schema

### Amounts

Generate plausible expense amounts using the application's existing currency convention.

Avoid generating identical amounts for every record.

### Categories

Use the expense categories already supported by the application.

If the existing application has no fixed category list, use a small realistic development set such as:

* Food
* Groceries
* Transport
* Utilities
* Shopping
* Healthcare
* Entertainment
* Education
* Bills
* Other

Do not introduce categories that conflict with existing database constraints.

### Payment Methods

If the existing schema supports payment method, use realistic values already accepted by the application, for example:

* Cash
* UPI
* Debit Card
* Credit Card
* Bank Transfer

Do not add unsupported enum values.

---

## Duration Distribution

Distribute the requested number of expenses across the selected duration.

The distribution should not place all records on the same date.

Use randomized dates within the selected date range while maintaining reproducible behavior where practical through a configurable random seed.

Example:

`/seed-expenses` → `50` expenses → `Last 3 months`

Result:

* 50 expense records
* Dates spread across approximately the previous 3 months
* Varied categories
* Varied amounts
* Varied descriptions/merchants
* Valid records compatible with the current database schema

---

## Existing Database Requirement

The command must operate on the **ongoing `spendly.db`** used by the Spendly expenses-tracker webpage.

### Mandatory behavior

* Locate/use the application's existing database configuration.
* Reuse the existing database connection/session layer.
* Reuse the existing Expense model/schema where available.
* Do not create `spendly_test.db`, `expenses.db`, or another replacement database.
* Do not drop or recreate existing tables.
* Do not overwrite existing expense records unless the command explicitly provides a future cleanup/reset feature.
* Preserve existing users and other application data.

### Transaction Safety

Insert generated records inside a database transaction.

If insertion fails:

* Roll back the transaction.
* Do not leave a partially seeded dataset.
* Return a clear error message.

If insertion succeeds:

* Commit the transaction.
* Return a summary of what was created.

---

## Slash Command Output

After successful execution, display a concise confirmation such as:

```text
Expense seeding completed.

Expenses created: 50
Duration: Last 3 months
Date range: YYYY-MM-DD to YYYY-MM-DD

The new expenses are now available in the Spendly expense tracker.
```

For an error:

```text
Expense seeding failed.

No expense records were added.
Reason: <clear error message>
```

---

## Duplicate/Repeat Execution

Repeated execution must be safe.

The command should not delete existing expenses.

Each successful execution should create a new set of records unless the existing application has a defined test-data identifier that can be reused.

If the database schema supports metadata/source tagging, preferably mark generated records as development seed data, for example:

`source = "seed-expenses"`

Only add such a field if the current schema already supports it or the database migration explicitly introduces it.

---

## Webpage Integration

The seeded records must immediately support the existing Spendly expenses-tracker webpage.

After seeding, verify that the webpage can use the records for:

* Total expenses
* Number of expenses
* Daily expenses
* Weekly expenses
* Monthly expenses
* Category-wise expenses
* Duration-wise expenses
* Expense list/table
* Expense charts/visualizations
* Date-range filtering
* Dashboard summaries

The slash command is a **data-generation/testing feature**, not a replacement for the normal expense-entry workflow.

---

## Duration-Wise Expense Analysis

The seeded data must make it possible to test duration-based expense queries.

The application should be able to calculate at least:

### Number of expenses

For a selected date range:

`COUNT(expenses)`

### Total expenses

For a selected date range:

`SUM(expense_amount)`

### Average expense

For a selected date range:

`AVG(expense_amount)`

### Period grouping

Support the grouping already used by the webpage, such as:

* Daily
* Weekly
* Monthly

Example:

```text
Date Range: Last 6 months

Month       No. of Expenses    Total Expense
----------  -----------------  -------------
Month 1          18              ₹xx,xxx
Month 2          24              ₹xx,xxx
Month 3          21              ₹xx,xxx
...
```

---

## Suggested Command Flow

```text
/seed-expenses

        ↓

How many expenses?
[10] [25] [50] [100] [250] [Custom]

        ↓

Select duration
[7 Days]
[30 Days]
[3 Months]
[6 Months]
[12 Months]
[Custom]

        ↓

Review

Expenses: 50
Duration: Last 3 months
Database: spendly.db

[Generate Expenses] [Cancel]

        ↓

Validate input

        ↓

Generate realistic expense records

        ↓

Insert into existing spendly.db

        ↓

Commit transaction

        ↓

Show result

50 expenses successfully created.
```

---

## Implementation Requirements

1. Inspect the existing Spendly project before implementing the command.
2. Identify the existing database connection configuration.
3. Identify the existing Expense model/table.
4. Identify required fields and database constraints.
5. Reuse existing validation and serialization logic where possible.
6. Implement `/seed-expenses` using the project's existing slash-command architecture.
7. Do not duplicate database models or connection logic.
8. Keep the command isolated from production expense-entry functionality.
9. Ensure generated records appear in the existing webpage without additional manual database copying.
10. Add error handling and transaction rollback.
11. Add tests for:

    * Number selection
    * Duration selection
    * Custom date range
    * Invalid number
    * Invalid date range
    * Successful insertion
    * Transaction rollback
    * Existing records remaining unchanged
    * Duration-wise aggregation

---

## Acceptance Criteria

The implementation is complete when:

* [ ] `/seed-expenses` is available in the Spendly slash-command system.
* [ ] The user can choose the number of expenses.
* [ ] The user can choose a predefined duration.
* [ ] The user can enter a custom number.
* [ ] The user can enter a custom date range.
* [ ] Input validation prevents invalid requests.
* [ ] Records are inserted into the existing `spendly.db`.
* [ ] Existing expense records are preserved.
* [ ] Generated dates are distributed across the selected duration.
* [ ] Generated records satisfy the current database schema.
* [ ] Failed operations roll back cleanly.
* [ ] Successful operations commit cleanly.
* [ ] The seeded records appear on the existing expenses-tracker webpage.
* [ ] Number-of-expenses calculations work.
* [ ] Duration-wise expense calculations work.
* [ ] Daily/weekly/monthly aggregation can be tested with the seeded data.
* [ ] The command does not create a second database.

---

## Important Development Constraint

Before writing implementation code, inspect the current Spendly project and **adapt this specification to the actual `spendly.db` schema, Expense model, existing slash-command mechanism, and webpage data layer**.

Do not assume field names, table names, ORM framework, or command framework when those details can be obtained from the existing project.

The objective is to extend the existing Spendly application—not to build a separate expense-seeding system.
