# Vehicle Parking System

A comprehensive software engineering solution for automated vehicle parking management, slot allocation, and monitoring.

## Technology Stack

- **Backend**: Python, Django, Django REST Framework
- **Frontend**: React (Vite)
- **Database**: PostgreSQL
- **Infrastructure & CI/CD**: Docker, Jenkins

## Project Structure

```text
.
├── backend/            # Django and Django REST Framework backend
├── frontend/           # React frontend application
├── docs/               # Project documentation and engineering artifacts
│   ├── requirements/   # Functional and non-functional requirements
│   ├── architecture/   # System architecture and diagrams
│   ├── design/         # UI/UX and software design specifications
│   ├── testing/        # Test plans, test cases, and test results
│   ├── validation/     # Verification and validation artifacts
│   └── meeting-notes/  # Agile meeting records and sprint logs
├── infra/              # Infrastructure and deployment configuration
│   ├── docker/         # Dockerfiles and compose setups
│   └── jenkins/        # CI/CD pipeline definitions
└── scripts/            # Development and deployment automation scripts
```

## Current Project Status

**Initial project setup**: Project structure, backend baseline, frontend baseline, documentation hierarchy, and environment configurations have been established. Application business modules will be introduced in subsequent agile sprints.

The shared US-31 API error handler and frontend error helper are available for domain modules to reuse. See the [error contract and usage](docs/design/US31-error-contract.md) and [test cases and execution evidence](docs/testing/US31-test-evidence.md).

## Development checks

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
