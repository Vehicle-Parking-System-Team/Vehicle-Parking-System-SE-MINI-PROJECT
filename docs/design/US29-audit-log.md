# US-29 audit log contract

Current integrated delivery: [documentation index](../README.md) and [final verification](../testing/FINAL_VERIFICATION_REPORT.md). The dated scope below records this story or sprint increment.
The audit log is an append-only application record of security and operational events. Each
entry snapshots the actor ID, username and role, timestamp, connected peer IP,
event type, affected resource and a small JSON details object. The recorder accepts
only registered event types and allowlisted detail/state fields. Producers pass
explicit server values; request bodies, headers, passwords and tokens are never copied.

`GET /api/audit/` is restricted to active administrators and returns entries in
newest-first chronological order using bounded page-number pagination. Optional
`event_type` and `actor_id` query parameters narrow the result. Other roles get
HTTP 403 for all read/write methods; anonymous requests get HTTP 401. Administrators
get HTTP 405 for write methods. Default page size is 50, capped at 100. Model saves,
deletes, queryset updates/deletes, base-manager writes, bulk updates and conflict
upserts reject modification. New rows may be appended with create/bulk_create.
These are application/ORM safeguards; direct SQL and a database owner remain
outside this protection. No claim of database-level or cryptographic tamper proofing is made.

## Event producers

| Event | Producer | Details |
| --- | --- | --- |
| `auth.login_succeeded` / `auth.login_failed` | Login API | Outcome only; failed attempts have no verified actor or submitted identifier |
| `auth.logout` | Logout API | Success outcome |
| `auth.password_changed` | Password-change API, including its alias | Empty details; no password/hash/token |
| `account.created` | Admin account-create API | Role and status |
| `account.updated` | Admin role/status API | Before and after role/status |
| `parking_slot.maintenance_changed` | Maintenance service/API | Before and after status |
| `parking_zone.deactivated` | Zone update (PATCH/PUT) and soft-delete (DELETE) service/API | Zone resource ID, previous/current active flags and count of child slots changed from active to inactive |
| `billing.payment_recorded` / `billing.fee_waived` | Settlement service/API | Settlement fields or waived fee amount |
| `reservation.cancelled` | Cancellation service/API | Before and after status |
| `tariff.created` / `tariff.updated` | Rate APIs | Tariff snapshots including penalty and multiplier |

Audit writes share the successful operation's database transaction. An audit
failure returns the existing sanitized HTTP 500 envelope and rolls back the
state change. Failed login events are written after the failed inner transaction
exits, preserving the HTTP 401 response and audit evidence. This assumes the
current `ATOMIC_REQUESTS=False` configuration; enabling request-wide transactions
would require revisiting failed-login persistence. Invalid payloads do not produce
success events. Idempotent settlement retries and unchanged role/status or tariff
updates do not duplicate events. Existing account-change notification signals
remain separate best-effort consumers; audit persistence does not depend on them.

Zone deactivation records one event in the transaction that updates the zone and
its child slots. Already inactive children are excluded from `affected_slot_count`.
An active zone with no active children still produces an event; repeating an
unchanged deactivation produces none. Rejected deactivations produce no success event.

HTTP producers take the actor from authentication and the IP from `REMOTE_ADDR`,
ignoring supplied role, actor and forwarded-IP headers. Services called without an
HTTP request still record an event but have no IP; maintenance and zone-deactivation
calls without an actor have a null actor. Invalid peer addresses are omitted. Reverse-proxy headers
must not be trusted without a separate deployment trust policy.

Audit entries are retained without a foreign key to the actor, so deleting an
account does not rewrite its historical identity snapshot. All records are retained,
including records older than the SAD's 90-day retention target; automated archival/purging
is not configured. No existing application data is rewritten by the additive
`common.0001_initial` migration. Run `python manage.py migrate` during deployment.

The story's API criteria are implemented. This does not establish a frontend audit
screen, production deployment, load acceptance or coverage of every possible future
privileged action. New business flows must explicitly use the recorder.

See [execution evidence](../testing/US29-test-evidence.md) for checks and limits.
