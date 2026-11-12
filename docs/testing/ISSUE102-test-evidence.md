# Issue #102 verification — 12 November 2026

Base: `main` at `535e0a7`. Stored occupancy and existing migrations are preserved.

| Check | Observed result |
| --- | --- |
| Full standalone Django suite on SQLite | 626 tests, OK; 12 PostgreSQL-specific skips |
| Focused availability/reservation check-in tests | 31 tests, OK |
| Standalone frontend tests | 112 passed |
| Frontend lint and production build | Passed; existing unrelated lint/bundle warnings |
| Django migration drift and documentation checks | Passed |
| Combined integration frontend | 122 passed after latest teammate updates |
| Combined PostgreSQL 18 suite | 642 tests, all passed, no skips |
| Follow-up PostgreSQL integration after authentication PR update | 71 focused tests, all passed |
| Bandit high-severity scan of combined backend | No high-severity findings |

The integration rehearsal combined #102 and #103 with tariff/receipt PR #107
and reservation-integrity PR #108. The follow-up also included authentication
PR #109 and the latest #108 UI update. All branches merged without conflicts.
This checks compatibility at those observed heads, not future changes. The
standalone branch has no migration drift. In the combined rehearsal, #109
introduces an unrelated missing `accounts` manager-state migration; it remains
the responsibility of that PR.

Real Edge browser checks passed against an isolated SQLite preview:

- A confirmed future booking appears Reserved and is excluded from walk-in counts.
- Real authenticated check-in and checkout update the staff map through polling.
- Protected bays still offer future booking requests to customers.
- Reload, Back and Forward restore the active workspace and selected vehicle.
- Customer attempts to link to users, dashboard, facility or audit fall back safely.
- Desktop and mobile snapshots were inspected.
- These workflows also passed with #103 and teammate changes combined.

Backend regressions check future/current bookings, expiry and exact buffer
boundaries, cancelled/fulfilled bookings, precedence of physical states,
allocation rejection, the reservation owner's check-in exception, privacy and
one-query serialization for multiple bays/bookings. Frontend tests exercise
sequential polling, timeout, visibility, cancellation, late-response rejection,
route/ID validation and protected-space counter reconciliation.

Local tests used Django 5.2.18, Python 3.12.12 and Node 22.19.0. CI independently
exercises its configured Python/PostgreSQL environment after publication. These
results do not establish deployment or large-scale load acceptance.
