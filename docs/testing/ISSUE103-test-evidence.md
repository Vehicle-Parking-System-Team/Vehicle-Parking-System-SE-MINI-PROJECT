# Issue #103 verification — 12 November 2026

Base: `main` at `535e0a7`. No migrations or production data changes.

| Check | Observed result |
| --- | --- |
| Full standalone Django suite on SQLite | 626 tests, OK; 12 PostgreSQL-specific skips |
| Focused audit browser and existing audit/immutability suite | 45 tests, OK |
| Standalone frontend tests | 109 passed |
| Frontend lint and production build | Passed; existing unrelated lint/bundle warnings |
| Documentation validation | Passed |
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

- Native pagination and combined action/actor/resource filters.
- Keyboard expansion of structured previous/new state differences.
- Invalid/reversed dates, empty results, service failure and successful retry.
- Historical text rendered as escaped text rather than executable HTML.
- Only GET requests to the audit endpoint; no mutation controls or requests.
- Operator/Customer navigation exclusion and independent API HTTP 403 denial.
- Desktop and 390-pixel mobile layout; the wide table scrolls within its region.
- The same audit workflows passed with #102 URL routing and teammate changes.

The API tests additionally cover offset-aware inclusive/exclusive time bounds,
legacy exact actor-ID filtering, snapshot searches, filtered pagination,
invalid parameter envelopes, cache headers, authorization before validation,
write-method denial and unchanged append-only safeguards.

Local tests used Django 5.2.18, Python 3.12.12 and Node 22.19.0. CI independently
exercises its configured Python/PostgreSQL environment after publication. These
results do not establish deployment or large-scale load acceptance.
