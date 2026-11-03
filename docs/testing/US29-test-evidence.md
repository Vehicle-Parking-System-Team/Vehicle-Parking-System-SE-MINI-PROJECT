# US-29 audit log verification

Validated on 3 November 2026 against `origin/main` at `286df4a` (merged PR #89).
Uses the existing development virtual environment and temporary SQLite test databases.

| Check | Result |
| --- | --- |
| Django system check | Passed: no issues |
| Migration model/state drift (`makemigrations --check --dry-run`) | Passed: no changes detected |
| `common.tests.test_audit` | 33 tests passed |
| Full backend suite | 540 tests ran in 210.793 seconds; passed with 12 skips (including PostgreSQL-only concurrency checks) |
| `git diff --check` | Passed |
| PostgreSQL audit tests | Added to existing PostgreSQL CI job; read the PR's current checks for execution result |

## Acceptance mapping

| Requirement | Evidence |
| --- | --- |
| Authentication, permission changes and manual overrides contain actor, timestamp, IP and type | Actual login/logout, admin role/status, maintenance, waiver/payment, password, tariff and cancellation API tests |
| Admin can read chronological records with HTTP 200 | Ordering with equal timestamps, stable ID tie-break, filtering and bounded pagination tests |
| Operators/customers cannot read or modify logs | GET/POST/PATCH/PUT/DELETE all return 403, including forged role parameters/headers |
| Audit entries cannot be changed through application APIs/ORM | Admin writes return 405; save/delete/update/bulk-update/base-manager/upsert attempts rejected |
| Credentials and tokens excluded | Login and password tests inspect stored data; recorder rejects unregistered fields/events |
| Actions cannot commit without their audit entry | Injected audit failures roll back login tokens, logout revocation, user creation/role changes, password changes, slot overrides, payments, tariffs and cancellations |
| Retry behavior | Repeated payment settlement, unchanged roles/status and tariffs do not duplicate audit events |

Commands run from `backend/` with a process-local development signing key:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test common.tests.test_audit --verbosity 1
python manage.py test --verbosity 1
```

The full suite included the initial 27 audit tests. Six further audit cases were
added while it ran; the subsequent targeted run passed all 33 audit cases.

The tests exercise migrations against a fresh test database. They do not apply
the migration to a developer/production database or establish production load,
a frontend audit screen, or database-owner/SQL tamper resistance. See the
[contract](../design/US29-audit-log.md) for the exact protection and retention scope.
