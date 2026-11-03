# US-25 — Admin dashboard metrics

Story #45, Epic #20, Member 4, Sprint 2 (5 SP). Handbook FR-27 maps to
dashboard metrics; the issue also preserves SRS v1.1 FR-29 for daily revenue
and occupancy. The current RTM tracks this story under FR-27.

## API and access

`GET /api/reports/dashboard/` returns HTTP 200 for active administrators.
It reuses `accounts.permissions.IsAdmin`, JWT authentication, and the US-31
error envelope. Anonymous requests receive 401, authenticated non-admins
receive 403, and write methods receive 405. Responses prohibit caching.
There are no filters, migrations, new dependencies, or writes to domain data.

## Calculations and scope

| Field | Definition |
| --- | --- |
| `as_of`, `timezone` | One captured instant in Asia/Kolkata |
| `total_slots` | Active slots belonging to active zones, including reserved/maintenance |
| `free_slots` | Available slots in that inventory without an active parking record |
| `active_sessions` | All records with status ACTIVE, including records on disabled inventory |
| `slot_distribution` | Available, occupied, reserved and maintenance counts in active inventory |
| `occupancy_percent` | Occupied slots / total active slots × 100, rounded to two decimals; zero for no capacity |
| `zones` | The same distribution per zone, sorted by name/id; zones without active slots are omitted |
| `today_revenue` | Decimal INR string from US-27's collected paid receipts, completed sessions only |
| `revenue_start`, `revenue_end` | Local midnight inclusive, captured instant exclusive; payment time controls inclusion |
| `activity` | 24 local hourly rows with arrivals, departures and exact revenue strings; future hours have zero values |
| `arrivals_today`, `departures_today` | Counts of check-in/checkout timestamps in today's observed window across all inventory |
| `average_stay_minutes` | Average elapsed stay for valid, nonnegative sessions completed today; null when none exist |

An active parking record takes precedence over a conflicting slot status in
the distribution. The endpoint does not repair data. Historical activity and
open-session counts include disabled inventory, so they need not equal the
active-capacity counters. Slot turnover on the page is today's arrivals divided
by current active slot inventory; zero inventory displays an unavailable label.

The date interval is `[local midnight, as_of)`, with partial current-hour data.
Revenue reuses `revenue_report` rather than introducing another payment rule.
It sums Decimal receipt amounts in bounded batches, preserving cents on both
SQLite and PostgreSQL. There are seven data queries independent of zone/slot
count: slot distribution, revenue, arrivals, departures, average duration,
recent flow, and active-session count. Authentication adds its existing reads.
Queries read current committed data; `as_of` is a time-window cutoff, not a
database-wide atomic snapshot under concurrent transactions.

## Estimates

These are transparent pace estimates, with their basis returned in `estimates`
and explained on the page. They are not a trained forecasting model or a
confidence interval.

- End-of-day revenue = today's collected revenue × 86,400 / elapsed local-day
  seconds, rounded half-up to cents. It is null before 01:00 IST to avoid
  extrapolating the first hour's sparse observations.
- Next-hour occupied slots = current occupied + last 60 minutes' arrivals −
  departures on currently active inventory. Clamp the result between zero and
  total active capacity minus reserved/maintenance slots.

The occupancy lookback can cross midnight. Estimates assume the current pace
continues; future reservations, facility changes, demand patterns, and payment
delays are not modeled. Revenue projections are not financial commitments.

## Interface

Administrators land on **Admin dashboard** after sign-in. Operator/customer
navigation remains role appropriate, and the dashboard also has a protected
route. The page uses BAY's existing tokens, fonts and icons: olive activity
series, blush outlook/revenue accents and midnight headings/summary strip.

The page provides four primary metrics, hourly arrival/departure and revenue
SVG charts, capacity distribution, two estimates, stay/turnover/net-flow
calculations, and a zone table with occupancy bars. Chart descriptions and an
expandable exact-value table provide an accessible alternative to the graphs.
Upcoming hours are distinguished from observed zeroes; current hours are
labelled partial. No sample or fabricated metrics are shipped in the page.

Data loads on entry, refreshes every 30 seconds while the page is visible, and
can be refreshed manually or paused. Requests do not overlap and are aborted
on cleanup. Failures retain previous figures with an explicit stale-data
warning and last-update time; initial failures offer a retry. Mobile grids
stack and wide tables scroll inside their containers.

See [validation evidence](../testing/US25-test-evidence.md). Load/SLA acceptance
and statistical forecast accuracy are not established by this increment.
