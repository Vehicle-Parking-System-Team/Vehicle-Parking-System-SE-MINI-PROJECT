# US-08 — Test Evidence

- **Story:** [US-08 (#28)](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/28)
- **Requirements:** FR-13 / FR-14
- **Design:** [US-08 validation contract](../design/US08-vehicle-validation.md)

## Verification scope

| Test ID | Automated coverage | Source |
| --- | --- | --- |
| TC-UC02-US08-UNIT-001 | Canonical plate normalization; supported state/BH shapes; malformed separators; legacy migration normalization; exact and separator-insensitive database uniqueness classification | `backend/vehicles/tests/test_vehicle_validation.py` |
| TC-UC02-US08-API-001 | Missing, blank, raw-overlong, malformed, illegal-character and non-string plate values return field-specific 400 with no database write | `backend/vehicles/tests/test_vehicle_validation.py` |
| TC-UC02-US08-API-002 | Duplicate normalized plate across owners and separator/case variants returns structured 409 with one record | `backend/vehicles/tests/test_vehicle_validation.py` |
| TC-UC02-US08-API-003 | Alias identity consistency and independent alias validation, unknown keys, non-string fields, owner-field limits, and server-managed ownership protection | `backend/vehicles/tests/test_vehicle_validation.py`; existing registration tests |
| TC-UC02-US08-API-004 | Malformed/duplicate PUT/PATCH updates return 400/409 without mutation; retaining own plate is accepted | `backend/vehicles/tests/test_vehicle_validation.py`; profile tests |
| TC-UC02-US08-API-005 | PostgreSQL concurrent duplicate registration returns exactly one 201 and one 409 | PostgreSQL-only `VehicleConcurrentRegistrationTests` |
| TC-UC02-US08-UI-001 | Frontend normalization, accepted formats, invalid/raw-overlong plate rejection, and owner contact field limits | `frontend/tests/vehicles.test.js` |
| TC-UC02-US08-SYS-001/002 | Manual end-to-end registration, duplicate feedback and profile-update scenarios | Not Run; execute on stable integrated build |
| TC-UC02-UNIT-001 / API-001 / API-002 | Original master Test Plan baseline cases retained unchanged: registration validation, valid registration, and duplicate registration | Master `Vehicle_Parking_System_Test_Plan.pdf`; existing registration tests |
| TC-UC10-API-001 | Shared error envelope, field details, and stable status/code mapping | `backend/common/tests/test_exceptions.py`; US-31 evidence |

## Document cross-check

- SRS source: `scripts/generate_srs.js` FR-01, FR-13 and FR-14. The available Library copy of SRS v1.1 (18 October 2026) was also inspected for those requirements. The repository's generated DOCX remains an LFS pointer, so it is not represented as inspected. The generator states that validation applies across all API endpoints and that failures use `{error, code, details}`.
- SAD: §3.4.3 vehicle management and §3.4.9 shared validation/error layer.
- RTM: v1.2.1 FR-13/FR-14 rows now point to US-08 and US-31 with separate responsibilities. The PR also adds the no-op `operations.0007_merge_payment_status_reservation` migration because current `main` has two independent `0006` leaves; this is an integration-graph repair, not a new business schema change. The SRS generator source now references RTM v1.2.1; regenerate the LFS-backed DOCX from the repository root with `cd scripts && npm ci && node generate_srs.js` after the updated RTM is accepted.
- The checked-in SRS DOCX is a Git LFS pointer (131 bytes; referenced object size 216,166 bytes). The pointer is not the DOCX content, so binary document inspection is not claimed here.
- The master Software Test Plan v1.0 requires 8–10+ cases for each implemented use case and says manual outcomes are recorded only after execution. UC-02 now has the three original baseline cases plus nine new US-08-specific cases; manual SYS-001/002 remain Not Run.
- The 19 October audit/Phase 3 report and the 03 October Handbook/Member 1 plan are historical snapshots that list Sprint 3. The later explicit 22 October allocation places US-08 in Sprint 2, and Issue #28 now reflects that; the older uploaded documents still need a future refresh.

## Manual system scenarios (not executed)

The master test plan requires 8–10+ cases across relevant test levels and says manual Actual Result / Pass-Fail must only be filled after execution. The following system-level scenarios are therefore recorded as **Not Run**, not as passed:

- `TC-UC02-US08-SYS-001`: Sign in as an authorized customer, register a valid plate using the UI, refresh the vehicle list, and confirm the canonical plate is displayed and retrievable.
- `TC-UC02-US08-SYS-002`: Attempt malformed and duplicate registration from the UI, verify field/conflict feedback, verify no duplicate row appears, then attempt a profile update to a duplicate plate and verify the original value remains.

## Required assertions

- Validation failures use HTTP 400 and exactly the shared `error`, `code`, and `details` envelope.
- Duplicate normalized plates use HTTP 409 and `code: CONFLICT`.
- The database separator-insensitive expression unique index from migration `0002_vehicle_registration_compact_uniq.py` remains authoritative under concurrent insert attempts; only its registration-number violation is mapped to 409.
- Invalid and duplicate profile updates do not mutate persisted vehicle records.
- Client-supplied ownership metadata cannot change the authenticated owner.
- Frontend validation is a usability layer; backend validation is authoritative.

## Execution status

**CI run 41107424010 — commit `6f78470dd76766f1cc42ec14eaf89ca5ca0360e7`.**

- Frontend CI: passed.
- PostgreSQL slot and vehicle integrity: passed.
- Security verification run 41107424077: passed.
- Backend Django CI: still running when this evidence snapshot was recorded.

The backend result must be checked before declaring CI fully green. Manual SYS-001/002 remain Not Run and require execution against the integrated application.
