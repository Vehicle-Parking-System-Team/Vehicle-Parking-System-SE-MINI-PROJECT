# Reservation-aware facility snapshots and workspace links

Issue #102 extends [public availability](US11-parking-availability.md) without
changing stored slot states, booking windows, allocation locks or migrations.

Both slot projections expose `reservation_protected` and `walk_in_available`
booleans. A confirmed booking protects its bay until its end plus
`RESERVATION_BUFFER_MINUTES`, including bookings that have not started. This
matches general walk-in allocation because walk-ins have no known departure.
Cancelled, fulfilled and expired windows do not block. No customer, plate,
reservation code or booking time is exposed in the public projection.

Public `status` is `reserved` for a physically available protected bay; occupied
and maintenance states take precedence. Management keeps physical `status` for
lifecycle actions and displays available protected bays as Reserved. Counters,
2D tiles and 3D models all use the same display classification. A known vehicle
may still redeem its own booking under existing check-in rules. Eligibility is
a general walk-in snapshot, not a guarantee for a particular vehicle class.
Customers can still request future bookings on protected bays; the reservation
service validates the requested window. No per-slot reservation queries are
added to list reads: eligibility is an indexed correlated EXISTS projection.

Both map modes refresh 30 seconds after each completed request, with one request
at a time and a 15-second request timeout. Hidden tabs pause and abort work;
leaving the page aborts requests and clears timers/listeners. The design demo
does no polling. Failures retain the last good snapshot and display an explicit
stale-data warning; a successful refresh clears it. Manual refresh cancels old
work. Map and vehicle models are rebuilt from the successful new snapshot.

Workspace links use `?page=facility` or `?page=profiles&vehicle=42`. Navigation
pushes browser history; reload and Back/Forward restore the page and selected
vehicle. Unrelated query parameters and anchors are preserved. The current
role's visible navigation is the allowlist, so unsupported or forbidden links
are replaced with that role's default before rendering. Existing component and
backend permission guards remain authoritative for records and privileged APIs.
Vehicle IDs must be positive safe integers. Links contain no authentication data.

## Verification

- Reservation projection regressions cover future/current windows, cancellation,
  fulfilment, exact expiry, configured buffer, privacy, raw management status,
  query count, walk-in rejection and the booking owner's permitted check-in.
- Frontend tests cover protected-bay counters, sequential polling, timeout,
  cancellation, visibility changes, route restoration, invalid IDs and RBAC fallbacks.
- Run `python manage.py test` from `backend`, then `npm test`, `npm run lint`
  and `npm run build` from `frontend`.
