# US-08 Test Case Supplement — UC-02 Vehicle Management

This supplement extends the representative cases in the master [Software Test Plan](Vehicle_Parking_System_Test_Plan.pdf) for the US-08 portion of UC-02. It preserves the plan's stable ID convention and keeps manual outcomes unfilled until a stable integrated build is executed.

| Test ID | Level | Scenario / test data | Expected result | Automation / status |
| --- | --- | --- | --- | --- |
| TC-UC02-UNIT-001 | Unit | Normalize case/whitespace and compare hyphenated, space-separated and compact supported formats; reject malformed separators and illegal punctuation | Valid variants produce one canonical value; malformed variants fail | Automated in `test_vehicle_validation.py` |
| TC-UC02-API-001 | Integration | Register valid standard, compact and BH-series plates; use `registration_number` and legacy `plate_number` alias | HTTP 201; stored response contains canonical plate and authenticated owner | Automated in registration and validation suites |
| TC-UC02-API-002 | Integration | Register a plate whose existing record uses a different separator form (hyphenated versus compact), including a different owner's record | HTTP 409 `CONFLICT`; exactly one record remains | Automated in `test_vehicle_validation.py` |
| TC-UC02-API-003 | Integration | Submit missing, blank, overlong, malformed, illegal-character and non-string plate values | HTTP 400 `VALIDATION_ERROR`; field-specific details; no database write | Automated in `test_vehicle_validation.py` |
| TC-UC02-API-004 | Integration | Submit unknown fields, conflicting aliases, non-string owner/type fields, and client-supplied owner identifiers | Invalid schema is rejected; server-managed ownership cannot be changed | Automated in validation and existing registration suites |
| TC-UC02-API-005 | Integration | PATCH a vehicle with malformed or another vehicle's plate; PATCH with its own unchanged plate | Invalid/duplicate update returns 400/409 without mutation; retaining own plate is allowed | Automated in validation and profile suites |
| TC-UC02-API-006 | Integration / Concurrency | Synchronize two PostgreSQL requests after duplicate preflight and submit the same plate in compact versus hyphenated form | One HTTP 201, one HTTP 409, one persisted row | PostgreSQL-only automated test; pending CI result |
| TC-UC02-UI-001 | UI | Enter valid spaced/compact/BH plate and malformed punctuation in registration/edit forms | Valid input canonicalizes; invalid input is blocked with field feedback | Automated helper regression tests; UI interaction still requires manual execution |
| TC-UC02-SYS-001 | System | Sign in, register a valid vehicle in React, refresh list and inspect returned vehicle | Vehicle is visible with canonical plate and correct owner | Not Run — record actual result after integrated-build execution |
| TC-UC02-SYS-002 | System | Submit malformed/duplicate registration and duplicate profile update through React | UI displays safe error; no duplicate is created; original profile remains unchanged | Not Run — record actual result after integrated-build execution |
| TC-UC10-API-001 | Integration | Submit malformed/boundary input and inspect common API error envelope | Standard HTTP status and `{error, code, details}`; no stack trace or secret leakage | Existing shared exception tests plus vehicle endpoint regression |

## Execution record

- Automated results: pending the PR's GitHub Actions runs.
- Manual system cases: **Not Run**. Do not mark Pass or fill Actual Result until executed against the integrated application.
- Traceability: FR-01/02, FR-13/14; US-05/06/07/08 and US-31.
