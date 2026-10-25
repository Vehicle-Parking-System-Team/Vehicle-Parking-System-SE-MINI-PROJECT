# US-11 public parking availability

US-11 (#31) implements FR-10 and SAD §3.4.4 using the existing
`parking_slots` domain and facility layout. It exposes current slot states,
not historical utilization or the US-25 administrative revenue dashboard.

## Access and data contract

`GET /api/parking/availability/` returns HTTP 200 and a JSON array. Anonymous
visitors and signed-in users see the same public information. Authentication
is deliberately not processed on this route, so an expired credential does
not block information available anonymously. POST, PUT, PATCH and DELETE
return HTTP 405. Existing management routes retain their Admin/Operator policy.

Example item:

```json
{
  "id": 1,
  "zone": 1,
  "zone_name": "Zone A",
  "zone_is_active": true,
  "slot_number": "A-01",
  "floor": 0,
  "status": "available",
  "vehicle_type": "Compact",
  "is_active": true
}
```

Only active slots in active zones are returned. Available, Occupied, Reserved
and Maintenance states remain visible. A NULL historical floor remains
"Unmapped floor". No vehicle plate, owner, parking-record identifier, operator
or ticket is serialized. This public projection intentionally excludes vehicle
identities described in the broader FR-10 architecture illustration.

Optional API filters:

| Parameter | Meaning |
| --- | --- |
| `zone` | Positive integer zone ID; an unknown ID returns an empty array |
| `vehicle_type` | Exact canonical value: `Two-Wheeler`, `Compact`, `SUV`, `EV Charging` |

Both filters may be combined. Invalid values return HTTP 400 through the
US-31 `{error, code, details}` contract. Legacy `any`/unknown classifications
remain visible without a type filter and do not match a selected canonical
type. This filter describes classification; it does not promise allocation
compatibility or implement the smaller-vehicle compatibility hierarchy.

## Frontend behavior

Visitors choose **View parking availability** on the sign-in screen. Signed-in
Admin, Operator and Customer accounts use **Parking availability** in navigation.
The existing facility management view remains separate for Admin/Operator.

The read-only view fetches the public array and applies zone and exact type
filters locally. Floor selectors group the filtered results. Total, Available,
Occupied and Other counts describe the selected floor and filters and are
calculated from the same rows as the map. Reserved and Maintenance count toward
Total and Other, never Available. Empty results yield zero counts and 0%
occupancy without division errors. Occupancy is occupied / total, rounded to
the nearest whole percent. Directory text search only narrows directory/2D
items; the labelled floor metrics retain their zone/type scope.

Every 30 seconds, and on manual **Refresh**, the view reads a fresh snapshot.
The server sends `Cache-Control: no-store, no-cache`; the client also requests
`no-store` and omits credentials. Poll requests do not overlap, and requests
and timers are cancelled when leaving the view. The last successful timestamp
is displayed. On failure, the last successful rows are retained with an
explicit stale-data warning; retries clear the warning only after success.

Slot status is the occupancy source used by existing operations. US-17 updates
its ParkingRecord and slot in one transaction. US-11 performs no domain writes,
adds no models/migrations and does not infer or repair mismatched historical
records. Checkout integration and concurrent allocation protections remain
with their owning stories.

Verification is recorded in [US11-test-evidence.md](../testing/US11-test-evidence.md).
