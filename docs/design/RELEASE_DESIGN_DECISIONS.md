# Vehicle Parking System Release Design Decisions

8 November 2026

The implementation baseline uses the following concrete decisions for demonstration and review. The original requirement IDs are preserved; these refinements describe delivered behavior without inventing a prior approval.

| Decision | Implemented behavior | Traceability |
| --- | --- | --- |
| Allocation | Exact class or legacy any; deterministic zone/name candidate order. Distance-ranked and broader vehicle-fit rules remain extension points. | FR-05 FR-07; DEC-04 DEC-14 |
| Ticketing | Signed session token with manual plate-based checkout. Scanner interfaces can use the token through a later integration. | FR-25 |
| Billing | Hourly/grace/multiplier fee snapshots; printable receipt; separate recorded Cash/Card/UPI settlement. penalty_fee is a retained configuration field. | FR-23 FR-24 FR-25 FR-26 |
| Reservation expiry | Confirmed/Cancelled/Fulfilled persistence; expiry is derived from time/grace for eligibility and alerts. | FR-19 FR-22 FR-30 |
| Public data | Anonymous availability exposes facility state only; identity is handled in authorized APIs. | FR-10 NFR-SEC-01 |
| Interfaces | React screens and REST-only operational workflows are listed separately in the SAD. | SRS sections 2 and 3 |
| Security scope | Environment origin/HTTPS controls tested locally; TLS certificate and proxy are deployment checks. JWTs use localStorage and explicit Bearer headers. | NFR-SEC-04 NFR-SEC-05 |
| Search | Owner joins and active-session prefetch keep partial search serialization at three queries. | FR-11 NFR-PERF-03 |
| Acceptance | Automated evidence and repository review are recorded separately from final team/instructor acceptance. | Test Plan section 15 |

The team can use this register to explain architectural choices and confirm any baseline requirement changes during review.
