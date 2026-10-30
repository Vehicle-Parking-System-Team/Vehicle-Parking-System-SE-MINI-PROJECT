# US-08 Test Case Supplement — UC-02 Vehicle Management

This supplement extends the representative cases in the master [Software Test Plan](Vehicle_Parking_System_Test_Plan.pdf). The original UC-02 identifiers remain reserved and unchanged: `TC-UC02-UNIT-001` (baseline registration validation), `TC-UC02-API-001` (valid registration), and `TC-UC02-API-002` (duplicate registration). New US-08 cases use the dedicated `TC-UC02-US08-*` namespace already established in SAD §3.4.3, avoiding collisions with the baseline and other vehicle stories.

| Test ID | Level | Scenario / test data | Expected result | Automation / status |
| --- | --- | --- | --- | --- |
| TC-UC02-US08-UNIT-001 | Unit | Normalize case/whitespace; compare hyphenated, space-separated and compact supported formats; reject malformed separators and illegal punctuation; verify legacy migration normalization and duplicate-constraint classification | Valid variants produce one canonical value; malformed variants fail; legacy formats normalize without deleting/merging records | Automated in `test_vehicle_validation.py` |
| TC-UC02-US08-API-001 | Integration | Submit missing, blank, raw-overlong (including the legacy alias), malformed, illegal-character and non-string plate values | HTTP 400 `VALIDATION_ERROR`; field-specific details; no database write | Automated in `test_vehicle_validation.py` |
| TC-UC02-US08-API-002 | Integration | Register a plate whose existing record differs by case, spaces or hyphens, including a different owner's record | HTTP 409 `CONFLICT`; exactly one record remains | Automated in `test_vehicle_validation.py` |
| TC-UC02-US08-API-003 | Integration | Submit unknown fields, mismatched aliases, matching aliases with different separators, malformed secondary aliases, non-string owner/type fields, and client-supplied owner identifiers | Mismatched aliases/invalid schema are rejected; matching aliases are accepted; server-managed ownership cannot be changed | Automated in validation and existing registration suites |
| TC-UC02-US08-API-004 | Integration | PUT/PATCH a vehicle with malformed or another vehicle's plate; PUT/PATCH with its own unchanged plate | Invalid/duplicate update returns 400/409 without mutation; retaining own plate is allowed | Automated in validation and profile suites |
| TC-UC02-US08-API-005 | Integration / Concurrency | Synchronize two PostgreSQL requests after duplicate preflight and submit the same plate in compact versus hyphenated form | One HTTP 201, one HTTP 409, one persisted row | PostgreSQL-only automated test |
| TC-UC02-US08-UI-001 | UI | Enter valid spaced/compact/BH plate, malformed punctuation, raw-overlong plate, and over-limit owner contact values in registration/edit forms | Valid input canonicalizes; invalid input is blocked with field feedback | Automated helper regression tests; UI interaction still requires manual execution |
| TC-UC02-US08-SYS-001 | System | Sign in, register a valid vehicle in React, refresh list and inspect returned vehicle | Vehicle is visible with canonical plate and correct owner | Not Run — record actual result after integrated-build execution |
| TC-UC02-US08-SYS-002 | System | Submit malformed/duplicate registration and duplicate profile update through React | UI displays safe error; no duplicate is created; original profile remains unchanged | Not Run — record actual result after integrated-build execution |
| TC-UC10-API-001 | Integration | Submit malformed/boundary input and inspect common API error envelope | Standard HTTP status and `{error, code, details}`; no stack trace or secret leakage | Existing shared exception tests plus vehicle endpoint regression |

## Execution record

- Automated results: recorded in [US-08 test evidence](US08-test-evidence.md) against the exact CI commit.
- Manual system cases: **Not Run**. Do not mark Pass or fill Actual Result until executed against the integrated application.
- Traceability: FR-01/02, FR-13/14; US-05/06/07/08 and US-31.
- Existing older US-06/US-07 artifacts reuse some baseline `TC-UC02-API-001/002` identifiers for different scenarios. That pre-existing cross-story collision is not extended by this supplement; the new US-08 namespace is unique.
