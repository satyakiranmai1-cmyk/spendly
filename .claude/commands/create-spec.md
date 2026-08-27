ep-number> <feature-name>

Command Inputs

Step Number: Sequential implementation number for the feature.

Feature Name: Short, clear name of the feature to be prepared.

Example

/next-feature 03 Monthly Expense Summary

Feature Specification Template

For every /next-feature request, prepare the following sections:

Step Number

<step-number>

Feature Name

<feature-name>

Objective

Describe what the feature should accomplish for the Spendly expenses-tracker webpage.

Database Impact

Identify whether the feature requires changes to spendly.db.

Include, where applicable:

Existing tables to use

New tables required

New columns required

Relationships or foreign keys

Indexes

Migration requirements

Data validation requirements

UI / Webpage Impact

Describe the pages, components, forms, dashboards, filters, buttons, or navigation elements affected.

Backend Impact

Describe:

Routes/endpoints

Business logic

Database queries

Validation

Error handling

Authentication/authorization considerations

Implementation Steps

Review the existing Spendly project structure.

Inspect spendly.db and identify relevant tables and relationships.

Define the required database changes, if any.

Define the backend changes.

Define the frontend/UI changes.

Implement the feature without breaking existing functionality.

Update database migrations or initialization scripts when required.

Test the feature with representative expense data.

Test existing Spendly functionality for regressions.

Document the completed feature and any database changes.

Acceptance Criteria

Feature is implemented according to the feature objective.

spendly.db changes are documented and applied safely.

Existing expense data is preserved.

Existing Spendly features continue to work.

UI is responsive and user-friendly.

Backend validation and error handling are implemented.

Database queries are tested.

Feature works with realistic test data.

No unnecessary duplicate tables, columns, or logic are introduced.

Deliverables

The /next-feature command should produce:

A feature implementation specification.

Required database/schema changes.

Backend implementation requirements.

Frontend/UI implementation requirements.

Testing requirements.

Acceptance criteria.

A clear list of files expected to be created or modified.

Slash Command Behavior

When /next-feature is invoked:

Read the supplied step number and feature name.

Inspect the current Spendly project and spendly.db structure before proposing schema changes.

Determine how the new feature fits into the existing application.

Avoid changing unrelated functionality.

Prefer reusing existing tables, services, routes, and UI components where appropriate.

Do not delete or overwrite existing user expense data.

Generate an implementation-ready specification using the template above.

Clearly identify any assumptions that require confirmation before implementation.

Naming Convention

Use:

Step <number> - <Feature Name>

Example:

Step 03 - Monthly Expense Summary

The step number must remain sequential so that future /next-feature commands can continue the Spendly development roadmap.