# US-30 in-app notifications (#50)

Signed-in active accounts have an inbox above their workspace content. Unread
alerts appear as banners (up to three), with a live unread count, manual refresh,
dismiss buttons, and paginated history including dismissed alerts. Dismissal is
explicit: opening the list does not mark everything read. Polling runs every 30
seconds only in a visible tab and resumes on visibility changes; no new worker,
socket server or dependency is required.

| Event | Recipient | Trigger |
| --- | --- | --- |
| `facility_full` | Active Admin/Operator accounts | After a successful check-in commits, if no active slot in an active zone remains available |
| `checkout` | Vehicle owner, if active | After checkout and any enclosing receipt transaction commit; this confirms checkout, not payment |
| `reservation_expiring` | Reservation customer | Inbox refresh finds a confirmed reservation ending in the next 15 minutes (including exactly 15 minutes, excluding already expired bookings) |

Reservation warnings display the exact expiry in Asia/Kolkata. Historical
facility alerts describe capacity at the event, not a promise of current status.
Notifications remain available until dismissed/read; history is preserved.

`GET /api/notifications/?unread_only=true&page=1` returns a standard 20-item
paginated response plus `unread_count`. Omitting `unread_only` includes history.
`POST /api/notifications/<id>/read/` marks one owned notification read and returns
`id`, `read_at`, `unread_count`; repeat requests preserve the original timestamp.
Other recipients' IDs return 404, including for administrators. No endpoint
allows clients to create alerts or choose recipients. Both endpoints require
active authenticated accounts, use the shared error envelope and prohibit caching.

The recipient/event unique constraint deduplicates re-delivery, including after
dismissal. A recipient/read-state index supports unread queries. Facility-full
callbacks use the latest active session ID to coalesce concurrent final arrivals;
a release/refill creates a new event. Expiry keys include reservation ID/end time.
Expiry alerts are generated only when that owner's inbox is requested; there is
no background delivery when the app is closed, nor a backfill for expired bookings.

Parking dispatch runs in `transaction.on_commit`, inside a separate savepoint,
with failures caught and logged as a fixed message. Rollback discards the callback.
Dispatch is best-effort: outages can lose an alert; a durable outbox/retry service
is outside this story. Reservation polling retries naturally and does not restore
unread status on previously dismissed warnings. Responses count the current
database state; concurrent tabs converge on the next refresh.

Apply `python manage.py migrate` before serving the new endpoints. Tests in
`notifications.tests` cover actual check-in/checkout producers, capacity and
recipient filtering, repeat cycles, transaction rollback, dispatch failures,
receipt integration, expiry boundaries, ownership, pagination, dismissal, JWT
and account status. The PostgreSQL CI job includes this suite as well.

Local verification (2026-11-04): full SQLite suite passed (600 tests, 12 skips),
PostgreSQL regression set passed (262 tests), and the final notification suite
passed separately (12 tests). All 94 frontend helper tests, lint and production
build passed, with existing Users/Profile lint and Three.js chunk warnings.
An isolated browser session displayed all three event types; dismissing checkout
changed unread count from 3 to 2 and preserved the read item in history. Test
fixtures, credentials, logs and preview artifacts stay ignored.
