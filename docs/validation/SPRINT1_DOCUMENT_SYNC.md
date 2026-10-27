# Sprint 1 documentation consistency report

Recorded 27 October 2026 against application commit `c98346e7a219114a03f84a53cb2a0d017deb3315`, current issue states and [integration CI](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/actions/runs/40451144341). Historical Phase 1/Phase 3 reports remain dated baseline records, not current completion claims.

## Corrections made

The README and frontend guide now describe the implemented application. The RTM separates implementation and verification, corrects module paths and withdraws an unsupported search performance Pass. The SAD identifies delivered versus planned components, current routes, data model, public availability, error contract and actual operational sequences. The SRS and generator receive the same implementation addendum and corrected traceability paths; original requirements are retained where functionality is not yet implemented. Test-plan execution is supplemented by the dated test summary rather than changing the historical PDF. The reassignment record retains historical context with a current-status correction.

## Functional gaps retained for review

| Baseline expectation | Observed code | Disposition |
| --- | --- | --- |
| DEC-14 matching-or-smaller compatibility and EV-specific eligibility | `operations.services` uses exact vehicle class or legacy `any`; vehicles have no separate EV-tag field | Requirement gap; do not claim DEC-14 acceptance or weaken it to make tests pass. Facility/operations owners must implement or agree a requirement change |
| DEC-04 nearest-compatible recommendation | Allocation orders database candidates rather than physical distance; optional manual `slot_id` exists | Nearest-location semantics not established; needs an agreed proximity rule and implementation |
| FR-10 occupied-vehicle identity illustration | Public availability serializes safe slot/zone/type/state fields, no vehicle/owner identifiers | Public behavior is intentional in PR #71. Do not expose identities publicly. Any separate authorized identity view remains absent |
| DEC-05 QR/exit verification | Checkout accepts `registration_number`; no scanning or token-verification workflow | Future functionality; checkout API acceptance does not establish scanner acceptance |
| FR-25 digital slip, QR image and receipt | Check-in persists a signed ticket token and returns record JSON | Token implemented; image/printable slip and receipt remain incomplete (US-23 open) |
| FR-24/26 fees, penalties and payment recording | Ordinary hourly/grace fee saved on ParkingRecord; `ParkingRate.penalty_fee` exists but checkout does not apply it; no invoice/payment model or method input | Do not report payment success, receipt or full billing acceptance; US-22/23/24 remain open |
| Reservation, reporting, audit and notification functionality | No corresponding domain apps or routes on this baseline | Planned requirements retained; no completion claim |
| Performance and complete NFR coverage | Passing regression/targeted races, no 50-request or 100,000-record benchmark | Keep NFR targets; record full target as unverified |

These are specification/code differences and missing capabilities, not proof of a new runtime regression. This documentation PR changes no application behavior. Existing contracts and database schemas remain intact.

## Tracker discrepancies

Sprint 1 remains open with three unresolved stories. Its description and several issue-body sprint/FR references are stale. US-11/12 assignees currently match Member 4, while their issue-body ownership still says Member 2. The [review](../meeting-notes/SPRINT1_REVIEW.md) records facts without inventing scope approval, editing issue acceptance criteria or moving work unilaterally.

## Document governance

SRS and RTM version 1.2.0 and SAD version 1.2.0 describe the 27 October application snapshot. The original test-plan PDF and legacy SAD PDF remain historical; use the current SAD markdown and test addendum. Retrospective actions are explicitly proposed until the team records actual decisions. No claim of formal sprint acceptance is made.
