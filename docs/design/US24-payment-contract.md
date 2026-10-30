# US-24 — Payment Recording Contract

**Story:** US-24 (#44)  
**Epic:** E6 — Pricing, Billing & Payment (#19)  
**Owner:** Member 3  
**Implementation PR:** [#86](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/pull/86)

## Workflow and acceptance sequence

Payment settlement happens **after checkout**, not as part of checkout finalization.

1. Checkout completes the parking session and creates its receipt with payment status `Pending`.
2. An authenticated, active Admin/Operator records the receipt's final payment state through `POST /api/parking/receipts/{receipt_id}/payment/`.
3. For `Paid`, the operator supplies a supported method (`Cash`, `Card`, or `UPI`) and the exact outstanding bill amount. The service records the payment timestamp and operator attribution.
4. The receipt and its associated completed parking session are synchronized in the same database transaction.
5. For `Waived`, the collected amount is zero, payment method and payment timestamp remain empty, and operator attribution is retained.

## Validation and state rules

- Unsupported methods/statuses, missing payment method for `Paid`, negative amounts, and amounts that do not exactly match the bill are rejected with HTTP 400.
- `Pending` does not represent a settlement and a repeated `Pending → Pending` request is a no-op; it must not rewrite audit attribution.
- `Paid` and `Waived` are terminal states. An identical retry is idempotent; a conflicting transition returns HTTP 409.
- Payment writes are restricted to authenticated, active Admin/Operator accounts.

## Verification coverage

The PR's billing tests cover supported methods, payment timestamp and operator attribution, Pending and Waived behavior, invalid methods and amounts, authorization, missing receipts, zero-value bills, idempotent retries, terminal-state conflicts, and receipt/session synchronization.

GitHub Actions for PR #86 reported successful completion for the Continuous Integration and Security verification workflows on the reviewed revision. This records CI status only; it is not a claim that tests were run locally.

## Requirement traceability

- Handbook: FR-26 — payment status recording.
- SRS v1.1 / RTM: FR-28 — Payment Processing & Status.
- Canonical user story: [US-24 (#44)](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/44).

The canonical issue's acceptance criteria specify the same post-checkout sequence described above.
