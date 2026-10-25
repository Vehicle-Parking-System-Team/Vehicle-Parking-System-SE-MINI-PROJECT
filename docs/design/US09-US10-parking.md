# US-09 / US-10 implementation on PR #64

This implementation extends `parking_slots` from PR #64 at
`8374e7b5b293c4de4de323a10d86fc4bd17cb9ca`. It uses the existing models,
database tables, zone foreign key, per-zone slot-number constraint and URLs.
There is no second `slots` app. Existing JWT authentication, active-account
rules, vehicle classifications and US-31 error contract are reused.

## Requirements and compatibility

- FR-03 / US-09: Admin and Operator slot/zone CRUD, initial Available status,
  and soft deactivation. Occupied/reserved bays reject specification changes
  and deactivation with HTTP 409, including PUT, PATCH, DELETE and zone deactivation.
- FR-04 / US-10: Available -> Occupied and Occupied -> Available service hooks;
  Maintenance/Reserved/inactive bays cannot be occupied through these hooks.
- SAD sections 3.4.4, 3.4.5 and DEC-02/03: services own state transitions,
  transactions roll back together, records are retained.
- The SAD's planned `backend/slots` path and uppercase state illustrations map
  to PR #64's implemented `backend/parking_slots` and lowercase stored values.
  Renaming the live app/tables or rewriting stored values is unnecessary.
- Migration `0002_parkingslot_floor` adds a nullable integer only. `0001_initial`
  is unchanged. Old floors remain NULL and appear as "Unmapped floor"; an
  operator supplies the actual floor later. New bays require an integer floor.
- Old `vehicle_type` strings, including `any` and unknown classifications,
  remain readable and may be retained during unrelated edits. New classifications
  use `vehicles.models.Vehicle.VEHICLE_TYPE_CHOICES`. No blanket data conversion.
- Slot numbers remain unique within a zone, with PR #64's 30-character limit;
  zones keep their existing 100-character limit. IDs and timestamps survive migration.

## Existing API routes

All management routes require an active Admin or Operator account. Customer
availability/dashboard access belongs to US-11, outside this implementation.

| Method | Route | Behavior |
| --- | --- | --- |
| GET / POST | `/api/parking/zones/` | List / create zones |
| GET / PUT / PATCH / DELETE | `/api/parking/zones/{id}/` | Modify / soft deactivate zone and unprotected bays |
| GET / POST | `/api/parking/slots/` | List / create bays; optional `zone` ID and lowercase `status` filters |
| GET / PUT / PATCH / DELETE | `/api/parking/slots/{id}/` | Modify / soft deactivate bay |
| PATCH | `/api/parking/slots/{id}/status/` | `{"status":"maintenance"}` or `{"status":"available"}` only |

Create payload: `{"slot_number":"A-01","zone":1,"floor":0,"vehicle_type":"Compact"}`.
The response also includes `id`, `zone_name`, lowercase `status`, `is_active`,
`created_at`, `updated_at`. Ordinary CRUD rejects a supplied status. The status
route only allows Available <-> Maintenance, so it cannot forge a check-in or
release an occupied bay before checkout. Django admin is read-only for these
models; use the API/UI to preserve lifecycle protections.

## US-10 integration contract for the operations owner

PR #64 has no check-in, checkout, parking-record or fee-calculation module.
These hooks are implemented and tested, but end-to-end US-10 acceptance remains
pending until the operations owner calls them. Do not add placeholder endpoints,
new record models or fee implementations to this change.

Import `occupy_slot` and `release_slot` from `parking_slots.services` into the
existing operations service when it is implemented:

```python
from django.db import transaction
from parking_slots.services import occupy_slot, release_slot

# Inside the actual check-in service, after its authorization, vehicle-type,
# reservation and active-session validation, and BEFORE writing its active record:
with transaction.atomic():
    slot = occupy_slot(selected_slot_id)
    # Create the actual parking record using slot.pk in THIS transaction.
    # Any failure must propagate out of this block to roll back both writes.

# Inside the actual checkout service:
with transaction.atomic():
    # Lock/load the actual active parking record and calculate/persist its fee.
    # Mark that record completed using the existing checkout implementation.
    slot = release_slot(record_slot_id)
    # Commit the record, fee and slot change together.
```

The comments identify integration positions, not ready-to-run operations code.
Both hooks raise `TransactionManagementError` without a caller-owned transaction.
Do not catch a business failure inside the outer atomic block and then commit
partial work. Existing US-31 handling converts raised Conflict to HTTP 409.

All slot mutations lock the zone before the slot, then conditionally update
the expected state. Zone deactivation uses the same lock order. If operations
also lock records/vehicles, use a consistent lock order across their entry and
exit paths; do not pre-lock a slot and then acquire its zone in reverse order.
SQLite tests establish conditional transitions and rollback, not PostgreSQL
parallel-load acceptance. The operations integration must test real concurrent
check-ins on the deployment database and enforce single active sessions.

## Frontend

The light neutral theme covers login, navigation, account, vehicles and facility
views. `ParkingScene.jsx` lazily loads Three.js and builds procedural cars and
decks. It renders on interaction rather than continuously, disposes resources,
and falls back to keyboard-accessible 2D/register views when WebGL is unavailable.
The map is a deterministic schematic, not a surveyed physical floor plan or
vehicle tracking system. Cars indicate an occupied state only.

The default view reads real API data. The separate, labeled design demo has 72
local sample bays, is read-only, and never seeds or writes to the database.
Refresh fetches a current snapshot; this is not the US-11 real-time dashboard.
The zone selector reuses the existing zones endpoint and permits creating a zone
before creating a bay. Existing authentication and vehicle functionality remain.

## Validation

Run `python manage.py test` from `backend`, and `npm test`, `npm run lint`,
`npm run build` from `frontend`. The migration regression upgrades seeded PR #64
0001 data and compares every original zone/slot field, including IDs, references,
statuses, legacy types and timestamps. Test databases are isolated; tests do not
alter a developer's normal database. See the handoff's validation evidence for
the separate SQLite upgrade rehearsal and browser checks.

## Current operations integration

US-17 now calls `occupy_slot` from the real check-in transaction. The US-12
follow-up adds active-record integrity guards and PostgreSQL concurrency tests;
see [US12-slot-integrity.md](US12-slot-integrity.md). US-10's checkout-after-fee
criterion still requires the actual US-19/US-22 implementation. The historical
PR #64 hook tests above do not establish that missing integration.
