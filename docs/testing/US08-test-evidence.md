# US-08 — Test Evidence

- **Story:** [US-08 (#28)](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/28)
- **Requirements:** FR-13 / FR-14
- **Design:** [US-08 validation contract](../design/US08-vehicle-validation.md)

## Verification scope

| Test ID | Automated coverage | Source |
| --- | --- | --- |
| TC-UC02-UNIT-001 | Canonical plate normalization; supported state/BH shapes; malformed separators and punctuation; database unique-constraint classifier | `backend/vehicles/tests/test_vehicle_validation.py` |
| TC-UC02-API-001 | Valid registration and canonical value persistence | `backend/vehicles/tests/test_vehicle_registration.py`; `backend/vehicles/tests/test_vehicle_validation.py` |
| TC-UC02-API-002 | Duplicate normalized plate across owners returns structured 409 and no second record | `backend/vehicles/tests/test_vehicle_validation.py` |
| TC-UC02-API-003 | Missing, blank, overlong, malformed and non-string plate values return field-specific 400 | `backend/vehicles/tests/test_vehicle_validation.py` |
| TC-UC02-API-004 | Alias consistency, unknown keys, type validation, owner-field limits, and server-managed ownership protection | `backend/vehicles/tests/test_vehicle_validation.py`; existing registration tests |
| TC-UC02-API-005 | Malformed/duplicate profile updates return 400/409 and leave the stored record unchanged | `backend/vehicles/tests/test_vehicle_validation.py` |
| TC-UC02-API-006 | PostgreSQL concurrent duplicate registration returns exactly one 201 and one 409 | PostgreSQL-only `VehicleConcurrentRegistrationTests` |
| TC-UC02-UI-001 | Frontend normalization, accepted format examples, invalid format rejection, and non-string rejection | `frontend/tests/vehicles.test.js` |
| TC-UC02-SYS-001/002 | Manual end-to-end registration, duplicate feedback and profile-update scenarios | Not Run; execute on stable integrated build |
| TC-UC10-API-001 | Shared error envelope, field details, and stable status/code mapping | `backend/common/tests/test_exceptions.py`; US-31 evidence |

## Document cross-check

- SRS source: `scripts/generate_srs.js` FR-01, FR-13 and FR-14; the generator states that validation applies across all API endpoints and that failures use `{error, code, details}`.
- SAD: §3.4.3 vehicle management and §3.4.9 shared validation/error layer.
- RTM: FR-13/FR-14 rows now point to US-08 and US-31 with separate responsibilities.
- The checked-in SRS DOCX is a Git LFS pointer (131 bytes; referenced object size 216,166 bytes). The pointer is not the DOCX content, so binary document inspection is not claimed here.
- The 19 October audit/Phase 3 report and the 03 October Handbook/Member 1 plan are historical snapshots that list Sprint 3. The later explicit 22 October allocation places US-08 in Sprint 2, and Issue #28 now reflects that; the older uploaded documents still need a future refresh.

## Manual system scenarios (not executed)

The master test plan requires 8–10+ cases across relevant test levels and says manual Actual Result / Pass-Fail must only be filled after execution. The following system-level scenarios are therefore recorded as **Not Run**, not as passed:

- `TC-UC02-SYS-001`: Sign in as an authorized customer, register a valid plate using the UI, refresh the vehicle list, and confirm the canonical plate is displayed and retrievable.
- `TC-UC02-SYS-002`: Attempt malformed and duplicate registration from the UI, verify field/conflict feedback, verify no duplicate row appears, then attempt a profile update to a duplicate plate and verify the original value remains.

## Required assertions

- Validation failures use HTTP 400 and exactly the shared `error`, `code`, and `details` envelope.
- Duplicate normalized plates use HTTP 409 and `code: CONFLICT`.
- The database unique constraint remains authoritative under concurrent insert attempts; only its registration-number violation is mapped to 409.
- Invalid and duplicate profile updates do not mutate persisted vehicle records.
- Client-supplied ownership metadata cannot change the authenticated owner.
- Frontend validation is a usability layer; backend validation is authoritative.

## Execution status

**Awaiting CI verification.**

Tests have been added to the repository. This document will be updated with exact workflow run IDs, checked commit SHA, and job results after GitHub Actions completes. No test pass is claimed before that run is observed.
