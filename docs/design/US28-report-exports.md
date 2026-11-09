# US-28 report exports (#48)

Current integrated delivery: [documentation index](../README.md) and [final verification](../testing/FINAL_VERIFICATION_REPORT.md). The dated scope below records this story or sprint increment.
Active administrators can download reports from **Admin dashboard → Export
reports**, or `GET /api/reports/export/`. Both CSV and PDF require the same
authentication and Admin permission as the report APIs. Responses are private,
non-cacheable attachments; validation uses the shared error envelope.

Required: `start`, `end`. Dates use Asia/Kolkata when no offset is supplied;
the start is inclusive and the end exclusive, with at most 366 days per request.
`report=logs|occupancy|revenue` defaults to logs.
`export_format=csv|pdf` defaults to CSV (use `export_format`, not DRF's `format`).

| Report | Filters | Data and date basis |
| --- | --- | --- |
| logs | `zone`, `status=ACTIVE|COMPLETED`, `vehicle_type` | Parking records by check-in time; recorded plate/slot/zone snapshots, falling back to current values for legacy rows |
| occupancy | `zone`, `interval=hour|day` | Same rows/calculations as US-26, including current inventory/zone and captured-time clipping |
| revenue | `payment_method=Cash|Card|UPI`, `vehicle_type`, `interval=hour|day` | Same INR paid-receipt totals by payment time as US-27 |

Unsupported filters are rejected rather than silently producing a broader export.
Occupancy/revenue export their periodic result rows, not dashboard estimates or
breakdown tables. Logs include the session's payment status and assessed fee;
collected revenue comes from settled receipt snapshots, not those log fields.

CSV starts with a UTF-8 BOM and column header, including for empty results.
The CSV writer handles delimiters/newlines; cells that could be spreadsheet
formulas are prefixed with an apostrophe. Log exports use a single joined query
and an iterator with 1,000-row batches, without a full result list or count query.
Use WSGI for synchronous CSV streaming; an ASGI deployment needs a matching
asynchronous iterator to avoid Django adapting/buffering the stream.

PDF uses landscape A4, wrapped cells, repeated columns and page numbers. It is
generated before download, spools beyond 1 MiB to a temporary file, and rejects
more than 10,000 result rows with HTTP 400 instead of truncating. Large exports
should use CSV. ReportLab generation is serialized per process for font safety.

Regression coverage: `python manage.py test reports.test_exports` checks Admin
access, filters and boundaries, snapshots, formula escaping, empty data,
aggregate parity, PDF signatures/limits, lazy CSV evaluation and constant query
count across 2,001 records. Full report and frontend checks also apply. This is
not evidence of the shared-load NFR-PERF-01 p95 target.

Local verification (2026-11-04): full SQLite suite 597 tests (12 backend-specific
skips), followed by all 68 report tests on PostgreSQL after final changes;
94 frontend helper tests, lint and production build passed (existing warnings
in Users/Profile and the Three.js chunk). An authenticated browser CSV download
returned HTTP 200; a 12-page long-cell PDF was rendered and inspected. A local
100,000-record SQLite CSV run produced 8,488,895 data bytes in 2.443 s, first
header in 0.310 s, without allocation tracing. A separate traced run peaked at
5.77 MiB and took 8.157 s. These are single-process observations, not a load or
p95 guarantee; ignored fixtures and generated outputs are not committed.
