# Sprint 1 delivery review

Recorded 27 October 2026 against application commit `c98346e7a219114a03f84a53cb2a0d017deb3315` and live GitHub issues/milestones. Planned sprint window: 19–25 October 2026. All displayed closure times use Asia/Kolkata (IST).

The original six-story commitment is closed. The current milestone contains 13 stories (49 SP): 10 closed (38 SP), three open (11 SP). This is a delivery record, not a claim that the whole application or every NFR has been accepted. Formal team sign-off and disposition of the three open stories are not recorded.

## Commitment and scope changes

The original 25 SP commitment was US-01, US-05, US-09, US-10, US-17 and US-31. US-06, US-07, US-11 and US-12 add 13 SP of closed work. US-25, US-29 and US-30 add 11 SP of unfinished work. The milestone description still reflects the original six stories; issue membership is the current allocation snapshot. These totals must not be presented as the original velocity commitment.

| Story | Scope | SP | Tracker status | Closed at | Merged implementation PRs |
| --- | --- | --- | --- | --- | --- |
| [#1](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/1) US-01 Authenticate and logout | Original | 3 | Closed | 21 Oct 20:21 IST | [#56](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/pull/56), [#59](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/pull/59) |
| [#25](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/25) US-05 Register a vehicle | Original | 5 | Closed | 22 Oct 18:30 IST | [#61](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/pull/61) |
| [#26](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/26) US-06 View and update vehicle | Added to milestone | 4 | Closed | 25 Oct 23:28 IST | [#65](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/pull/65) |
| [#27](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/27) US-07 Search vehicle and current status | Added to milestone | 3 | Closed | 26 Oct 00:03 IST | [#66](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/pull/66) |
| [#29](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/29) US-09 Create, modify and remove parking slots | Original | 5 | Closed | 24 Oct 20:49 IST | [#64](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/pull/64) |
| [#30](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/30) US-10 Maintain slot state | Original | 3 | Closed | 24 Oct 20:49 IST | [#64](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/pull/64), [#72](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/pull/72) |
| [#31](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/31) US-11 View current parking status | Added to milestone | 3 | Closed | 25 Oct 23:37 IST | [#71](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/pull/71) |
| [#32](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/32) US-12 Enforce slot integrity and destructive-operation rules | Added to milestone | 3 | Closed | 26 Oct 23:40 IST | [#72](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/pull/72) |
| [#37](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/37) US-17 Check in vehicle and assign slot | Original | 5 | Closed | 25 Oct 22:15 IST | [#67](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/pull/67) |
| [#45](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/45) US-25 Admin dashboard metrics | Added to milestone | 5 | Open | Open | — |
| [#49](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/49) US-29 Audit log | Added to milestone | 3 | Open | Open | — |
| [#50](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/50) US-30 In-app notifications | Added to milestone | 3 | Open | Open | — |
| [#51](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/51) US-31 Shared validation and error-handling contract | Original | 4 | Closed | 19 Oct 22:19 IST | [#55](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/pull/55) |

US-07 closed at 00:03 IST on 26 October and US-12 closed at 23:40 IST on 26 October, after the planned local calendar window. They remain visible above as later closure evidence rather than being backdated. GitHub's milestone due timestamp is `2026-10-25T00:00:00Z`; the human-readable 19–25 October window and actual closure timestamps are recorded separately.

## Delivered increment and demonstration coverage

Authentication and logout, vehicle registration/profile/search, slot/zone management, public availability, check-in and shared API errors are implemented. US-12 also completes the real fee/checkout/slot-release integration for US-10. Use [the test summary](../testing/SPRINT1_TEST_SUMMARY.md) for existing browser demonstration evidence and CI results. No new sprint-review meeting or customer demonstration was observed for this record.

US-18 ([PR #73](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/pull/73)), US-21 ([PR #63](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/pull/63)), US-19 ([PR #74](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/pull/74)) and US-20 ([PR #75](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/pull/75)) are also merged on the inspected application baseline. Their current tracker allocation is outside Sprint 1; they are not added to its delivered SP total. No checkout or history frontend is implemented.

## Open work and closure conditions

- US-25 [#45](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/45): admin metrics; open, 5 SP.
- US-29 [#49](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/49): audit log; open, 3 SP.
- US-30 [#50](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/50): notifications; open, 3 SP.

The Scrum Master must agree the destination sprint/backlog for these unresolved carryovers and then reconcile milestone membership and description. This documentation change does not change estimates, close issues or milestones, or invent an acceptance decision. Issue-body target sprints also disagree with current milestone membership: US-25/US-29 say Sprint 2 and US-30 says Sprint 3. Their older FR cross-reference prose must be reconciled with the canonical RTM (FR-27, FR-29 and FR-30 respectively).

See [the retrospective observations](SPRINT1_RETROSPECTIVE.md) and [the consistency report](../validation/SPRINT1_DOCUMENT_SYNC.md) for unresolved functionality gaps and technical follow-up.
