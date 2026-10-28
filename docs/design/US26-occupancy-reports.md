# US-26 occupancy and usage report contract

Issue: [#46](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/46).
This increment provides a read-only administrator API, tests and documentation.
It does not add a report screen, exports, revenue calculations or database models.
Reporting maps to FR-28 in the committed SRS/SAD/RTM; the issue also retains its
older SRS FR-29 reference. See [execution evidence](../testing/US26-test-evidence.md).

## Endpoint and permission dependency

`GET /api/reports/occupancy/`

Uses `accounts.permissions.IsAdmin` from US-02 (#22), with the existing JWT/session
authentication and US-31 error handler. Unauthenticated requests return 401;
authenticated Operators/Customers and inactive administrators are denied.
No report-specific role implementation is added. US-02 merged in PR #78 and is
included in this branch's base. The endpoint does not permit POST, PATCH or DELETE.

| Query field | Meaning |
| --- | --- |
| `start` | Required ISO-8601 timestamp; inclusive |
| `end` | Required ISO-8601 timestamp; exclusive and later than start |
| `interval` | `hour` or `day`; default `day` |
| `zone` | Optional positive current zone ID; omission includes all current zones |

Offsets are converted to Asia/Kolkata. Timestamps without an offset are interpreted
in Asia/Kolkata. Buckets follow local clock-hour/day boundaries; first and last
buckets may be partial. The report is limited to 366 days and 10,000 zone-period
rows per request. Exceeding either bound returns 400 with field validation details;
use a narrower range or an individual zone. These are API resource limits.
An unknown positive zone ID returns structured 404 `NOT_FOUND`.

Example, with an administrator access token in the local environment:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/reports/occupancy/?start=2026-10-20T00:00:00&end=2026-10-21T00:00:00&interval=hour&zone=1' -Headers @{ Authorization = "Bearer $env:PARKING_ACCESS_TOKEN" }
```

## Calculation rules

The report captures one `as_of` time. For each parking record, occupied time is
the overlap between the requested bucket and the parking interval. A missing
checkout uses `as_of`; completed intervals are also clipped to `as_of`. Only
positive overlaps contribute. A record ending exactly at bucket start, or
starting exactly at bucket end, contributes nothing to that bucket.

For each zone and bucket:

```text
observed time = max(0, min(bucket end, as_of) - bucket start)
occupied slot-minutes = sum of overlapping parking-record minutes
capacity slot-minutes = current slot count × observed minutes
utilization percent = 100 × occupied slot-minutes / capacity slot-minutes
```

Zero capacity or zero observed time produces 0%, without division errors.
Future buckets remain present with zero observed time and activity. Today's
unfinished buckets use elapsed time, not the unelapsed portion of the bucket.
`entries` counts check-ins inside that bucket and before `as_of`; carry-in
sessions contribute occupied time but not new entries. Displayed minutes and
percentages are rounded to two decimal places after aggregation.

All current zones are included, even empty/inactive zones. Capacity counts all
currently persisted slots, including inactive and maintenance slots. Records are
attributed through the slot's **current zone**. The response labels both policies:

```json
{
  "capacity_basis": "current_total_slot_inventory",
  "zone_basis": "current_slot_zone"
}
```

This is a current-inventory comparison for historical activity. The database
does not retain a complete capacity, maintenance or zone-movement timeline;
the report does not claim exact historical operational utilization. It does
not reconstruct past capacity from current status or invent snapshot data.
Changing current inventory/zone assignments can change a historical report.

`peak_hours` lists each zone's local clock hours (0–23) with the largest accumulated
occupied slot-minutes across the requested range, independently of the chosen
row interval. All ties are returned in ascending hour order. Zero activity
returns an empty hours list. The response declares
`peak_hour_basis=occupied_slot_minutes_by_local_clock_hour`. This measures usage,
not an instantaneous simultaneous-vehicle peak or a normalized hourly percentage.

## Response shape

Top-level fields: `timezone`, `interval`, `start`, `end`, `as_of`, `capacity_basis`,
`zone_basis`, `peak_hour_basis`, `results`, and `peak_hours`.

Each result contains `zone_id`, `zone_name`, bucket `start`/`end`, `slot_count`,
`observed_minutes`, `occupied_slot_minutes`, `utilization_percent`, and `entries`.
Rows are ordered by zone ID, then bucket start. Every selected zone receives
every requested bucket, including zero-value rows. With no zones, both arrays
are empty. Peak entries contain `zone_id`, `hours`, and `occupied_slot_minutes`.

The response does not expose vehicles, owners, operators, payments or ticket
tokens. `Cache-Control` prevents caching. Queries read existing `ParkingRecord`,
`ParkingSlot` and `ParkingZone` data; no cross-module writes or schema changes
are made. Aggregation relies on canonical parking-record integrity and does
not silently repair overlapping or otherwise inconsistent historical records.

## Integration scope

Only route registration touches existing implementation code. New code lives
in `backend/reports/`; no installed application entry is required because this
package defines no models. Existing Django test discovery includes `reports/tests.py`.
The source queries are bounded by the date range and use streamed record iteration;
the report does not issue a database query per zone or bucket.

The local implementation is subject to review before merge.
PostgreSQL and deployment performance acceptance must be recorded separately
from SQLite functional tests. No new performance claim is made for the existing
NFR response-time targets.
