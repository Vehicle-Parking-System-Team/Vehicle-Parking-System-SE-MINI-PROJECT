# US-12 integrity verification and US-10 integration limits

> **Historical story evidence:** Results and limitations below describe the original story verification. For the integrated 27 October application baseline, use [the current test summary](SPRINT1_TEST_SUMMARY.md). Later module additions do not invalidate these results or retroactively expand what this execution proved.

Requirements: FR-04, FR-07, NFR-SAFE-01; stories #30 and #32.
This evidence covers slot guards and the real check-in → fee processing →
checkout → slot-release integration required by US-10. Payment/receipt
processing and unrelated story closure remain outside this PR.

## Environment and results

Windows, Python 3.12.12, Django 5.2.18, DRF 3.18.3, PostgreSQL 18.1 and
psycopg 3.3.6. PostgreSQL ran in a separate temporary cluster on loopback
port 55432; the developer/shared application databases were not used.

| Check | Observed result |
| --- | --- |
| Full `python manage.py test --verbosity 1`, PostgreSQL | 279 passed, no skips, 118.224 s |
| Full suite, SQLite | 279 run; 270 passed, 9 row-lock concurrency tests skipped, 107.503 s |
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

Two added checkout races verify single completion under duplicate checkout
and record/slot consistency when checkout competes with a new allocation.
The existing two operations concurrency tests also ran on PostgreSQL, rather
than being skipped as on SQLite. These checks establish the exercised races,
not a 50-request load or a production performance target.

## Reproduction

Install `python -m pip install -r requirements-postgres.txt` from `backend/`.
Configure the `DB_*` variables for an isolated PostgreSQL instance with test
database creation permission, then run:

```sh
python manage.py test --verbosity 1
python manage.py test parking_slots.test_integrity parking_slots.test_services operations.test_checkout operations.tests --verbosity 2
```

The PostgreSQL CI job runs the second command. Existing SQLite and frontend
jobs remain. CI results must be checked on the PR separately from these local
results. There are no frontend changes in this PR.

The full regression run exposed a migration-test isolation defect: rewinding
slot migrations also un-applied dependent operations migrations. Its `finally`
block now restores the full current migration graph. All original preservation
assertions remain, and production migration files are unchanged.

## Remaining acceptance boundaries

The compatibility predicate retains main's exact-class/legacy-any rule. HTTP 422 is required by US-12;
malformed request validation remains HTTP 400. The shared field-error contract
is preserved for both statuses.

US-10 Available → Occupied and Maintenance rejection are exercised through
real check-in. Its third criterion is exercised through the real checkout API,
fee persistence and atomic slot release. Checkout tests additionally cover:

- Inclusive grace, exact hour and microsecond boundaries, multi-day duration,
  configured grace changes, Decimal rates, negative/invalid rates and overflow.
- Admin/Operator access; anonymous, Customer and inactive-account rejection.
- Client attempts to supply price, time, state, slot or payment fields.
- Unknown/repeated checkout, future entry times and inconsistent active records.
- A real JWT login → checkout → re-entry → checkout → anonymous availability
  flow using APIClient, without bypassing authentication.
- Snapshot stability after tariff edits; the existing penalty setting is not
  automatically applied, and no Paid status is produced.
- Rollback after record-save failure, slot-release failure and inconsistent
  slot state; check-in response fields remain unchanged.
- Additive migration preservation of both ACTIVE and COMPLETED historical rows,
  with the four new snapshot fields remaining NULL for those old rows.

See [the checkout contract](../design/US10-checkout-contract.md) and
[the integrity contract](../design/US12-slot-integrity.md). These tests use
Django's APIClient and database transactions; no new frontend or deployment is
claimed. All local results above reflect the refreshed branch including US-07, US-18 and US-19.


## Integration with merged US-18

Merged main at `b1ee4e6`, retaining its duplicate-session conflict details and
re-entry coverage. The shared incompatible-assignment test now expects HTTP
422, matching US-12, in both initial selection and the locked compatibility
recheck. Duplicate active sessions still return HTTP 409 with existing-slot
metadata. The full suites above were rerun after resolving this conflict.


## Single checkout integration with merged US-19

Merged main at `5b066a4`. One `operations.services.check_out_vehicle` now
implements both US-19 behavior and US-10 fee/snapshot persistence; the duplicate
checkout module is removed. There is one checkout view, request serializer and
URL pattern. Existing US-19 assertions are retained with a valid configured
tariff fixture. The full suites above ran after reconciliation.

The operations suite additionally passed all 51 tests on PostgreSQL. Added
regressions verify that the checkout and base record serializers return integer
whole-second `duration_seconds` (NULL when active), and that one hour plus one
microsecond still bills two hours despite its displayed duration being 3600.

The tariff is fetched in one ordinary SELECT, without a row lock. A PostgreSQL
test pauses checkout after that read and completes an independent rate/grace
update before allowing checkout to continue. Checkout still persists the
originally read fee inputs and amount. This verifies both that tariff writers
are not blocked and that the saved snapshots are stable. Vehicle/record locks
and the outer transaction still protect checkout/slot-state correctness.
