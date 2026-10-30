# US-08 — Vehicle Validation and Duplicate Handling

- **User Story:** [US-08 (#28)](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/28)
- **Parent Epic:** E2 — Vehicle Management (#15)
- **Owner:** Member 1
- **Requirements:** FR-13 (vehicle-domain payload validation), FR-14 (shared structured errors)
- **Story points:** 4 SP
- **Related stories:** US-05 registration (#25), US-06 profile/update (#26), US-07 search (#27), US-31 shared error contract (#51)

## 1. Scope and boundary

US-08 completes the vehicle-domain portion of FR-13/FR-14. It does not create a second error-handling framework: the shared response contract remains implemented by US-31 in `backend/common/exceptions.py`. Vehicle serializers validate client payloads, vehicle services normalize and verify registration numbers, and the database unique constraint remains the final authority for duplicate prevention.

This story applies to vehicle creation and vehicle profile replacement/partial updates. Search intentionally supports partial prefixes and is not subject to full-plate validation.

## 2. Registration-number contract

### Accepted input forms

The implementation preserves the existing Indian registration formats supported by the vehicle module:

- State-series examples: `KA-01-AB-1234`, `KA01AB1234`, `DL3CBB1122`
- Existing project-compatible series examples: `KA-01-TEST-99`
- BH-series examples: `22-BH-1234-AA`, `22BH1234A`

Input is trimmed and uppercased. Space-separated groups (for example `ka 01 ab 1234`) become `KA-01-AB-1234`; spaces around valid hyphen separators are removed. Compact plates remain compact. Canonicalization does not repair illegal punctuation, tabs, mixed separators, or repeated hyphens: those values fail validation. The normalized value must be at most 20 characters and match the anchored backend format expression.

The format expression validates the documented project shape; it is not an external RTO/state-series registry lookup or a legal verification of vehicle registration.

### Payload fields

| Field | Contract |
| --- | --- |
| `registration_number` | Required on POST and PUT; optional on PATCH only when the plate is not being changed; string; normalized; max 20; supported format |
| `plate_number` | Legacy write-only alias; same validation as `registration_number`; if both are supplied they must normalize to the same value |
| `vehicle_type` | Canonical choice: `Two-Wheeler`, `Compact`, `SUV`, or `EV Charging`; required on create/full update |
| `owner_name` | Optional string, trimmed, max 100 characters |
| `owner_phone` | Optional string, trimmed, max 20 characters; no phone-number syntax is imposed because the SRS leaves owner profile field semantics unresolved (UD-15) |
| Server-managed fields | Owner, ID, username and timestamps cannot be changed by client input; authenticated identity determines ownership |

Unknown payload keys and non-string scalar values are rejected with HTTP 400. Legacy server-managed keys may be present in older clients' requests but are ignored and cannot alter ownership or record metadata. This preserves the existing ownership-spoof regression guarantee.

## 3. API behavior

| Method and endpoint | Validation behavior |
| --- | --- |
| `POST /api/v1/vehicles/` | Validates and creates a vehicle; returns 201 |
| `PUT /api/v1/vehicles/{id}/` | Requires a valid complete vehicle payload; returns 200 |
| `PATCH /api/v1/vehicles/{id}/` | Validates supplied fields; a supplied plate is fully validated; returns 200 |
| `GET /api/v1/vehicles/search/?plate=...` | Preserves partial-prefix search; missing/too-short query is a structured 400 |

### Failure contract

All handled vehicle API errors use US-31's `{error, code, details}` envelope.

- Invalid, missing, malformed, overlong, unknown, or wrong-type payload fields: **400**, `VALIDATION_ERROR`, field-specific `details`.
- Duplicate normalized registration number: **409**, `CONFLICT`, empty `details`.
- Authentication, authorization, and not-found outcomes retain their standard 401/403/404 status and shared machine-readable error codes.
- Unexpected database integrity failures are not mislabeled as duplicate registrations; they remain generic 500 `INTERNAL_ERROR` responses.

## 4. Duplicate and transaction integrity

The vehicle table already has a unique constraint on `registration_number`; no schema migration is required. The serializer performs an early duplicate lookup for a useful response. Registration and update writes remain inside `transaction.atomic()`. If concurrent requests pass the early lookup, the database unique constraint decides the winner. Only a violation of the registration-number unique constraint is translated to HTTP 409. Other integrity failures are re-raised for the shared handler.

On update, the current vehicle is excluded from the duplicate lookup so a profile can retain its own plate. A duplicate or malformed update must leave the persisted record unchanged.

## 5. Frontend behavior

The registration and edit forms use the same normalization/format policy as the backend for immediate field feedback. The server remains authoritative. Registration errors are rendered beside the registration field; duplicate conflicts and other API errors are parsed by `parseApiError` and shown in the form alert. Owner name/phone inputs reflect the persisted length limits. Search remains prefix-capable and uses only presence/length client checks.

## 6. Documentation reconciliation\n\n- The SRS generator's FR-01 acceptance criteria require HTTP 400 for missing/malformed mandatory fields and a conflict for duplicate license plates. FR-13 and FR-14 are universal requirements; this design implements only the vehicle-domain portion.\n- RTM v1.2.1 now links the vehicle serializer/service/frontend validator and the shared US-31 exception contract to FR-13/FR-14. SAD §3.4.3 and the FR-13/FR-14 traceability rows now describe the implementation boundary.\n- Historical audit snapshots dated 19 October list US-08 under Sprint 3. The explicit allocation decision recorded on 22 October placed US-08 in Sprint 2; Issue #28 was synchronized to Sprint 2 on 30 October. The older audit reports remain dated historical snapshots, not the current backlog.\n- The SRS DOCX LFS pointer could not be dereferenced through the GitHub contents interface during this review; its rendered binary must be inspected separately if an exact DOCX-content sign-off is required.\n\n## 7. Traceability and verification

| Test ID | Coverage |
| --- | --- |
| `TC-UC02-US08-UNIT-001` | Canonicalization, accepted formats, malformed formats, and duplicate-constraint classification |
| `TC-UC02-US08-API-001` | Missing, blank, malformed, overlong and wrong-type registration payloads; 400 field errors |
| `TC-UC02-US08-API-002` | Normalized duplicate registration, cross-owner collision and structured 409 |
| `TC-UC02-US08-API-003` | Unknown keys, server-managed fields, alias consistency and payload sanitization |
| `TC-UC02-US08-API-004` | Profile update validation, duplicate rejection and no-mutation guarantee |
| `TC-UC02-US08-UI-001` | Frontend normalization, format validation and invalid-input rejection |
| `TC-UC10-API-001` | Shared US-31 structured error contract |

Execution evidence and CI status are recorded in [US-08 test evidence](../testing/US08-test-evidence.md). The SRS generator source (`scripts/generate_srs.js`, v1.2.0) keeps FR-13/FR-14 system-wide and defines the vehicle registration acceptance criteria under FR-01. The checked-in SRS DOCX is Git LFS-backed: GitHub's contents API exposes a 131-byte pointer to a 216,166-byte object, not the document body. I therefore verified the SRS generator source, RTM, SAD, issue and code; I do not claim to have inspected the binary DOCX contents. The requirement wording is unchanged: US-08 implements the vehicle slice while US-31 owns the shared cross-cutting error mechanism.
