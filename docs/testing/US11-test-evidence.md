# US-11 verification evidence

Verified on 25 October 2026 against the implementation based on `335788c`.
Requirement: FR-10; story: #31; system reference: TC-UC03-SYS-002.

## Automated checks

Environment: Windows, Python 3.12.12, Django 5.2.18, DRF 3.18.3,
Node.js 22.19.0, SQLite temporary test database.

| Command | Observed result |
| --- | --- |
| `python manage.py test --verbosity 1` from `backend/` | 196 tests run; 194 passed, 2 PostgreSQL concurrency cases skipped |
| `python manage.py check` | No issues |
| `python manage.py makemigrations --check --dry-run` | No changes detected |
| `npm test` from `frontend/` | 58 tests passed |
| `npm run lint` | Passed |
| `npm run build` | Passed; existing lazy Three.js chunk exceeds Vite's 500 kB warning threshold |

`backend/parking_slots/test_availability.py` adds 16 tests covering:

| Cases | Verified behavior |
| --- | --- |
| Anonymous access and field allowlist | HTTP 200; public slot fields only |
| Admin, Operator, Customer | All can read availability |
| Invalid/expired credential | Public endpoint remains anonymously accessible |
| Unsupported write methods | HTTP 405 even for Admin; no rows changed |
| Inactive slots/zones | Excluded from public data |
| Mixed states | Available, Occupied, Reserved and Maintenance retained |
| Zone filter | Only matching zone rows |
| Exact type filter | All four canonical types; legacy `any` excluded from typed results |
| Combined filters | Zone/type intersection, including no matches |
| Invalid filters | HTTP 400 and US-31 error envelope |
| Empty/unknown zone | HTTP 200 with empty array |
| NULL floor | Preserved without inventing a floor |
| Real US-17 check-in | Next GET shows Occupied; plate, owner and ticket excluded |
| Cache headers | Success and validation errors both disable caching |
| Query behavior | One joined SELECT for 12 slots; no per-slot zone queries |
| Management regression | Anonymous 401 and Customer 403 on existing management reads/writes |

Five frontend helper tests cover composed filters, reconciled/empty summaries,
credential/cache/cancellation options, fresh sequential responses and safe
handling of server/malformed responses.

## Browser acceptance

Headless Chromium, desktop 1440 × 1000 and mobile 390 × 844, connected to the
real local Vite → Django API → isolated SQLite database. Fixture rows covered
two zones, ground/basement/NULL floors, all four states and canonical types.
The normal developer database was not used.

Observed checks passed:

- Open availability from the sign-in screen without credentials; confirm
  ground-floor Total 3, Available 1, Occupied 1 and Other 1.
- Inspect a bay: no create/edit/maintenance/deactivate controls.
- Select Compact: Total 2, Occupied 0. Combine with the other zone: Total 0.
- Select basement and Unmapped floor; each shows the corresponding bay.
- Change a fixture slot in the database and manually refresh; Occupied changes
  from 1 to 2. Restore its state and observe the automatic refresh returning
  Occupied to 1 about 28.5 seconds later, within the running 30-second cycle.
- Simulate HTTP 503: last successful counts remain with a stale-data warning;
  retry successfully and confirm the warning clears.
- Leave availability and advance the browser clock 31 seconds: no further
  availability requests occur.
- Sign in separately as Customer, Operator and Admin; availability is read only
  for all. Customer has no management navigation; Operator/Admin retain the
  existing management screen and Add parking bay control.
- Confirm no horizontal overflow at 390 px and no uncaught page errors.

Reviewed screenshots: [desktop](screenshots/US11-desktop.png),
[mobile](screenshots/US11-mobile.png).

## Limits and existing findings

SQLite results do not establish PostgreSQL concurrent-allocation acceptance;
those safeguards belong to US-12/operations. Browser freshness checks changed
fixture slot state directly; they do not claim checkout integration. The API
test separately exercises the real check-in service. No performance load target
or production deployment was verified.

`npm audit --json` reported one high-severity finding for the existing locked
Vite 8.3.1 development dependency, including GHSA-587h-7wmj-h5pm. Dependency
manifests/lockfile are unchanged by US-11; this finding remains unresolved and
requires a separate dependency update. CI status is recorded on the PR;
local passing checks alone are not a CI or merge claim.
