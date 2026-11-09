# Vehicle Parking System Documentation

The current engineering documents share version 2.0 and the 8 November 2026 verification baseline.

| Document | Editable source | Submission formats |
| --- | --- | --- |
| Requirements | requirements/Vehicle_Parking_System_SRS.md | Matching DOCX and PDF |
| Architecture and design | SAD/Vehicle_Parking_System_SAD.md | Matching DOCX and PDF |
| Test plan | testing/Vehicle_Parking_System_Test_Plan.md | Matching DOCX and PDF |
| Traceability | requirements/traceability_matrix.md | Markdown |
| Test catalogue and execution | testing/TEST_CASES.md; testing/FINAL_VERIFICATION_REPORT.md | Markdown and machine-readable JSON |
| Delivery and contribution record | meeting-notes/DELIVERY_REGISTER.md | Markdown |
| Design decisions | design/RELEASE_DESIGN_DECISIONS.md | Markdown |
| UML models | diagrams/*.puml | Editable PlantUML plus SVG and PNG |

## Rebuilding documents and diagrams
Install scripts/requirements-documents.txt, then run python scripts/build_documents.py. On Windows with Microsoft Word, run scripts/export_documents.ps1 to update the contents/page fields and export PDFs. LibreOffice is an alternative PDF export engine; retain the same base names. Review every rendered page before submission. scripts/generate_srs.js remains a compatibility entry point for the document build; PYTHON may select a Python executable.

Use PlantUML 1.2026.9: java -jar plantuml.jar -tsvg docs/diagrams/*.puml and repeat with -tpng. Smetana provides layout without a separate Graphviz installation. Sequence diagrams include participants, calls, return paths, transaction boundaries and alternate error paths. PlantUML source and rendered models must be reviewed together.

## Verification
Backend: run python manage.py test --verbosity 2 from backend with a PostgreSQL test account. Frontend: npm ci, npm test, npm run lint and npm run build. Performance: configure DB_* and run python scripts/verify_acceptance.py --output docs/testing/reports/performance.json from the repository root. The benchmark creates a unique temporary test database and never seeds the configured application database.

The final verification report gives measurements, hardware/runtime profile, commands and evidence scope. Older dated sprint/story reports remain historical execution records. Current status is defined by this index, the RTM and final verification, rather than those older snapshots.
