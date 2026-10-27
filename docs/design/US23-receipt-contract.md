# US-23 receipt API contract

Issue: [#43 — Generate bill and receipt](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/43).

## Generate a receipt

`POST /api/parking/receipts/` requires authentication and accepts only a completed parking record ID:

```json
{ "record_id": 123 }
```

A successful first request returns HTTP 201 and a stable receipt identifier, unique invoice number, itemized charge snapshots, entry/exit timestamps, elapsed duration, rate, multiplier, billable hours, grace period, total fee and currency. Repeating the request for the same session returns the same receipt with HTTP 200; a one-to-one database constraint prevents duplicate receipts for a session.

The receipt stores its own snapshot of vehicle/slot labels, timestamps, rate, multiplier, duration, computed charge breakdown and total. Later edits to the parking record do not rewrite an issued receipt. The billed amount is copied from checkout, not recomputed during receipt generation.

## Read and print

- `GET /api/parking/receipts/{receipt_id}/` returns receipt data as JSON.
- `GET /api/parking/receipts/{receipt_id}/print/` renders a printer-friendly HTML page. The page provides a Print / Save as PDF action.

Active Admin/Operator accounts can access receipts for operational support. A Customer can generate or read only receipts for a vehicle they own. Unauthenticated requests are rejected and access to another customer's receipt is forbidden.

## Failure behavior and scope

- HTTP 400: the session is not completed, the fee is absent, billing snapshots are incomplete, or the payload is invalid.
- HTTP 403: an authenticated user is not allowed to access the parking session or receipt.
- HTTP 404: the parking record or receipt does not exist.

This story creates invoices/receipts; it does not record payment, claim settlement, generate tax information, or introduce a payment gateway. The printable document explicitly states that it is not proof of payment settlement.

## Verification

Focused tests cover invoice and charge contents, idempotency, API retrieval, the printable page, the open-session 400 response, owner/operator access, anonymous access, invalid/missing records, and immutable receipt snapshots. The repository CI checks remain the authoritative integration result for the PR.
