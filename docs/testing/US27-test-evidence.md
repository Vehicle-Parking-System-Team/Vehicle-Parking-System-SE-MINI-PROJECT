# US-27 revenue report execution evidence

Executed on 3 November 2026. Issue: [#47](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/47).
Contract: [collected revenue API](../design/US27-revenue-reports.md).
Implementation commit: `77d5b79`; main base: `286df4a`; US-29 comparison head:
`a5b0f89` ([PR #90](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/pull/90)).

## Executed checks

Environment: Windows, Python 3.12.12, Django 5.2.18, PostgreSQL 18,
psycopg 3.3.6. Every Django process used a generated signing key.

| Check | Observed result |
| --- | --- |
| `python manage.py check` | Pass, no issues, standalone and combined with US-29 |
| `python manage.py makemigrations --check --dry-run` | No changes detected, standalone and combined |
| `python manage.py test reports --verbosity 1`, SQLite | 44 tests passed, 0.626 seconds (22 occupancy + 22 revenue) |
| `python manage.py test --verbosity 0`, standalone SQLite | 535 tests run, 12 expected skips, no failures, 209.724 seconds |
| `python manage.py test --verbosity 0`, SQLite, combined with US-29 | 568 tests run, 12 expected skips, no failures, 206.901 seconds |
| `python manage.py test reports billing --verbosity 0`, PostgreSQL | 92 tests passed, 51.185 seconds |
| `python manage.py test reports common.tests.test_audit --verbosity 0`, PostgreSQL, combined with US-29 | 77 tests passed, 5.431 seconds |
| `python -m bandit -r backend/reports --severity-level high` | Zero findings at all severity levels, no suppressions |
| `git diff --check` | Pass |
| `git merge-tree --write-tree origin/main HEAD` | Clean merge |
| `git merge-tree --write-tree origin/codex/us-29-audit-log HEAD` and reversed arguments | Both clean; identical combined tree `d7c84a6a6e8aeee560d339c3ad97a2691cf60773` for implementation commit `77d5b79` |

The SQLite skips belong to PostgreSQL-only concurrency coverage elsewhere in
the application. Fault-injection regressions intentionally log simulated
downstream, checkout and logout failures; these are passing test scenarios.
PostgreSQL runs used fresh, isolated temporary clusters with generated
passwords and loopback ports; both servers were stopped after testing.
No existing application database was used.

## Revenue regression coverage

`backend/reports/test_revenue.py` verifies:

- Exact paid totals and reconciliation of period, payment-method and vehicle-category subtotals.
- Exclusion of pending/waived receipts, active sessions and non-INR amounts; zero-fee paid receipts.
- Settlement-date attribution, inclusive-start/exclusive-end boundaries, microseconds, UTC offsets and local dates.
- Hourly/daily buckets, partial periods, midnight splits, empty/future reports and filtered zero results.
- Intersecting filters, stable vehicle snapshots, and idempotent receipt/settlement retries without double counting.
- Exact cents when totals exceed a single receipt's maximum monetary value.
- Invalid/missing dates, unsupported filters and the inclusive 366-day range limit.
- Anonymous, customer, operator and suspended/deactivated/inactive administrator denial; real bearer-token access.
- No receipt mutations, no personal data in responses, denied writes and a single batched data query.

## Scope and merge limits

Only `backend/reports/` and US-27-specific design/evidence files change.
US-29's changed files have no overlap with this branch. Main and US-29 heads
were checked against GitHub during validation. Merge results establish
compatibility with those inspected versions; later changes require rechecking.

No new migration, dependency or deployment configuration is needed. The
implemented acceptance scope is the report API. No report UI, export, refund
workflow, production latency or load acceptance is claimed. Remote CI results
are tracked on the pull request; the local PostgreSQL checks above additionally
cover the reporting code that the existing PostgreSQL CI job does not select.
