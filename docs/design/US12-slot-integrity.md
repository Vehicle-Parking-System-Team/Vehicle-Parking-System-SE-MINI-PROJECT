# US-12 slot integrity and US-10 state integration

US-12 (#32) protects active parking records even when the retained slot status
is inconsistent. It uses the existing `parking_slots` service boundary,
`operations.ParkingRecord`, shared errors and database constraints. No new
alternative parking domain or frontend routes are added. The US-10 checkout
integration adds nullable snapshots to the existing ParkingRecord.

## Integrity rules

- Slot specification changes and soft deactivation return HTTP 409 if the slot
  is Occupied/Reserved or has an ACTIVE ParkingRecord.
- Zone deactivation returns HTTP 409 if any child slot is protected by status
  or an active record. The zone and all children remain unchanged on failure.
- Maintenance transitions and operations state hooks reject a slot with an
  active record. Checkout completes its record before calling
  `release_slot`, within the same outer transaction.
- Completed records remain retained and do not prevent soft deactivation of
  an otherwise unprotected slot. No historical data is deleted by these guards.
- Incompatible manual check-in selection returns HTTP 422, including when
  compatibility changes between candidate discovery and the locked recheck.
  The US-31 response remains `{error, code, details}`, with `VALIDATION_ERROR`
  and a `slot_id` field message. Other malformed inputs remain HTTP 400.

Allocation retains the existing check-in policy: matching class or legacy
`any`. The broader SAD DEC-14 size hierarchy is not introduced by this PR.

## Transactions and locks

Operations owns the check-in transaction. It locks the vehicle, then calls
`occupy_slot`, which locks the zone before the slot. Slot/zone management and
maintenance use the same zone-before-slot order. Active-record checks execute
while those locks are held. Every normal check-in creates its ParkingRecord
before committing and releasing the slot/zone locks, so a competing mutation
must observe either the committed record/state or the rolled-back original.

Conditional slot-state updates and the existing unique active-record
constraints remain in place. Direct database writes that bypass these services
are not made safe by this change. Inconsistent historical data is protected,
not automatically repaired.

## US-10 acceptance boundary

| Acceptance criterion | Current integration |
| --- | --- |
| Available → Occupied on check-in | Real US-17 service integration and rollback tests |
| Maintenance rejects allocation | Real check-in API regression tests |
| Occupied → Available after checkout and fee processing | Real checkout endpoint calculates/saves the fee and completes/releases atomically |

The [checkout contract](US10-checkout-contract.md) defines the minimal backend
integration needed for the third criterion, using the existing configured
tariff. It records a fee and does not claim payment settlement, bill/receipt
generation, a checkout UI, or closure of other user stories.

## Verification

See `parking_slots.test_integrity` for stale-state protection and real concurrent
manual allocation, check-in/deactivation, check-in/maintenance and check-in/zone
deactivation tests. PostgreSQL tests require the actual database lock features;
SQLite skips those cases rather than claiming equivalent concurrency evidence.

Install `backend/requirements-postgres.txt` for the PostgreSQL driver and set
`DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` and `DB_PORT` for an
isolated test database. The configured test user needs permission to create
Django's temporary test database. Never point acceptance fixtures at a shared
application database. CI's PostgreSQL job uses disposable test-only credentials.

The migration preservation test restores all migration leaf nodes after its
historical-data checks. This preserves its original row/field assertions and
ensures dependent operations tables exist for subsequent tests.


## Reconciled US-19 checkout

The merged US-19 endpoint and PR's fee integration use one
`operations.services.check_out_vehicle` implementation and one `check-out/`
route. The base record serializer owns integer `duration_seconds` (NULL for
active sessions); the checkout serializer adds fee/snapshot fields without
changing that type. Tariffs are read once without `select_for_update`; only
vehicle/record and zone/slot state transitions require checkout locks.
