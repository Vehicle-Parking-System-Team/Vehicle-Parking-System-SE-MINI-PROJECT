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

- SRS: source and regenerated v1.2.1 DOCX were inspected for FR-01, FR-02, FR-11, FR-13 and FR-14. The baseline wording remains unchanged; the implementation addendum records the US-08 validation scope, current automated results, and remaining manual/PostgreSQL checks. The DOCX generator takes the canonical RTM as input.
- SAD: §3.4.3 vehicle management and §3.4.9 shared validation/error layer.
- RTM: v1.2.1 FR-13/FR-14 rows link US-08 vehicle validation and US-31 shared errors separately and record the local suite result and manual-test limitation. The two operations `0006` migrations are explicitly ordered and `0007_merge_payment_status_reservation` joins their history without a schema operation.
- The generated SRS is Git LFS-backed; the updated document was generated from `scripts/generate_srs.js` and the canonical RTM, then its requirement text was extracted for consistency checks.
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

## Historical migration regression

The latest confirmed failing workflow before this correction was Actions run `41112613634` (PR head `d9c6e99`). Its backend job ran 504 tests and reported exactly two errors:

- `CheckoutMigrationTests.test_existing_active_and_completed_records_survive_nullable_snapshot_migration`
- `ExistingDataMigrationTests.test_pr64_rows_survive_additive_floor_migration`

Both failed while `MigrationExecutor` reversed migrations on SQLite with `OperationalError: no such column: ""payment_timestamp""`. The rollback reached a `RemoveField` table rebuild that referenced `payment_timestamp` after an unordered sibling migration had removed that column. The cause was migration graph ordering, not a stale model definition. The correction serializes the reservation and payment migrations and retains the original reservation migration and payment/reservation fields.

## Local verification on the integrated PR candidate

The integrated tree was tested against the fetched `origin/main` base with the PR changes and migration correction:

| Verification | Result |
| --- | --- |
| Checkout snapshot migration rollback test | Passed |
| Parking-slot additive floor migration rollback test | Passed |
| Complete backend suite | Passed: 504 tests, 12 skipped, 0 failures |
| Fresh test-database migration from zero | Passed as part of the Django test database setup |
| `manage.py check` | Passed: no issues |
| `makemigrations --check --dry-run` | Passed: no changes detected |
| Frontend tests | Passed: 94/94 |
| Frontend lint | Passed with warnings in untouched `src/pages/Users.jsx` and `src/pages/Profile.jsx` |
| Frontend production build | Passed; Vite reported a chunk-size advisory |

The local backend used SQLite. This machine has no Docker executable, PostgreSQL service, or listener on port 5432, so the PostgreSQL-only concurrent registration test was skipped locally. The earlier workflow's PostgreSQL job passed on an older PR revision; it is not claimed as verification of this correction. Check the revision-specific PostgreSQL result in the current PR Actions rather than treating the local skip or older run as a pass.

Manual system cases `TC-UC02-US08-SYS-001/002` remain **Not Run** and require execution against the integrated application. Frontend interaction testing was not performed in a browser; automated frontend tests exercise the shared validation helpers and API error handling.
