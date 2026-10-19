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

- **Software Requirements Specification (SRS)**: [`docs/requirements/Vehicle_Parking_System_SRS.docx`](docs/requirements/Vehicle_Parking_System_SRS.docx) (Generated via [`scripts/generate_srs.js`](scripts/generate_srs.js))
- **Requirements Traceability Matrix (RTM)**: [`docs/requirements/traceability_matrix.md`](docs/requirements/traceability_matrix.md)
- **Software Architecture Document (SAD)**: [`docs/SAD/Vehicle_Parking_System_SAD.md`](docs/SAD/Vehicle_Parking_System_SAD.md) (Authoritative architectural specification harmonized with SRS v1.1 and RTM v1.1; legacy PDF archive preserved at [`docs/SAD/Vehicle_Parking_System_SAD (2) (1) (1).pdf`](docs/SAD/Vehicle_Parking_System_SAD%20(2)%20(1)%20(1).pdf))
- **Software Test Plan**: [`docs/testing/Vehicle_Parking_System_Test_Plan.pdf`](docs/testing/Vehicle_Parking_System_Test_Plan.pdf)
- **Audit & Phase 3 Reports**: [`docs/validation/DOCUMENT_ISSUE_AUDIT.md`](docs/validation/DOCUMENT_ISSUE_AUDIT.md), [`docs/validation/PHASE3_CORRECTION_REPORT.md`](docs/validation/PHASE3_CORRECTION_REPORT.md)

## Current Project Status

**Baseline Ready for Development**: Repository structure, Django/DRF backend baseline (`backend/config/`), React Vite frontend baseline (`frontend/src/`), documentation hierarchy, and environment configurations have been established. All 30 Functional Requirements (`FR-01` to `FR-30`), 15 architectural/business decisions (`DEC-01` to `DEC-15`), and 32 canonical user stories across 8 epics are fully aligned across the SRS, RTM, SAD, and Test Plan. Application domain modules (`backend/<domain>/`, `frontend/src/pages/`) will be introduced in subsequent agile sprints according to the sprint backlog.
