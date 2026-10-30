# US-08 — Test Evidence

- **Story:** [US-08 (#28)](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/28)
- **Requirements:** FR-13 / FR-14
- **Design:** [US-08 validation contract](../design/US08-vehicle-validation.md)

## Verification scope

| Test ID | Automated coverage | Source |
| --- | --- | --- |
| TC-UC02-US08-UNIT-001 | Canonical plate normalization; supported state/BH shapes; malformed separators and punctuation; database unique-constraint classifier | `backend/vehicles/tests/test_vehicle_validation.py` |
| TC-UC02-US08-API-001 | Missing, blank, overlong, malformed and non-string plate values return field-specific 400 | `backend/vehicles/tests/test_vehicle_validation.py` |
| TC-UC02-US08-API-002 | Duplicate normalized plate across different owners returns structured 409 and does not create a second record | `backend/vehicles/tests/test_vehicle_validation.py` |
| TC-UC02-US08-API-003 | Alias consistency, unknown keys, type validation, owner-field limits, and server-managed ownership protection | `backend/vehicles/tests/test_vehicle_validation.py`; existing registration tests |
| TC-UC02-US08-API-004 | Malformed/duplicate profile updates return 400/409 and leave the stored record unchanged | `backend/vehicles/tests/test_vehicle_validation.py` |
| TC-UC02-US08-UI-001 | Frontend normalization, accepted format examples, invalid format rejection, and non-string rejection | `frontend/tests/vehicles.test.js` |
| TC-UC10-API-001 | Shared error envelope, field details, and stable status/code mapping | `backend/common/tests/test_exceptions.py`; US-31 evidence |

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
