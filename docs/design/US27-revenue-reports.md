# US-27 collected revenue reports

Current integrated delivery: [documentation index](../README.md) and [final verification](../testing/FINAL_VERIFICATION_REPORT.md). The dated scope below records this story or sprint increment.
Implements [#47](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/47).
The bill/receipt feature (US-23, #43), settlement feature (US-24, #44),
and administrator permissions (US-02, #22) are already merged into the base
`286df4a`. The endpoint has no dependency on US-29 audit logging.

## API contract

`GET /api/reports/revenue/` requires an active administrator. Anonymous requests
receive 401; operators, customers and inactive administrators receive 403.
Writes receive 405. Responses use `Cache-Control: no-store` and the shared
`{error, code, details}` error contract.

| Query | Rules |
| --- | --- |
| `start`, `end` | Required ISO 8601 timestamps; start included, end excluded; end must follow start; maximum duration 366 days |
| `interval` | `day` (default) or `hour` |
| `payment_method` | Optional `Cash`, `Card` or `UPI`; exact casing |
| `vehicle_type` | Optional `Two-Wheeler`, `Compact`, `SUV` or `EV Charging` |

Offsets are converted to Asia/Kolkata. Values without an offset, including
date-only inputs at midnight, are interpreted in Asia/Kolkata. Buckets split
at local hour/day boundaries, with partial first and last buckets clipped to
the query range. Periods with no payments return zero counts and `"0.00"`.
Malformed dates, reversed/equal ranges and unsupported filter values return
400 with `VALIDATION_ERROR`.

Example: `/api/reports/revenue/?start=2026-11-01&end=2026-11-03&payment_method=UPI`.

The response contains `timezone`, `currency`, `start`, `end`, `interval`, the
applied `filters`, and these reconciliation outputs:

- `totals`: `receipt_count` and `revenue`.
- `results`: ordered period rows with `start`, `end`, `receipt_count`, `revenue`.
- `by_payment_method`: payment method subtotals, including zero methods.
- `by_vehicle_type`: receipt vehicle-category subtotals, including zero categories.

Every monetary value is a decimal string with two fractional digits, such as
`"60.60"`. For the same filters, each breakdown's amounts and counts sum to
`totals`. The endpoint returns aggregates without plates, receipt identifiers,
user identities or ticket tokens.

## Revenue definition

Revenue means **collected INR payments**, taken from each `BillingReceipt`
whose `payment_status` is `Paid` and linked parking record is `COMPLETED`.
`payment_timestamp` determines the reporting period, even when checkout and
receipt creation occurred earlier. Sum `payment_amount`, counting each receipt
once; do not add the mirrored payment fields on `ParkingRecord`.

Pending and waived receipts, active sessions, null settlement timestamps,
payments outside the period, and currencies other than INR are excluded.
The current billing service only creates INR receipts. A zero-fee paid receipt
contributes one receipt and zero revenue. Filters intersect and all subtotals
describe the filtered population.

Vehicle categories come from immutable receipt snapshots; later vehicle
profile edits do not reclassify past receipts. Historical categories outside
the current vehicle choices are retained in unfiltered breakdowns so totals
still reconcile. No refund, reversal or partial-payment model exists in the
current settlement contract; supporting those later requires revisiting this
definition. Response metadata makes the calculation explicit through
`revenue_basis=collected_paid_receipts`, `date_basis=payment_timestamp`, and
`vehicle_basis=receipt_snapshot`.

One database query reads only the settlement timestamp, method, snapshot
category and amount, in batches of 1000. Python Decimal addition preserves
cents on SQLite as well as PostgreSQL; SQLite's floating-point SQL SUM can
lose precision for large totals. There is no per-receipt lookup or write.
Runtime scales with matching receipts; no production latency/load claim is made.

## Integration boundary

This increment adds the report API and automated regressions. It needs no new
packages, migrations or configuration. It uses the existing reports URL mount
and changes only `backend/reports/` plus US-27-specific documentation. It adds
no report screen or CSV/PDF export; export reporting is US-28 (#48).
US-29's audit event producers, models, settings, routes and documentation are
outside this diff. See [execution evidence](../testing/US27-test-evidence.md)
for tested base/head versions and combined-branch verification.
