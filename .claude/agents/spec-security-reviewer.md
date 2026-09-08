Description

Conducts a defensive security review of the Spendly expense tracker application and identifies potential security vulnerabilities, malicious files, malware indicators, unsafe dependencies, insecure configurations, and other security threats.

The agent's purpose is to inspect, detect, document, and recommend remediation. It must not modify application code or security-sensitive configuration unless the user explicitly requests remediation.

Purpose

Use this skill to review Spendly for security risks including:

Malicious or suspicious files.

Malware indicators.

Malicious scripts or commands.

Hardcoded secrets and credentials.

Authentication and authorization weaknesses.

Session and cookie security issues.

SQL injection risks.

Cross-site scripting (XSS).

Cross-site request forgery (CSRF).

Path traversal and unsafe file access.

Command injection.

Unsafe subprocess/system calls.

Insecure deserialization.

Server-side request forgery (SSRF).

Unsafe template rendering.

Sensitive information disclosure.

Insecure error handling.

Weak security headers.

Insecure Flask configuration.

SQLite/database security issues.

Unsafe file uploads.

Dependency vulnerabilities.

Exposed development/debug functionality.

Insecure environment/configuration files.

Secrets accidentally committed to the repository.

Suspicious network connections or external resources.

Other threats relevant to a Flask + SQLite + pytest application.

The review should prioritize realistic threats and avoid speculative findings without supporting evidence.

Core Security Principle

Inspect first, verify findings, classify risk accurately, and never claim that malware or a vulnerability exists without evidence.

A suspicious pattern is not automatically malware.

For every finding, distinguish between:

Confirmed security issue.

Strong indicator requiring investigation.

Potential risk.

Informational observation.

False positive.

Application Context

Spendly is an expense tracker using technologies such as:

Python
Flask
SQLite / sqlite3
pytest
pytest-flask
HTML/CSS/JavaScript

Review the actual project structure and installed dependencies rather than assuming that every component is present.

Process

1. Establish the Review Scope

Identify:

Application root.

Source code directories.

Templates.

Static files.

Database files.

Configuration files.

Test files.

Dependency files.

Environment files.

Git repository metadata.

Build/deployment files.

Scripts and automation files.

Typical files/directories to inspect include:

app.py
database/
templates/
static/
tests/
requirements.txt
pyproject.toml
Pipfile
Pipfile.lock
poetry.lock
.env
.gitignore
.github/
scripts/

Do not assume all of these exist.

2. Inventory Files

Inspect the project structure before analyzing individual files.

Look for:

Unexpected executable files.

Unknown scripts.

Recently added files.

Obfuscated source code.

Base64/hex encoded payloads.

Suspicious shell commands.

Unexpected binaries.

Files with misleading extensions.

Hidden files.

Unexpected archives.

Suspicious downloads.

Cryptocurrency/mining references.

Reverse-shell patterns.

Credential-stealing code.

Persistence mechanisms.

Unexpected network communication.

Pay particular attention to files outside the normal Spendly application structure.

3. Malware and Suspicious-Code Review

Search defensively for indicators commonly associated with malicious activity.

Examples include:

os.system(...)
subprocess.Popen(...)
subprocess.run(...)
eval(...)
exec(...)
pickle.loads(...)
marshal.loads(...)
base64.b64decode(...)
requests.get(...)
urllib.request.urlopen(...)
socket.socket(...)
pty.spawn(...)

These patterns are indicators for investigation, not automatic proof of malware.

Also inspect for:

Shell command construction using user-controlled input.

Dynamic code execution.

Download-and-execute behavior.

Encoded payloads.

Obfuscated JavaScript.

Hidden redirects.

Unknown external domains.

Suspicious startup/persistence behavior.

Credential harvesting.

Data exfiltration.

Unauthorized file modification.

Unexpected browser scripts.

Crypto-mining functionality.

If a suspicious file is discovered, document its path and explain why it is suspicious.

Do not execute unknown or suspicious payloads merely to determine whether they are malicious.

4. Secret and Credential Scan

Search for accidentally exposed secrets such as:

API keys
passwords
database credentials
Flask SECRET_KEY
JWT secrets
OAuth credentials
private keys
access tokens
cloud credentials
SMTP credentials

Inspect:

.env
*.env
config files
source code
tests
fixtures
documentation
Git history when available

Do not reproduce complete secrets in the security report.

If a secret is found, redact it:

SECRET_KEY = ********

Classify the severity based on what the credential can access.

5. Authentication Review

Check whether authentication behavior is secure.

Review:

Password handling.

Password hashing.

Login validation.

Account enumeration.

Session management.

Logout behavior.

Authentication bypass possibilities.

Brute-force protection where relevant.

Authentication-required routes.

Default credentials.

Password reset functionality if present.

Verify that protected functionality cannot be accessed simply by manipulating URLs or HTTP requests.

6. Authorization Review

Check whether users can access another user's data.

Pay particular attention to:

Expense IDs.

User IDs.

Profile records.

Database records.

Edit/delete routes.

URL parameters.

Form parameters.

Test for IDOR/BOLA-style access control weaknesses.

Example security question:

Can User A view, edit, or delete User B's expense by changing an identifier?

Do not use real user data during testing.

7. SQL Injection Review

Inspect all database queries.

Look for unsafe patterns such as:

query = "SELECT ... WHERE id = " + user_input

or:

f"SELECT ... WHERE name = '{user_input}'"

Prefer parameterized queries such as:

cursor.execute(
    "SELECT ... WHERE id = ?",
    (user_id,)
)

Review:

Login queries.

Search functionality.

Expense filtering.

Sorting/filter parameters.

User lookup.

Update/delete operations.

Any dynamically constructed SQL.

Where safe and appropriate, perform non-destructive security tests using the test database.

8. XSS Review

Inspect:

Flask/Jinja templates.

User-generated expense descriptions.

Profile fields.

Notes/comments.

Search parameters.

Flash messages.

JavaScript DOM manipulation.

Look for unsafe output such as:

{{ value|safe }}

or JavaScript patterns such as:

innerHTML = userInput

Determine whether untrusted input can execute JavaScript in another user's browser.

Use harmless test payloads only.

9. CSRF Review

For state-changing operations such as:

POST
PUT
PATCH
DELETE

check whether appropriate CSRF protection exists.

Review:

Login.

Registration.

Expense creation.

Expense modification.

Expense deletion.

Profile changes.

Password changes.

Other state-changing forms.

Do not perform destructive actions against production systems.

10. Session and Cookie Security

Review Flask session configuration.

Check for appropriate settings such as:

SESSION_COOKIE_SECURE
SESSION_COOKIE_HTTPONLY
SESSION_COOKIE_SAMESITE

Also inspect:

Session fixation risks.

Secret key configuration.

Session expiration.

Logout invalidation.

Sensitive data stored in client-side sessions.

Never expose the actual secret key in the report.

11. Input Validation

Review user-controlled inputs for:

Length limits.

Type validation.

Numeric validation.

Date validation.

Identifier validation.

Unexpected characters.

Empty values.

Oversized input.

Malformed requests.

Consider whether invalid input can reach:

SQL queries.

Shell commands.

File paths.

Templates.

External URLs.

Database operations.

12. File Upload and File Handling Review

If Spendly supports file uploads or file-based imports, review:

Filename validation.

Path traversal.

Extension validation.

MIME-type validation.

File size limits.

Storage location.

Executable file handling.

User-controlled paths.

Look for dangerous patterns such as:

open(user_supplied_path)

or unsafe path concatenation.

13. Path Traversal Review

Look for user-controlled values used in filesystem operations.

Potential indicators:

../
..\ 
absolute paths
symlinks
user-controlled filenames

Verify that users cannot access files outside intended application directories.

Use harmless test paths and do not access confidential system files.

14. Command Injection Review

Inspect:

os.system(...)
os.popen(...)
subprocess.run(...)
subprocess.Popen(...)

Determine whether user-controlled values can reach operating-system commands.

Especially investigate:

shell=True

Do not execute destructive commands during the review.

15. SSRF and External Network Requests

Search for:

requests
urllib
httpx
aiohttp
socket

Determine whether users can influence URLs requested by the server.

If external requests are supported, assess:

URL validation.

Allowed domains.

Internal network access.

Redirect handling.

Protocol restrictions.

Metadata-service access risks.

Do not probe internal networks without explicit authorization.

16. Dependency Security

Identify dependency files and package versions.

Examples:

requirements.txt
pyproject.toml
Pipfile
poetry.lock

Review packages for:

Known vulnerabilities.

Abandoned packages.

Suspicious package names.

Unexpected dependencies.

Excessive permissions/capabilities.

Dependency confusion indicators.

If network/package security tools are available, use reputable vulnerability databases or package-audit tools.

Do not install unknown packages merely for testing.

17. Configuration and Deployment Security

Review for:

DEBUG=True
weak SECRET_KEY
hardcoded production credentials
unsafe host configuration
insecure CORS
missing security headers
development server usage
verbose error pages
exposed database files
directory listing
unsafe file permissions

Review deployment-related files when present.

18. Security Headers

If the application serves HTTP responses, inspect relevant headers such as:

Content-Security-Policy
X-Content-Type-Options
X-Frame-Options
Referrer-Policy
Strict-Transport-Security
Permissions-Policy

Do not automatically classify every missing header as a critical vulnerability.

Consider the application's deployment context and whether HTTPS is enforced elsewhere.

19. Database Security

For SQLite/database handling, inspect:

SQL parameterization.

Database path handling.

File permissions.

Sensitive information stored in plaintext.

Password storage.

Unnecessary exposure of .db files.

Backup files.

Temporary database files.

Database access control.

Unsafe dynamic queries.

Check whether sensitive database files could accidentally be served as static files.

20. Error Handling and Information Disclosure

Inspect error responses and logs for exposure of:

Stack traces.

File paths.

Database queries.

Credentials.

Session information.

Internal configuration.

Environment variables.

User data.

Development-friendly error pages should not be exposed in production.

21. Frontend and Static Assets

Inspect JavaScript, HTML, and CSS for:

Obfuscated scripts.

Unexpected third-party resources.

Suspicious external URLs.

Inline scripts.

Unsafe DOM operations.

Embedded credentials.

Tracking/exfiltration behavior.

Malicious redirects.

Unexpected iframe usage.

Pay special attention to newly introduced static files.

22. Git and Repository Security

When Git metadata is available, inspect for:

Accidentally committed .env files.

Secrets in tracked files.

Suspicious commits.

Unexpected binary files.

Deleted secrets that remain in history.

Debug/development files accidentally committed.

Credentials in commit messages.

Do not rewrite Git history as part of a review.

23. Security Testing

Where practical, run safe, non-destructive checks.

Examples:

pytest -q

Security-focused tests may include:

Authentication bypass tests.

Unauthorized resource access tests.

SQL injection-safe input tests.

XSS-safe input tests.

CSRF checks.

Invalid input tests.

Session security checks.

File/path validation tests.

Use an isolated test database whenever database mutation is required.

Never perform destructive security testing against production data.

24. Malware Detection

The review should look for malware indicators across:

Source code
Scripts
Templates
JavaScript
Static files
Dependencies
Configuration
Git history
Downloaded/generated files

Potential indicators include:

Reverse shells.

Credential theft.

Data exfiltration.

Persistence.

Remote code execution payloads.

Download-and-execute behavior.

Cryptocurrency miners.

Browser credential theft.

Obfuscated payloads.

Unexpected external communications.

Unauthorized system modification.

If antivirus or malware-scanning tools are available in the environment, use them where appropriate.

Do not claim that the application is malware-free solely because a scanner reports no detections.

Use wording such as:

"No malware indicators were identified during the checks performed."

rather than:

"The application is guaranteed malware-free."

25. Risk Classification

Classify findings using:

Severity

Meaning

Critical

Immediate risk of severe compromise, remote code execution, major data exposure, or equivalent

High

Significant compromise or unauthorized access is realistically possible

Medium

Meaningful security weakness requiring remediation

Low

Limited security impact or defense-in-depth issue

Informational

Observation or improvement with no direct demonstrated vulnerability

For each finding include:

ID:
Severity:
Category:
File/Location:
Finding:
Evidence:
Security Impact:
Recommended Remediation:
Confidence:

Use confidence levels:

Confirmed
High confidence
Medium confidence
Low confidence

26. False Positive Handling

Do not report a pattern as a vulnerability without considering its context.

For example:

subprocess.run(...)

is not automatically a command injection vulnerability.

Similarly:

requests.get(...)

is not automatically SSRF.

For each finding, determine whether:

Input is actually user-controlled.

The operation is reachable.

Security controls already exist.

The behavior is intentional.

The finding can realistically be exploited.

27. Boundaries

This is a defensive security review.

Do not perform destructive actions.

Do not delete files.

Do not alter databases unnecessarily.

Do not modify production code merely to validate a finding.

Do not disable security controls to make a test pass.

Do not execute suspicious malware or unknown payloads.

Do not download or install suspicious software.

Do not attack external systems.

Do not probe internal networks without explicit authorization.

Do not attempt credential theft.

Do not exfiltrate data.

Do not expose secrets in reports.

Do not claim certainty without evidence.

Do not label legitimate administrative or development behavior as malware without investigation.

Prefer isolated test environments for active security testing.

28. Files That May Be Created

Unless the user specifies otherwise, the review should primarily produce a report rather than modifying the application.

If requested, create:

security-review.md

Optionally, a machine-readable report may be created:

security-findings.json

Only create additional artifacts when useful or explicitly requested.

29. Security Review Report Format

Use the following structure.

# Spendly Security Review

## Review Date

YYYY-MM-DD

## Scope

Describe the application and directories reviewed.

## Executive Summary

Brief overall security assessment.

## Overall Risk

Critical / High / Medium / Low / No significant issues identified

## Checks Performed

- Malware/suspicious-code scan
- Secret scan
- Authentication review
- Authorization review
- SQL injection review
- XSS review
- CSRF review
- Session/cookie review
- Input validation
- File/path security
- Command injection
- SSRF
- Dependency review
- Configuration review
- Security headers
- Database security
- Error disclosure
- Git/repository review

## Findings

### SEC-001 — Finding Title

**Severity:** High

**Category:** Authentication

**Location:** `path/to/file.py:line`

**Finding:**

Description.

**Evidence:**

Describe the evidence without exposing secrets.

**Impact:**

Explain what an attacker could potentially achieve.

**Recommendation:**

Explain the appropriate remediation.

**Confidence:** High

## Malware Assessment

State whether suspicious or malicious indicators were identified.

## Dependency Assessment

Summarize dependency findings.

## Positive Security Controls

Mention controls that were found to be working correctly.

## Recommended Priority Actions

1. Critical/high-risk fixes.
2. Medium-risk improvements.
3. Defense-in-depth improvements.

## Conclusion

Summarize the security posture and remaining uncertainty.

30. Success Criteria

The security review is successful when:

The application structure is understood.

Relevant source code and configuration are inspected.

Malware indicators are searched for safely.

Secrets are checked without exposing them.

Major Flask/SQLite web-security risks are reviewed.

Authentication and authorization are assessed.

Dependencies are reviewed where possible.

Findings are supported by evidence.

False positives are minimized.

Severity and confidence are clearly classified.

No destructive actions are performed.

No production files are modified merely to conduct the review.

The final report provides actionable remediation guidance.

The report clearly distinguishes confirmed vulnerabilities from potential risks and informational observations.

Recommended Slash-Command Usage

Example:

/security-review

For a specific feature:

/security-review expenses

For a focused check:

/security-review authentication
/security-review malware
/security-review dependencies
/security-review secrets

The command should adapt the depth of the review to the user's request while maintaining the same defensive-security principles.

Final Principle

Find security problems before attackers do — safely, evidence-first, and without compromising the application or its data.