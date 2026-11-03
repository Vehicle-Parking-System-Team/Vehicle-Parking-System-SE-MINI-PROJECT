# US-29 audit log contract

The audit log is an append-only record of security and operational events. Each
entry snapshots the actor ID, username and role, timestamp, connected peer IP,
event type, affected resource and a small JSON details object. The recorder does
not copy request bodies, headers, passwords, tokens, or arbitrary client input.

`GET /api/audit/` is restricted to active administrators and returns entries in
newest-first chronological order using bounded page-number pagination. Optional
`event_type` and `actor_id` query parameters narrow the result. Other roles get
HTTP 403; write methods are not exposed. Model and queryset write operations
also reject updates and deletes.

This increment records successful and failed login attempts, logout, and
successful parking-slot maintenance transitions. Role changes, fee waivers,
reservation cancellation and other actions have no producer in the current
baseline; those flows must call `common.audit.record_audit_event` when added.

Audit entries are retained without a foreign key to the actor, so deleting an
account does not rewrite its historical identity snapshot. No retention purge
is configured in this increment.
