Description

A combined Spendly custom slash-command skill for creating, running, validating, and reporting pytest tests for a feature according to its specification.

This command integrates the responsibilities of:

spec-test-writer — create or expand tests from the feature specification.

spec-test-runner — execute the tests, analyze results, and report whether the implementation satisfies the specification.

The specification is always the source of truth. Tests must validate intended behavior rather than simply mirror the current implementation.

Purpose

Use this command when a Spendly feature has been:

Implemented.

Modified.

Added or expanded.

Requested by the user for test coverage.

Requested by the user for verification.

The command should be able to:

Find the relevant feature specification.

Understand the intended behavior.

Inspect existing test conventions.

Create or update appropriate pytest tests when requested or when the workflow requires test creation.

Run the relevant tests.

Run the full suite when appropriate.

Analyze failures against the specification.

Clearly report test results and specification mismatches.

Key Principle

Follow the specification, not the code.

The feature specification defines correctness.

If the specification and implementation disagree:

Write tests that represent the specification.

Do not weaken assertions to match incorrect implementation behavior.

Do not modify production code to make tests pass.

Clearly report the specification/implementation mismatch.

Workflow

Phase 1 — Identify the Feature

Determine which Spendly feature the user wants to work with.

Look in:

.claude/specs/NN-*.md

If the user names a feature, locate its corresponding specification.

If no feature is named, use the most recently added or modified relevant specification.

Read these sections carefully:

Objective

UI/Webpage Impact

Backend Impact

Acceptance Criteria

These sections define the expected behavior.

Phase 2 — Inspect Existing Test Conventions

Before creating or modifying tests, inspect a couple of existing files under:

tests/

For example:

tests/test_profile.py

Follow the project's existing patterns.

Typical conventions include:

client fixture.

Temporary database setup.

db_module.DB_PATH monkeypatching.

init_db().

TESTING = True.

Small helpers such as:

register(client, ...)

login(client, ...)

Assertions based on:

HTTP status codes.

Redirect targets.

Flash messages.

HTML markers/classes/IDs.

Expected response content.

Do not unnecessarily introduce a different testing style.

Phase 3 — Use Implementation Only as an Interface Reference

It is acceptable to inspect:

app.py
database/db.py
templates/

only to determine how to interact with the application.

Use the implementation to discover:

Route paths.

HTTP methods.

Form field names.

Session keys.

HTML hooks.

Database setup requirements.

Existing interfaces required by the test client.

Do not use implementation logic to decide what the feature should do.

The specification remains the source of truth.

Phase 4 — Create or Update Tests

If tests are missing or the user asks for coverage, create or extend:

tests/test_<feature_name>.py

Follow the existing naming convention.

Tests should cover:

Golden Path

The normal successful workflow described in the Objective.

Acceptance Criteria

Every applicable item under the specification's Acceptance Criteria.

Relevant Edge/Error Cases

Include realistic cases implied by the specification, such as:

Invalid input.

Missing required fields.

Unauthenticated access.

Unauthorized access.

Empty states.

Invalid identifiers.

Expected validation errors.

Do not add speculative tests for behavior that the specification does not describe.

Phase 5 — Test Placement

Prefer:

tests/test_<feature_name>.py

Extend an existing test file when the feature clearly belongs there.

Examples:

Profile functionality → tests/test_profile.py
Expense functionality → tests/test_expenses.py
Authentication → tests/test_auth.py

Only create or edit files under:

tests/

unless the user explicitly asks for another artifact.

Phase 6 — Run the Tests

For a specific feature:

pytest tests/test_<feature_name>.py -q

For verbose diagnostics:

pytest tests/test_<feature_name>.py -v

For a specific test:

pytest tests/test_<feature_name>.py::test_<test_name> -q

If the feature could affect other functionality:

pytest -q

Prefer running the feature-specific tests first, followed by the full suite when appropriate.

Phase 7 — Analyze Test Results

Do not stop at whether pytest exits successfully.

Compare the test results with the relevant specification.

Determine whether failures are caused by:

A. Implementation Bug

The test correctly represents the specification, but the application does not satisfy it.

Report:

Test name.

Expected behavior.

Actual behavior.

Relevant acceptance criterion.

Likely implementation area.

Do not modify production code.

B. Specification/Implementation Mismatch

The specification requires behavior different from the current implementation.

Keep the test aligned with the specification and flag the discrepancy.

C. Test Bug

The test itself is incorrect or makes an invalid assumption.

Only change the test when test maintenance/correction is part of the user's request.

D. Environment/Setup Problem

Examples:

Missing dependency.

Import failure.

Database initialization problem.

Incorrect Python environment.

Missing configuration.

Permission problem.

Report these separately from application failures.

Phase 8 — Re-run After Test Changes

If tests were created or modified:

Run the relevant feature test file.

Fix test setup/assertion issues only when they are genuine test issues.

Re-run the tests.

If the feature tests pass and the change may interact with other functionality, run:

pytest -q

Never change an assertion merely to obtain a green result.

Phase 9 — Report Results

Use a concise, actionable report.

Test Command

pytest tests/test_<feature_name>.py -q

Result

X passed
Y failed
Z errors

Coverage

State which specification areas were tested:

Objective/golden path.

Acceptance Criteria.

Relevant edge/error cases.

Passing Tests

List the important passing tests.

Failed Tests

For each failure:

Test:
Expected:
Actual:
Classification:
Reason:

Classification should be one of:

Implementation bug
Spec/implementation mismatch
Test bug
Environment/setup issue

Spec Compliance

State whether the tested behavior currently satisfies the specification.

Recommended Next Step

Recommend the appropriate action:

Fix implementation.

Correct the test.

Update specification.

Resolve environment/setup issue.

Add missing coverage.

Re-run the full suite.

Boundaries

Only create or edit test files under tests/ when creating or modifying tests.

Never modify app.py to make a test pass.

Never modify database/db.py to make a test pass.

Never modify templates to make a test pass.

Never change production behavior to satisfy a test.

Never rewrite assertions solely to match buggy or incomplete implementation behavior.

Never ignore failing tests.

Never hide specification/implementation mismatches.

Never add speculative requirements.

Never claim that a feature is correct merely because pytest is green if important specification requirements are untested.

Never confuse environment failures with application bugs.

Do not create tests unless the user requests test creation/expansion or the workflow explicitly calls for generating tests after a feature implementation/modification.

Recommended Slash-Command Behavior

The custom slash command should support the following intent patterns.

Create and Run

When the user asks to test a newly implemented feature:

1. Find the feature spec.
2. Read Objective and Acceptance Criteria.
3. Inspect existing test conventions.
4. Inspect implementation only for test interfaces.
5. Create/update the feature tests.
6. Run the feature tests.
7. Analyze failures against the spec.
8. Run the full suite if appropriate.
9. Report results and discrepancies.

Run Existing Tests

When tests already exist and the user asks to run them:

1. Find the relevant spec.
2. Find the relevant tests.
3. Run the feature tests.
4. Analyze failures against the spec.
5. Run the full suite if appropriate.
6. Report results.

Expand Coverage

When the user asks to add coverage:

1. Read the specification.
2. Identify uncovered Objective/Acceptance Criteria behavior.
3. Inspect existing test conventions.
4. Add tests only for specified behavior.
5. Run the new/affected tests.
6. Run the full suite when appropriate.
7. Report coverage and results.

Debug Failures

When the user asks why tests are failing:

1. Reproduce the failure.
2. Read the relevant specification.
3. Inspect the failing test.
4. Inspect implementation only as needed.
5. Classify the failure.
6. Explain the cause.
7. Recommend the next action.

Example Commands

Feature test

pytest tests/test_profile.py -q

Verbose feature test

pytest tests/test_profile.py -v

Individual test

pytest tests/test_profile.py::test_profile_update -q

Full suite

pytest -q

Success Criteria

The command succeeds when:

The correct specification is identified.

The specification is treated as the source of truth.

Existing test conventions are followed.

Relevant tests are created or located correctly.

The golden path is covered.

Applicable Acceptance Criteria are covered.

Relevant edge/error cases are covered.

Tests execute successfully or failures are clearly explained.

Production code is never changed merely to make tests pass.

Specification/implementation mismatches are surfaced.

The final report is accurate and actionable.

Relationship Between the Two Skills

This combined command merges:

spec-test-writer

Responsibility:

Create pytest tests that verify the behavior described by the specification.

spec-test-runner

Responsibility:

Execute those tests, validate the results against the specification, and report failures or mismatches.

Combined workflow:

User specification
       ↓
.claude/specs/
       ↓
Understand Objective + Acceptance Criteria
       ↓
Inspect existing tests
       ↓
Create / update tests
       ↓
Run pytest
       ↓
Analyze results
       ↓
Compare with specification
       ↓
Classify failures
       ↓
Report clearly

Final Principle

Write tests for what Spendly is supposed to do, run them correctly, and report honestly when the implementation does not match the specification.
