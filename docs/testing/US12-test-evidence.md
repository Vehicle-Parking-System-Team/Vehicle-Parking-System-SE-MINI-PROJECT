# US-12 integrity verification and US-10 integration limits

Requirements: FR-04, FR-07, NFR-SAFE-01; stories #30 and #32.
This evidence covers the implemented slot guards and existing check-in
integration. It does not establish full checkout/fee acceptance for US-10.

## Environment and results

Windows, Python 3.12.12, Django 5.2.18, DRF 3.18.3, PostgreSQL 18.1 and
psycopg 3.3.6. PostgreSQL ran in a separate temporary cluster on loopback
port 55432; the developer/shared application databases were not used.

| Check | Observed result |
| --- | --- |
| Full `python manage.py test --verbosity 1`, PostgreSQL | 208 passed, no skips, 92.162 s |
| Full suite, SQLite | 208 run; 202 passed, 6 row-lock concurrency tests skipped, 82.925 s |
| Targeted slot integrity/state and operations concurrency, PostgreSQL | 25 passed |
| Check-in API and active-record integrity, SQLite | 21 passed, including HTTP 422 compatibility errors |
| `python manage.py check` | No issues |
| `python manage.py makemigrations --check --dry-run` | No changes detected |

The added tests use real ParkingRecords and the real check-in service/API.
They cover destructive operations against an ACTIVE record whose slot still
says Available, zone-wide rollback, maintenance rejection, release rejection
while a record is active, duplicate allocation, retained completed history,
Maintenance allocation rejection and rollback after ticket-generation failure.

Four new PostgreSQL races start independent database connections together:

1. Two vehicles manually select the same bay: exactly one succeeds, one receives
   Conflict, one ACTIVE ParkingRecord remains and the bay is Occupied.
2. Check-in versus slot deactivation: exactly one succeeds; no inactive bay
   has a newly committed active parking record.
3. Check-in versus maintenance: exactly one succeeds; no vehicle is committed
   into a Maintenance bay.
4. Check-in versus zone deactivation: exactly one succeeds; zone/child changes
   do not partially commit if check-in wins.

The existing two operations concurrency tests also ran on PostgreSQL, rather
than being skipped as on SQLite. These checks establish the exercised races,
not a 50-request load or a production performance target.

## Reproduction

Install `python -m pip install -r requirements-postgres.txt` from `backend/`.
Configure the `DB_*` variables for an isolated PostgreSQL instance with test
database creation permission, then run:

```sh
python manage.py test --verbosity 1
python manage.py test parking_slots.test_integrity parking_slots.test_services operations.tests.CheckInConcurrencyTests --verbosity 2
```

The PostgreSQL CI job runs the second command. Existing SQLite and frontend
jobs remain. CI results must be checked on the PR separately from these local
results. There are no frontend changes in this PR.

The full regression run exposed a migration-test isolation defect: rewinding
slot migrations also un-applied dependent operations migrations. Its `finally`
block now restores the full current migration graph. All original preservation
assertions remain, and production migration files are unchanged.

## Remaining acceptance boundaries

The implemented compatibility predicate retains main's exact-class/legacy-any
rule pending the allocation-policy decision. HTTP 422 is required by US-12;
malformed request validation remains HTTP 400. The shared field-error contract
is preserved for both statuses.

US-10 Available → Occupied and Maintenance rejection are exercised through
real check-in. Its checkout-after-fee criterion remains unimplemented because
US-19/US-22 are absent on main. No mock checkout is counted as completion.
See [the contract](../design/US12-slot-integrity.md) for the service boundary.
