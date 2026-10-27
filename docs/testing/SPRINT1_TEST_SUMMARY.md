# Sprint 1 verification summary and test plan addendum

Recorded 27 October 2026. Application baseline: `c98346e7a219114a03f84a53cb2a0d017deb3315`. This addendum accompanies the original [Software Test Plan](Vehicle_Parking_System_Test_Plan.pdf); it does not rewrite its historical execution baseline or mark all requirements accepted.

## Latest integration CI

[Main run 40451144341](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/actions/runs/40451144341) completed successfully on 27 October 2026 for this exact application commit. Logs and individual job conclusions were inspected.

| Check | Environment | Observed result |
| --- | --- | --- |
| Django system check and backend regression | GitHub Ubuntu, Python 3.13, SQLite | System check passed; 291 tests run in 89.310 s; 282 passed, nine concurrency tests skipped |
| PostgreSQL slot/operations integrity | GitHub Ubuntu, Python 3.13, PostgreSQL 18 service | 75 tests passed in 7.167 s; no skipped cases reported |
| Frontend helper tests | GitHub Ubuntu, Node 22 | 68 passed; zero failures |
| Frontend lint and production build | Same frontend CI job | Both passed |

These are historical CI observations at the named application commit, not new local executions or performance benchmarks. The documentation PR has its own independent CI result. The PostgreSQL job is targeted; it is not a full PostgreSQL application-suite run.

## Requirement and executable test mapping

| Area | Requirements and plan references | Executable evidence | Limits |
| --- | --- | --- | --- |
| Authentication | FR-15; TC-UC01-UNIT-001 / SYS-001 | `backend/accounts/tests/test_auth.py`, PRs #56/#59, latest backend CI | Does not close US-02/03/04 |
| Vehicle registration/profile/search | FR-01/02/11; TC-UC02-UNIT-001 / API-001 / API-002 | `backend/vehicles/tests/test_vehicle_registration.py`, `test_vehicle_profile.py`, `test_vehicle_search.py`; frontend vehicle tests; PRs #61/#65/#66 | CI success does not establish the 100,000-record performance target |
| Slot/zone lifecycle | FR-03/04; TC-UC03-UNIT-001 / INT-001 | `backend/parking_slots/tests.py`, `test_services.py`, `test_migrations.py`; PRs #64/#72 | Existing records preserved; checkout integration is covered by US-12 evidence |
| Public availability | FR-10; TC-UC03-SYS-002 | [US-11 evidence](US11-test-evidence.md); API tests plus recorded desktop/mobile browser checks | Historical browser evidence from 25 October; no new browser run in this documentation update |
| Integrity and check-in | FR-05/06/07; TC-UC05-UNIT-001 / INT-001 / INT-002, TC-UC03-SYS-002 | `backend/operations/tests.py`, `backend/parking_slots/test_integrity.py`; [US-12 evidence](US12-test-evidence.md) | Tested races do not prove 50-request load or the planned compatibility hierarchy |
| Shared validation/errors | FR-13/14; TC-UC10-API-001 and expanded API/INT/UNIT IDs | [US-31 evidence](US31-test-evidence.md), `backend/common/tests/test_exceptions.py`, `frontend/tests/apiErrors.test.js` | Shared contract tests do not verify every future domain endpoint |
| Checkout/history already on current main | FR-08/09/12; TC-UC06-INT-001 / INT-002 / SYS-001 | `backend/operations/test_checkout.py`, `test_history.py`; PRs #72/#74/#75 | API coverage; no checkout/history page; outside current Sprint 1 allocation |
| Rate configuration and ordinary checkout fee | FR-23, partial FR-24 | `backend/rates/tests.py`, `backend/operations/test_checkout.py`; PRs #63/#72 | No penalty application, invoice, payment recording or receipt acceptance |

Original test-plan IDs describe coverage areas; these mappings do not imply every original manual procedure has been executed. The named test files and story evidence identify the actual checks.

## Reproduction

From `backend/` after installing `requirements.txt`:

```sh
python manage.py check
python manage.py test --verbosity 2
```

For isolated PostgreSQL verification, install `requirements-postgres.txt`, configure `DB_ENGINE=django.db.backends.postgresql` plus `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, and run:

```sh
python manage.py test parking_slots.test_integrity parking_slots.test_services operations.test_checkout operations.tests --verbosity 2
```

Use a dedicated test database account with database-creation permission. From `frontend/`: `npm ci`, `npm test`, `npm run lint`, `npm run build`.

## Unverified acceptance

No production deployment, merchant payment flow, hardware scan, 50-request load, p95 API benchmark or 100,000-record search/history benchmark is established here. Reservation, audit, notification, administrative analytics and full-system security acceptance remain open. See [the consistency report](../validation/SPRINT1_DOCUMENT_SYNC.md) for code/specification mismatches that must not be hidden by a passing status.
