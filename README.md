# Vehicle Parking System

A comprehensive software engineering solution for automated vehicle parking management, slot allocation, and monitoring.

## Technology Stack

- **Backend**: Python, Django, Django REST Framework
- **Frontend**: React (Vite)
- **Database**: PostgreSQL
- **CI**: GitHub Actions (backend, PostgreSQL integrity, frontend); Docker/Jenkins directories are placeholders

## Project Structure

```text
.
├── backend/            # Django and Django REST Framework backend
├── frontend/           # React frontend application
├── docs/               # Project documentation and engineering artifacts
│   ├── requirements/   # Functional and non-functional requirements (SRS, RTM)
│   ├── SAD/            # Software Architecture Document (SAD)
│   ├── testing/        # Test plans, test cases, and verification specifications
│   ├── validation/     # Verification, audit, and consistency reports
│   └── meeting-notes/  # Agile meeting records and sprint logs
├── infra/              # Infrastructure and deployment configuration
│   ├── docker/         # Dockerfiles and compose setups
│   └── jenkins/        # CI/CD pipeline definitions
└── scripts/            # Development and deployment automation scripts
```

## Project Documentation & Engineering Artifacts

Authoritative specifications, architectural models, and traceability registers are maintained under [`docs/`](docs/):

- **Software Requirements Specification (SRS)**: [`docs/requirements/Vehicle_Parking_System_SRS.docx`](docs/requirements/Vehicle_Parking_System_SRS.docx) (Generated via [`scripts/generate_srs.js`](scripts/generate_srs.js); generation instructions below)
- **Requirements Traceability Matrix (RTM)**: [`docs/requirements/traceability_matrix.md`](docs/requirements/traceability_matrix.md)
- **Software Architecture Document (SAD)**: [`docs/SAD/Vehicle_Parking_System_SAD.md`](docs/SAD/Vehicle_Parking_System_SAD.md) (Authoritative architectural specification harmonized with SRS v1.2.0 and RTM v1.2.0; legacy PDF archive preserved at [`docs/SAD/Vehicle_Parking_System_SAD (2) (1) (1).pdf`](docs/SAD/Vehicle_Parking_System_SAD%20%282%29%20%281%29%20%281%29.pdf))
- **Software Test Plan**: [`docs/testing/Vehicle_Parking_System_Test_Plan.pdf`](docs/testing/Vehicle_Parking_System_Test_Plan.pdf)
- **Audit & Phase 3 Reports**: [`docs/validation/DOCUMENT_ISSUE_AUDIT.md`](docs/validation/DOCUMENT_ISSUE_AUDIT.md), [`docs/validation/PHASE3_CORRECTION_REPORT.md`](docs/validation/PHASE3_CORRECTION_REPORT.md)

## Current Project Status

**Sprint 1 delivery recorded; formal milestone reconciliation pending.** The application implements JWT authentication/logout, vehicle registration/profile/search, slot/zone management, public availability, transactional check-in, checkout with ordinary fee snapshots and slot release, completed-session history API, and rate configuration. Authentication, vehicles, facility management and public availability have frontend views; check-in, checkout, history and rates currently expose backend APIs without dedicated frontend flows.

The current main baseline also includes work outside Sprint 1. Reservations, administrative analytics, audit logs, notifications, invoices/payments and receipts remain incomplete. See the [Sprint 1 review](docs/meeting-notes/SPRINT1_REVIEW.md), [verification summary and test-plan addendum](docs/testing/SPRINT1_TEST_SUMMARY.md), [RTM](docs/requirements/traceability_matrix.md) and [known specification gaps](docs/validation/SPRINT1_DOCUMENT_SYNC.md). The original six-story commitment is closed; the milestone currently contains 10 closed and three open stories.

The shared US-31 API error handler and frontend error helper are available for domain modules to reuse. See the [error contract and usage](docs/design/US31-error-contract.md) and [test cases and execution evidence](docs/testing/US31-test-evidence.md).

## Development checks

US-11 adds public, read-only parking availability from the sign-in screen and
signed-in navigation, with zone/type filters and a 30-second refresh. See the
[availability API and behavior](docs/design/US11-parking-availability.md) and
[verification evidence](docs/testing/US11-test-evidence.md).

US-12 protects bays with active parking records and verifies allocation races
on PostgreSQL. US-10's authenticated checkout API processes the configured fee,
completes the record and releases the bay atomically. See the
[slot integrity contract](docs/design/US12-slot-integrity.md),
[checkout contract](docs/design/US10-checkout-contract.md) and
[verification evidence](docs/testing/US12-test-evidence.md).

Create and activate a Python virtual environment (Python 3.12+ locally; CI uses 3.13). From `backend/`:

```sh
python -m pip install -r requirements.txt
python manage.py check
python manage.py test --verbosity 2
```

From `frontend/` with Node.js 22:

```sh
npm ci
npm test
npm run lint
npm run build
```

Without a local `.env`, backend tests use the existing SQLite fallback and a temporary test database. PostgreSQL remains the application target; these tests do not establish PostgreSQL concurrency acceptance. No additional runtime or test dependency is required for US-31.


## Run locally

Use Python 3.12+ and Node.js 22. From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
python backend/manage.py migrate
python backend/manage.py runserver 127.0.0.1:8000
```

In another terminal, from `frontend/`:

```sh
npm ci
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`). Its `/api` proxy targets `http://127.0.0.1:8000`. Without `.env`, Django uses local SQLite and development defaults. To use PostgreSQL, set `DB_ENGINE=django.db.backends.postgresql` and the `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` settings in a local root/backend `.env`; install `backend/requirements-postgres.txt` before migrating. `DATABASE_URL` and `VITE_API_BASE_URL` from the legacy example are not consumed by the current settings/client.

Register a Customer through the UI. For local role demonstrations, inspect `python backend/manage.py seed_demo_users --help`; the command provides development accounts. Production deployment is not established by these development instructions.

## Regenerate the SRS

From `scripts/`, run `npm ci` and `node generate_srs.js`. Keep source, `assets/` diagrams and the generated `docs/requirements/Vehicle_Parking_System_SRS.docx` in the same review. Render the DOCX and review its pages before publishing. The version 1.2.0 implementation addendum records delivered behavior and outstanding gaps without declaring future requirements complete.
