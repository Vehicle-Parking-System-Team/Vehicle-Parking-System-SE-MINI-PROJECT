# US-32 shared security verification evidence

Issue: [#52](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/52).
Executed locally on 27 October 2026. This is evidence for the
[shared security increment](../design/US32-security.md), not full story acceptance.

## Observed results

| Check | Environment and command | Result |
| --- | --- | --- |
| Django system check | Windows, Python 3.12.12, Django 5.2.18; `python manage.py check` from `backend/` | Pass; no issues |
| Focused security checks | Temporary SQLite; `python manage.py test common.tests.test_security --verbosity 1` | Pass; 16 tests |
| Complete backend regression | Same environment; `python manage.py test --verbosity 1` from `backend/` | 307 discovered; 298 passed, 9 skipped; 112.456 seconds |
| Frontend regression | Node.js 22; `npm test` from `frontend/` | 68 passed |
| Frontend lint/build | `npm run lint`, `npm run build` | Pass; existing large-chunk warning remains |
| Python source scan | Bandit 1.9.4; `python -m bandit -r backend --severity-level high` | Zero high, zero medium; 47 low-severity findings reported in counts; no suppressions |
| Secret scan | Checksum-verified Gitleaks 8.30.1; `gitleaks dir <source-snapshot> --redact --no-banner` | No detected leaks in tracked/proposed files |

All Django executions supplied a generated environment signing key. The local
secret scan copied tracked and proposed files into a temporary directory outside
the repository, excluding ignored `.env`, virtual environments and dependencies.
CI scans its clean checkout. Neither scan covers historical commits.

The nine SQLite skips are target-database concurrency checks; PostgreSQL acceptance
must use the existing PostgreSQL CI job. Sanitized errors printed by deliberate
fault-injection tests are expected and did not fail the suite. CI results are
reported by the PR checks and must be inspected separately from these local results.

## Focused test inventory

Tests live in `backend/common/tests/test_security.py`. IDs below are US-32-specific
subcases; they do not redefine the Test Plan's existing TC-SEC-001/002 scenarios.

| ID | Test method | Observed behavior |
| --- | --- | --- |
| TC-US32-001 | `test_signing_key_is_required_in_both_modes` | Missing/blank signing key fails startup in both modes |
| TC-US32-002 | `test_environment_key_signs_jwt` | JWT signing uses the injected key |
| TC-US32-003 | `test_production_defaults_require_https_and_no_cross_origin_trust` | HTTPS/Secure settings enabled; no default cross-origin trust |
| TC-US32-004 | `test_development_retains_http_and_local_vite_origins` | Existing local HTTP/Vite workflow retained |
| TC-US32-005 | `test_cors_and_csrf_trust_are_configured_independently` | Separate origin lists parsed correctly |
| TC-US32-006 | `test_postgres_requires_an_environment_password` | Missing PostgreSQL password fails startup |
| TC-US32-007 | `test_postgres_uses_environment_password` | Supplied database password retained |
| TC-US32-008 | `test_allowed_cors_preflight_echoes_exact_origin` | Allowed preflight returns exact origin; no credential grant |
| TC-US32-009 | `test_untrusted_preflight_has_no_allow_origin` | Untrusted, suffix-spoofed and null origins receive no CORS grant |
| TC-US32-010 | `test_untrusted_origin_does_not_bypass_authentication` | Unauthenticated write returns 401 without CORS grant |
| TC-US32-011 | `test_session_write_without_csrf_is_forbidden` | Session write without CSRF token returns 403 |
| TC-US32-012 | `test_valid_csrf_reaches_payload_validation` | Valid CSRF reaches serializer, returning 400 for empty payload |
| TC-US32-013 | `test_cors_allowlist_does_not_grant_csrf_trust` | Allowed CORS origin with valid token still fails CSRF origin check |
| TC-US32-014 | `test_customer_cannot_read_or_modify_another_vehicle` | Foreign vehicle read/update denied; state preserved |
| TC-US32-015 | `test_sql_payload_cannot_broaden_vehicle_search` | SQL-like plate rejected without extra records |
| TC-US32-016 | `test_production_redirect_and_secure_session_cookie` | HTTP redirects to HTTPS; HTTPS response sets Secure session/CSRF cookies |

## Remaining acceptance

US-32 stays open. The complete endpoint/role matrix requires US-02 #22 and account
administration #23; future vehicle validation requires US-08 #28. Audit
non-repudiation and privileged event coverage require US-29 #49 and event producers.
Actual TLS/proxy behavior, browser XSS verification, dependency advisory scanning,
and full-history secret review are not established by these checks. Test Plan
TC-SEC-002 audit-data inspection cannot be signed off before the audit module exists.
