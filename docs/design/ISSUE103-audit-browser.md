# Admin audit event browser

Issue #103 adds a read-only Audit log workspace for administrators using the
existing [US-29 audit contract](US29-audit-log.md). Customers and operators have
no navigation entry and cannot render the page through the workspace guard.
The API independently requires an active Admin account. Audit writes, event
producers, allowlisted payloads and append-only ORM protections are unchanged.

`GET /api/audit/` keeps newest-first ordering with an event-ID tie breaker,
50-row pages and the existing maximum of 100 rows. It supports these optional
filters, combined with AND:

| Parameter | Meaning |
| --- | --- |
| `event_type` | Exact event action, up to 100 characters |
| `actor_id` | Existing exact historical actor ID filter, up to 64 characters |
| `actor` | Case-insensitive recorded username substring OR exact actor ID, up to 150 characters |
| `resource_type` | Exact resource type, up to 100 characters |
| `start` | Inclusive ISO-8601 timestamp |
| `end` | Exclusive ISO-8601 timestamp, later than start when both are supplied |

Send explicit timestamp offsets for unambiguous instants; the UI converts its
labelled browser-local date inputs to UTC ISO timestamps. Invalid filters use
the shared HTTP 400 `{error, code, details}` envelope. Unknown valid filters
produce an empty result. Actor filters use historical snapshots, including
deleted or renamed users, without joining the current user directory. Responses,
including errors, use no-store cache headers.

The event table shows local time, recorded actor username and role, action,
resource type and ID. Inspect expands the event's peer IP, actor ID, UTC timestamp,
formatted previous/new state changes and original recorded JSON. React escapes
all recorded text. Failed authentication events without a verified actor are
labelled accordingly. No payload HTML is interpreted.

Filters apply on submit and reset to page one; clearing filters restores all
events. Requests abort on unmount or filter/page changes; late responses cannot
overwrite a newer selection. A 15-second deadline provides a retryable error.
Loading, empty, invalid-filter and API-error states are distinct. Pagination
constructs same-origin GET requests rather than following server-provided links
with credentials. The horizontally scrollable table has a labelled keyboard
region, native buttons, labelled filters and expandable details. Existing BAY
colors and spacing are retained at desktop and mobile widths.

No edit/delete controls, mutation APIs, schema changes, new audit producers,
retention jobs or permission-policy changes are introduced.

## Verification

- `python manage.py test common.tests.test_audit common.tests.test_audit_browser`
  verifies filters, time boundaries and offsets, pagination, access denial,
  unchanged audit payloads and append-only protections.
- `npm test`, `npm run lint` and `npm run build` verify frontend helpers and build.
- Browser checks cover pagination, applying/clearing filters, expandable state
  changes, loading/errors/empty states, escaped content, role restrictions and
  responsive table containment.
