Description

Runs and validates pytest test cases for Spendly features according to the user's specifications and the feature specs in .claude/specs/.

The purpose is to ensure that the implemented code behaves as intended, that the relevant tests execute correctly, and that failures are clearly reported without modifying production code or changing tests merely to make them pass.

Purpose

Use this skill to:

Run tests for a specific Spendly feature.

Run the full pytest suite when appropriate.

Validate test results against the feature specification.

Identify test failures, errors, and likely causes.

Distinguish between:

A genuine implementation bug.

A test bug.

A specification/implementation mismatch.

An environment or setup problem.

Report results clearly to the user.

Invoke this skill when the user asks to:

Run or test a feature.

Verify that code works correctly according to specifications.

Check whether newly created tests pass.

Run a specific test file or the complete test suite.

Investigate test failures.

Key Principle

Validate the specification, not just the current implementation.

Tests and their results must be interpreted against the intended behavior described in the relevant specification. Never hide an implementation defect by changing an assertion simply because the current code behaves differently.

Process

1. Identify the feature and specification

Determine which feature the user wants tested.

Look in:

.claude/specs/NN-*.md

If the user names a feature, locate its corresponding specification.

If no feature is named, use the most recently added or modified relevant specification.

Read the specification carefully, especially:

Objective

UI/Webpage Impact

Backend Impact

Acceptance Criteria

These define the expected behavior against which the test results should be evaluated.

2. Locate the relevant tests

Look under:

tests/

Identify the test file associated with the feature.

Typical naming:

tests/test_<feature_name>.py

If the feature does not have a dedicated test file, determine whether its tests belong in an existing feature test file.

Do not create or modify tests unless the user explicitly asks for test creation or expansion. The spec-test-writer skill is responsible for writing tests.

3. Inspect the test environment

Before running tests, inspect only what is necessary to understand how the tests should be executed.

Relevant files may include:

pytest.ini
pyproject.toml
requirements.txt
conftest.py
app.py
database/db.py

Check for:

pytest configuration

test discovery rules

Flask test configuration

required fixtures

database setup

application startup requirements

relevant environment variables

Do not modify production files or configuration merely to make tests pass.

4. Run the appropriate tests

For a specific feature, prefer:

pytest tests/test_<feature_name>.py -q

For a specific test:

pytest tests/test_<feature_name>.py::test_<test_name> -q

For more diagnostic output:

pytest tests/test_<feature_name>.py -v

If changes could affect multiple features, run the full suite:

pytest -q

When useful, run the full suite after the feature-specific tests pass.

5. Analyze the results

Classify each failure or error before reporting it.

A. Test passes

The test successfully validates the expected behavior.

B. Implementation bug

The test correctly represents the specification, but the application does not satisfy the expected behavior.

Report:

Failing test

Expected behavior

Actual behavior

Likely implementation area

Relevant acceptance criterion

Do not modify production code.

C. Specification/implementation mismatch

The specification requires behavior different from the current implementation.

Keep the test aligned with the specification and explicitly flag the mismatch.

D. Test bug

The test itself is incorrect, incomplete, or makes an invalid assumption.

Only modify the test if the user has asked for test maintenance or correction.

E. Environment/setup failure

Examples:

Missing dependency

Database initialization failure

Import error

Incorrect Python environment

Missing configuration

Permission problem

Clearly separate environment failures from application failures.

Spec Compliance Checks

After running tests, compare the coverage/results with the specification.

Check whether the relevant tests address:

The Objective/golden path.

Every Acceptance Criteria item.

Important validation and error behavior described by the spec.

Authentication/authorization behavior when applicable.

Empty states when applicable.

Expected UI markers, flash messages, redirects, or response status codes when specified.

Do not invent requirements that are not present in the specification.

Failure Investigation

When a test fails:

Read the complete pytest failure output.

Identify the failing assertion or error.

Check the relevant specification.

Inspect the implementation only as needed to understand the failure.

Determine whether the failure is:

implementation defect,

test defect,

spec/implementation mismatch,

environment/setup issue.

Report the conclusion clearly.

Do not immediately change code or tests to make the suite green.

Boundaries

Do not modify app.py, database/db.py, templates, or other production files.

Do not modify configuration simply to suppress a failure.

Do not rewrite tests solely to match buggy or incomplete implementation behavior.

Do not ignore failing tests.

Do not claim that a feature is correct merely because pytest exits successfully if the tests do not cover the relevant specification requirements.

Do not add speculative requirements that are absent from the specification.

Do not create new tests unless explicitly requested; use spec-test-writer for test creation.

Do not hide environment/setup failures as application bugs.

Do not treat every failure as an implementation bug without checking the specification and test itself.

Reporting Format

Provide a concise report containing:

Test Command

pytest tests/test_<feature_name>.py -q

Result

X passed
Y failed
Z errors

Passing Tests

List the important tests that passed.

Failed Tests

For each failure, report:

Test:
Expected:
Actual:
Classification:
Reason:

Spec Compliance

State whether the tested behavior satisfies the relevant Objective and Acceptance Criteria.

Recommended Next Step

Examples:

Fix the implementation.

Correct the test.

Update the specification.

Resolve the environment/setup issue.

Add missing test coverage using spec-test-writer.

Example Workflow

For a feature called profile:

pytest tests/test_profile.py -q

If the feature-specific tests pass and the change could affect other functionality:

pytest -q

Then compare the results with:

.claude/specs/<profile-spec>.md

Report whether the implementation satisfies the specification rather than simply reporting that pytest is green.

Success Criteria

The skill succeeds when:

The correct feature tests are identified.

Tests are executed using the project's pytest conventions.

Test output is accurately interpreted.

Failures are classified correctly.

Specification requirements are used as the source of truth.

Production code is not modified to make tests pass.

Test assertions are not weakened to accommodate incorrect behavior.

The user receives a clear and actionable test report.

Relationship to Other Spendly Skills

spec-test-writer

Responsible for creating or expanding pytest tests from a feature specification.

spec-test-runner

Responsible for executing, validating, analyzing, and reporting test results.

Recommended workflow:

Feature implementation
        ↓
spec-test-writer
        ↓
Create/update tests
        ↓
spec-test-runner
        ↓
Run tests
        ↓
Analyze against specification
        ↓
Report pass/fail/mismatch