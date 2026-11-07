# Vehicle Parking System

A React and Django parking application with PostgreSQL transaction integrity, vehicle management, live availability, reservations, entry/exit APIs, receipts and settlement, administrative reports, audit events and in-app notifications.

## Documentation
The [documentation index](docs/README.md) links the version 2.0 SRS, architecture/design specification and Test Plan in editable Markdown/Word and PDF formats. It also links the [traceability matrix](docs/requirements/traceability_matrix.md), [test catalogue](docs/testing/TEST_CASES.md), [final verification report](docs/testing/FINAL_VERIFICATION_REPORT.md), [delivery register](docs/meeting-notes/DELIVERY_REGISTER.md) and editable UML sources.

## Verified delivery
The final local PostgreSQL run passes 611 backend tests, 94 frontend helper tests, lint, build, system checks and the high-severity source scan. The documented benchmark verifies CRUD p95 below 500 ms, search/history p95 below 200 ms over 100000 records, and 50-request allocation/checkout consistency. See the report for the workload, environment and raw samples.

The linked [Agile board](https://github.com/orgs/Vehicle-Parking-System-Team/projects/1) records 32 completed stories and 116 story points. Issue milestones and iterations share the delivery-register allocation.

## Run locally
Use Python 3.12+ and Node.js 22. Create a virtual environment and install backend/requirements-postgres.txt for PostgreSQL or backend/requirements.txt for SQLite development. Generate a local signing key and set DJANGO_SECRET_KEY in your environment or an ignored .env file. Set DB_ENGINE and the DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT variables for PostgreSQL; leaving DB_ENGINE unset selects the local SQLite fallback.

From backend run python manage.py migrate then python manage.py runserver 127.0.0.1:8000. From frontend run npm ci then npm run dev. Open the URL printed by Vite, normally http://localhost:5173. The development proxy forwards relative /api requests to Django.

Register a Customer through the sign-in screen. For local role demonstrations run python manage.py seed_demo_users --help and choose the development accounts explicitly. [Security setup](docs/design/US32-security.md) describes environment and origin controls.

## Application interfaces
The React workspace provides account/profile, vehicle registration/search, facility management, public availability, administrative dashboard/export and notification views. Reservations, parking entry/exit, history, tariffs and billing are also exposed through documented REST APIs. The [SAD](docs/SAD/Vehicle_Parking_System_SAD.md) is the canonical endpoint register.

## Development checks
From backend: python manage.py check and python manage.py test --verbosity 2. From frontend: npm test, npm run lint and npm run build. GitHub Actions independently runs regression, PostgreSQL integrity, frontend and source/secret checks for pushes to main and pull requests targeting main.

For reproducible performance verification configure a PostgreSQL test account and run python scripts/verify_acceptance.py --output docs/testing/reports/performance.json. See [the document build instructions](docs/README.md) for Word/PDF and diagram generation.
