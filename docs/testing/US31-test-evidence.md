# US-31 test cases and evidence

> **Historical story evidence:** Results and limitations below describe the original story verification. For the integrated 27 October application baseline, use [the current test summary](SPRINT1_TEST_SUMMARY.md). Later module additions do not invalidate these results or retroactively expand what this execution proved.

Story: [#51](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/51). Requirements: FR-13/FR-14, UC-10. Contract: [shared API errors](../design/US31-error-contract.md).

Initially executed on 19 October 2026 for Member 4's implementation at `c2ce42f`. The backend results below include the logging review follow-up executed on the same date. Commands use the repository's virtual environment; CI records its exact checked-out revision.

## Environment and results

| Check | Environment | Observed result |
| --- | --- | --- |
| Django system check | Windows, Python 3.12.12, Django 5.2.18, DRF 3.18.3 | Pass; no issues |
| Backend suite | Same environment; temporary in-memory SQLite 3.51.1 | Pass; 22 tests, including debug-mode, diagnostic logging and transaction subcases |
| Backend compatibility suite | Python 3.12.12, Django 5.1.15, DRF 3.15.2; temporary SQLite | Pass; same 22 tests and system check |
| Frontend helper suite | Node 22.19.0, npm 10.9.3 | Pass; 12 tests |
| Frontend lint | Existing oxlint configuration | Pass |
| Frontend production build | Vite 8.3.1 | Pass |
| Backend-to-helper handoff | Six actual DRF JSON responses consumed by `parseApiError` | Pass; field, nested row, form, auth, conflict and internal errors |

The handoff check used the test-only views under `override_settings`, then parsed their actual serialized bodies with the JavaScript helper. It is a local contract integration check, not a browser or full parking-system acceptance test.

## Automated case inventory

All rows below passed in the local execution. Backend methods are in `backend/common/tests/test_exceptions.py`; frontend cases are in `frontend/tests/apiErrors.test.js`.

| Stable test ID | Level | Backend method / expected behavior |
| --- | --- | --- |
| TC-UC10-API-001 | API integration | `test_missing_fields`: 400; field details |
| TC-UC10-API-002 | API integration | `test_invalid_type`: 400; invalid field identified |
| TC-UC10-API-003 | API integration | `test_boundary_violations`: length and both numeric limits rejected |
| TC-UC10-API-004 | API integration | `test_non_field_validation`: general validation retained |
| TC-UC10-API-005 | API integration | `test_list_validation`: root message list retained |
| TC-UC10-API-006 | API integration | `test_nested_list_validation`: row and field details retained |
| TC-UC10-API-007 | API integration | `test_malformed_json_is_safe`: 400; parser internals masked |
| TC-UC10-API-008 | API integration | `test_unauthenticated_preserves_challenge`: 401 and Bearer challenge |
| TC-UC10-API-009 | API integration | `test_invalid_credentials_are_safe`: safe authentication failure |
| TC-UC10-API-010 | API integration | `test_no_challenge_preserves_drf_403`: existing DRF status retained |
| TC-UC10-API-011 | API integration | `test_permission_denied_is_safe`: 403; policy internals masked |
| TC-UC10-API-012 | API integration | `test_missing_resource_is_safe`: 404; lookup internals masked |
| TC-UC10-API-013 | API integration | `test_conflict_has_public_message`: 409; safe domain explanation |
| TC-UC10-API-014 | API integration | `test_default_conflict`: default 409 contract |
| TC-UC10-API-015 | API integration | `test_method_not_allowed_preserves_allow_header`: 405 and Allow |
| TC-UC10-API-016 | API integration | `test_unsupported_media_type`: 415 contract |
| TC-UC10-API-017 | API integration | `test_unacceptable_response_format`: 406 contract |
| TC-UC10-API-018 | API integration | `test_throttle_preserves_retry_after`: 429 and retry interval |
| TC-UC10-API-019 | API/security | `test_unexpected_failures_are_safe_in_both_debug_modes`: runtime/database/API failures masked and safely logged |
| TC-UC10-API-020 | API regression | `test_success_and_valid_boundaries_are_unchanged`: original 201 payload |
| TC-UC10-API-021 | API/security | `test_chained_traceback_excludes_sensitive_context`: view, stack locations and chain types logged; exception/local/query/header secrets excluded from response and raw log record |
| TC-UC10-INT-001 | Database integration | `test_failed_requests_roll_back_writes`: no persisted user after validation/conflict/unexpected failure under ATOMIC_REQUESTS |

| Stable test ID | Level | Frontend case / expected behavior |
| --- | --- | --- |
| TC-UC10-UNIT-001 | Unit | Field messages preserved |
| TC-UC10-UNIT-002 | Unit | Non-field errors displayed at form level |
| TC-UC10-UNIT-003 | Unit | Root list errors displayed at form level |
| TC-UC10-UNIT-004 | Unit | Nested fields use dotted paths |
| TC-UC10-UNIT-005 | Unit | List serializer row indices retained |
| TC-UC10-UNIT-006 | Unit | Index-keyed serializer row indices retained |
| TC-UC10-UNIT-007 | Unit | General error code/message retained |
| TC-UC10-UNIT-008 | Unit | Empty/network/HTML errors use safe fallback |
| TC-UC10-UNIT-009 | Unit | Invalid/obsolete envelopes use safe fallback |
| TC-UC10-UNIT-010 | Unit | Non-message values ignored |
| TC-UC10-UNIT-011 | Unit | Input payload remains unchanged |
| TC-UC10-UNIT-012 | Unit | Field names cannot change object prototypes |

## Reproduce

From `backend/`, after installing `requirements.txt`:

```sh
python manage.py check
python manage.py test --verbosity 2
```

From `frontend/`:

```sh
npm ci
npm test
npm run lint
npm run build
```

The suite creates and destroys its own test database. Its synthetic user and routes are test-managed; no fixtures, local database, logs or exported response bodies are committed.

## Acceptance boundaries

The shared handler, helper and documented contract are implemented. Real module endpoint adoption, JWT behavior, role permissions, parking-state concurrency and actual form rendering belong to their owning stories and remain unverified here because those modules/pages do not yet exist. PostgreSQL-specific transaction/concurrency acceptance is not established by SQLite tests. Review, merge and integrated sprint acceptance are separate from these local test results. The existing SRS/SAD/Test Plan documents are preserved; this evidence adds FR-13/FR-14 coverage without changing their broader requirement mappings.
