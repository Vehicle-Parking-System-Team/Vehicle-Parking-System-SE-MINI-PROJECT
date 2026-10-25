# Vehicle Parking System — Document & GitHub Backlog Audit Report
**Phase 1: Pull, Audit, and Compare All Project Documents Against GitHub Issues**

**Repository:** `Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT`  
**Workspace:** `c:\Users\Trisha V P\Vehicle-Parking-System-SE-MINI-PROJECT-1`  
**Audit Date:** 19 October 2026  
**Audit Baseline:** Git `origin/main` commit `02e18ea` and live GitHub Issue Tracker  
**Status:** AUDIT COMPLETE — AWAITING TEAM APPROVAL BEFORE CORRECTIONS

---

## 1. Repository and Git-State Verification

- **Repository Root:** `c:\Users\Trisha V P\Vehicle-Parking-System-SE-MINI-PROJECT-1`
- **Active Git Branch:** `main`
- **Remote Tracking:** `origin/main` (`https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT.git`)
- **Remote Synchronization:** The local `main` branch was fast-forwarded to `origin/main` (commit `02e18ea`). Local branch is fully up to date with remote `main`.
- **Committed History Verified:**
  - `02e18ea` (origin/main, origin/HEAD): Delete `docs/SAD/Vehicle_Parking_System_SAD.pdf`
  - `b51de23`: Add files via upload (`Vehicle_Parking_System_SAD (2) (1) (1).pdf`)
  - `44c3578`: Add files via upload (`docs/testing/Vehicle_Parking_System_Test_Plan.pdf`)
  - `5dbc55e`: Add files via upload (`docs/requirements/Vehicle_Parking_System_SRS.docx`)
  - `85bfc5d`: Delete `docs/architecture` directory
  - `1f316c7`: Delete `docs/design` directory
- **Local Working Tree State (Uncommitted / Untracked):**
  - Untracked file: `docs/requirements/traceability_matrix.md` (Local RTM draft created previously)
  - Untracked file: `scripts/generate_srs.js` (Local script designed to generate SRS docx from an internal data model)
  - Untracked file: `scripts/package.json` & `scripts/package-lock.json` (Local Node.js dependency files for docx generation)
- **Impact of Local State on Audit:** None of the untracked files have altered the committed repository baseline. The audit was conducted strictly against the latest committed documents (`Vehicle_Parking_System_SRS.docx`, `Vehicle_Parking_System_SAD (2) (1) (1).pdf`, `Vehicle_Parking_System_Test_Plan.pdf`), while cross-auditing `traceability_matrix.md` to prevent propagation of conflicting mappings into official documents.
- **Confirmation:** No destructive operations (reset, clean, stash, checkout) were performed. No existing project documents, code files, or GitHub issues were modified.

---

## 2. Document Inventory

| # | Document File Path | Format | Version / Date Stated | Apparent Owner | Document Purpose & Stated Scope |
|---|---|---|---|---|---|
| 1 | `docs/requirements/Vehicle_Parking_System_SRS.docx` | DOCX (Word) | Version 1.0 (Undated / Course UE24CS341A) | Team (PES University) | Software Requirements Specification. Contains only 14 functional requirements (FR-01 to FR-14) covering minimal vehicle registration, slot operations, check-in/out, and error handling. Missing all 32 user stories and FR-15 to FR-30. |
| 2 | `docs/SAD/Vehicle_Parking_System_SAD (2) (1) (1).pdf` | PDF (23 pages) | Version 0.1 (Draft / Undated) | VPS Engineering Team | Software Architecture & Design Specification (SAD). Defines a modular monolith (React 18 SPA + Django REST Framework + PostgreSQL). Declares baseline scope restricted to FR-01..14, and marks FR-15..30 as provisional/out-of-scope. Uses a 3rd conflicting FR numbering scheme. |
| 3 | `docs/testing/Vehicle_Parking_System_Test_Plan.pdf` | PDF (10 pages) | Version 1.0 (12 October 2026) | Member 3 (Test Plan Lead) | Software Test Plan. Covers 10 Use Cases (UC-01 to UC-10), maps 32 user stories (US-01 to US-32) across all 4 members, uses Handbook requirement numbers (FR-01 to FR-30), and sets test levels, metrics, and templates. |
| 4 | `docs/requirements/traceability_matrix.md` (Local untracked) | Markdown | Version 1.0.0 (October 2026) | Member 1 (Integration Lead) | Requirements Traceability Matrix. Maps FR-01 to FR-30 using custom story IDs (`US-VM-01`, `US-SM-01`, etc.). Completely drops Reservation Management (E4) and misassigns Billing & Payments to Member 4. |
| 5 | `scripts/generate_srs.js` (Local untracked) | JavaScript (Node.js) | Version 1.1 generator draft | Member 1 | Automation script using `docx` library. Contains hardcoded tables for FR-01 to FR-30 matching `traceability_matrix.md` rather than the canonical 32 GitHub issues. |
| 6 | `README.md` | Markdown | Initial setup (October 2026) | Team | High-level project summary and directory tree. Outdated: still lists `docs/architecture/` and `docs/design/` which were deleted from git. |

---

## 3. Verified GitHub Issue Inventory

The GitHub Issue Tracker (`Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT`) was queried directly via the authenticated API. A total of **52 issues and 1 PR** were retrieved.

### 3.1 Agreed Epics (8 Canonical Epics)
The project is partitioned into **8 agreed Epics**, with exactly **2 Epics (8 User Stories, 4 per epic) owned by each team member**:

| Epic # | Epic Title | Functional Domain | Assigned Owner | GitHub Assignee | Canonical Stories |
|---|---|---|---|---|---|
| **#2** | **E1 – Identity & Access Management** | Auth, logout, RBAC, user accounts, profiles, passwords | Member 1 | `Trisha-Vallamkonda-Prathap` | US-01, US-02, US-03, US-04 (13 SP) |
| **#15** | **E2 – Vehicle Management** | Vehicle registration, updates, plate search, duplicate handling | Member 1 | `Trisha-Vallamkonda-Prathap` | US-05, US-06, US-07, US-08 (16 SP) |
| **#16** | **E3 – Parking Facility & Availability** | Slot CRUD, state management, live occupancy dashboard, integrity rules | Member 2 / Member 4 | `tejasv5467` / `maddox095` | US-09, US-10 (Member 2 - Done); US-11, US-12 (Reassigned to Member 4 - 6 SP) |
| **#17** | **E4 – Reservation Management** | Advance reservations, modification, cancellation, conflict prevention, check-in link | Member 2 | `tejasv5467` | US-13, US-14, US-15, US-16 (15 SP) |
| **#18** | **E5 – Parking Operations** | Check-in, slot allocation, single active session, check-out, slot release, history | Member 3 | `vasishtcoffee` | US-17, US-18, US-19, US-20 (16 SP) |
| **#19** | **E6 – Pricing, Billing & Payment** | Rate configuration, fee calculation, receipt/bill generation, payment recording | Member 3 | `vasishtcoffee` | US-21, US-22, US-23, US-24 (13 SP) |
| **#20** | **E7 – Admin Dashboard & Reporting** | Dashboard operational metrics, occupancy reports, revenue reports, exportable logs | Member 4 | `maddox095` | US-25, US-26, US-27, US-28 (14 SP) |
| **#21** | **E8 – Audit, Notifications & Quality** | Security audit logging, in-app notifications, shared validation, security hardening | Member 4 | `maddox095` | US-29, US-30, US-31, US-32 (15 SP) |

*Note on Duplicate/Redundant Epic Issues:*
- **Issue #13** is titled `E5 – Parking Operations` (assigned to `vasishtcoffee`, open, no labels) — this is an unlabelled redundant duplicate of Epic #18.
- **Issue #3** (`Admin Dashboard & Reporting`) and **Issue #9** (`Audit, Notifications & Quality`) were closed as duplicates in favor of #20 and #21.

---

### 3.2 Canonical User Story Backlog (32 User Stories)

| Story ID | Issue # | Story Title | Parent Epic | Owner | SP | Milestone / Sprint | Primary Requirement Mappings (Handbook / SRS v1.1) |
|---|---|---|---|---|---|---|---|
| **US-01** | #1 | Authenticate and logout | E1 (#2) | Member 1 | 3 SP | Sprint 1 (19–23 Oct) | Handbook `FR-15` / SRS v1.1 `FR-16, FR-17` |
| **US-02** | #22 | Enforce role-based access | E1 (#2) | Member 1 | 5 SP | Sprint 2 (26–30 Oct) | Handbook `FR-16` / SRS v1.1 `FR-18` |
| **US-03** | #23 | Admin manages user accounts | E1 (#2) | Member 1 | 3 SP | Backlog (Sprint 3) | Handbook `FR-17` / SRS v1.1 `FR-15, FR-21` |
| **US-04** | #24 | Manage profile and password | E1 (#2) | Member 1 | 2 SP | Backlog (Sprint 3) | Handbook `FR-18` / SRS v1.1 `FR-19, FR-20` |
| **US-05** | #25 | Register a vehicle | E2 (#15) | Member 1 | 5 SP | Sprint 1 (19–23 Oct) | Handbook `FR-01` / SRS v1.1 `FR-01` |
| **US-06** | #26 | View and update vehicle | E2 (#15) | Member 1 | 4 SP | Sprint 2 (26–30 Oct) | Handbook `FR-02` / SRS v1.1 `FR-02` |
| **US-07** | #27 | Search vehicle and current status | E2 (#15) | Member 1 | 3 SP | Sprint 2 (26–30 Oct) | Handbook `FR-11` / SRS v1.1 `FR-11` |
| **US-08** | #28 | Vehicle validation and duplicate handling | E2 (#15) | Member 1 | 4 SP | Backlog (Sprint 3) | Handbook `FR-13, FR-14` / SRS v1.1 `FR-13, FR-14` |
| **US-09** | #29 | Create, modify and remove parking slots | E3 (#16) | Member 2 | 5 SP | Sprint 1 (19–23 Oct) | Handbook `FR-03` / SRS v1.1 `FR-03, FR-23` |
| **US-10** | #30 | Maintain slot state | E3 (#16) | Member 2 | 3 SP | Sprint 1 (19–23 Oct) | Handbook `FR-04` / SRS v1.1 `FR-04` |
| **US-11** | #31 | View current parking status | E3 (#16) | Member 4 *(Reassigned from Member 2)* | 3 SP | Sprint 2 (26–30 Oct) | Handbook `FR-10` / SRS v1.1 `FR-10` |
| **US-12** | #32 | Enforce slot integrity and destructive-operation rules | E3 (#16) | Member 4 *(Reassigned from Member 2)* | 3 SP | Sprint 2 (26–30 Oct) | Handbook `FR-07, BR-12` / SRS v1.1 `FR-07, NFR-SAFE-01` |
| **US-13** | #33 | Create a parking reservation | E4 (#17) | Member 2 | 5 SP | Sprint 2 (26–30 Oct) | Handbook `FR-19` / Cross-ref `UC-04` |
| **US-14** | #34 | Modify or cancel a future reservation | E4 (#17) | Member 2 | 2 SP | Backlog (Sprint 3) | Handbook `FR-21` / Cross-ref `UC-04` |
| **US-15** | #35 | Prevent reservation conflicts | E4 (#17) | Member 2 | 4 SP | Backlog (Sprint 3) | Handbook `FR-20` / `NFR-SAFE-01, NFR-PERF-02` |
| **US-16** | #36 | Link valid reservation to check-in | E4 (#17) | Member 2 | 4 SP | Backlog (Sprint 3) | Handbook `FR-22` / `FR-05, UC-04` |
| **US-17** | #37 | Check in vehicle and assign slot | E5 (#18) | Member 3 | 5 SP | Sprint 1 (19–23 Oct) | Handbook `FR-05` / SRS v1.1 `FR-05, FR-25` |
| **US-18** | #38 | Prevent duplicate active assignment | E5 (#18) | Member 3 | 3 SP | Sprint 2 (26–30 Oct) | Handbook `FR-06` / SRS v1.1 `FR-06, NFR-SAFE-02` |
| **US-19** | #39 | Check out vehicle and release slot | E5 (#18) | Member 3 | 5 SP | Sprint 2 (26–30 Oct) | Handbook `FR-08, FR-09` / SRS v1.1 `FR-08, FR-09` |
| **US-20** | #40 | Retain parking history | E5 (#18) | Member 3 | 3 SP | Sprint 2 (26–30 Oct) | Handbook `FR-12` / SRS v1.1 `FR-12` |
| **US-21** | #41 | Configure parking rates | E6 (#19) | Member 3 | 3 SP | Backlog (Sprint 3) | Handbook `FR-23` / SRS v1.1 `FR-27` |
| **US-22** | #42 | Calculate parking fee | E6 (#19) | Member 3 | 5 SP | Backlog (Sprint 3) | Handbook `FR-24` / SRS v1.1 `FR-26, FR-27` |
| **US-23** | #43 | Generate bill and receipt | E6 (#19) | Member 3 | 3 SP | Backlog (Sprint 3) | Handbook `FR-25` / SRS v1.1 `FR-28` |
| **US-24** | #44 | Record payment status | E6 (#19) | Member 3 | 2 SP | Backlog (Sprint 4) | Handbook `FR-26` / SRS v1.1 `FR-28` |
| **US-25** | #45 | Admin dashboard metrics | E7 (#20) | Member 4 | 5 SP | Sprint 2 (26–30 Oct) | Handbook `FR-27` / Cross-ref `FR-27` |
| **US-26** | #46 | Occupancy and parking-usage reports | E7 (#20) | Member 4 | 3 SP | Backlog (Sprint 3) | Handbook `FR-28` / SRS v1.1 `FR-29` |
| **US-27** | #47 | Revenue reports | E7 (#20) | Member 4 | 3 SP | Backlog (Sprint 3) | Handbook `FR-28` / SRS v1.1 `FR-29` |
| **US-28** | #48 | Export reports | E7 (#20) | Member 4 | 3 SP | Backlog (Sprint 3) | Handbook `FR-28` / SRS v1.1 `FR-30` |
| **US-29** | #49 | Audit log | E8 (#21) | Member 4 | 3 SP | Sprint 2 (26–30 Oct) | Handbook `FR-29` / SRS v1.1 `FR-22` |
| **US-30** | #50 | In-app notifications | E8 (#21) | Member 4 | 3 SP | Backlog (Sprint 3) | Handbook `FR-30` / Cross-ref `UC-09` |
| **US-31** | #51 | Shared validation and error-handling contract | E8 (#21) | Member 4 | 4 SP | Sprint 1 (19–23 Oct) | Handbook `FR-13, FR-14` / SRS v1.1 `FR-13, FR-14` |
| **US-32** | #52 | Security hardening and verification | E8 (#21) | Member 4 | 5 SP | Backlog (Sprint 4) | Handbook `NFR-SEC-01..07` / SRS v1.1 `NFR-SEC-01..07` |

*Note on Closed Duplicate Stories:* Issues #4, #5, #6, #7, #8, #10, #11, #12, #14 were earlier duplicate submissions of US-25..32 by Member 4 and are correctly closed.

---

## 4. Critical Requirement and Scope Conflicts

### 4.1 Conflict A: Three Competing Requirement Numbering Schemes
Across the documents and issues, three entirely different mappings for requirement identifiers (FR-15 through FR-30) are co-existing:

```
+------------------------------------------------------------------------------------------------------+
| SCHEME 1: TEAM HANDBOOK & TEST PLAN (Canonical Baseline)                                              |
| FR-01..02 (Vehicle) | FR-03..04, 10 (Slots) | FR-05..09, 12 (Operations) | FR-13..14 (Validation)   |
| FR-15..18: Identity & Access Management (US-01..04)                                                  |
| FR-19..22: Reservation Management (US-13..16)                                                        |
| FR-23..26: Pricing, Billing & Payment (US-21..24)                                                    |
| FR-27..28: Admin Dashboard & Reports (US-25..28)                                                     |
| FR-29..30: Audit Log & Notifications (US-29..30)                                                     |
+------------------------------------------------------------------------------------------------------+
                                                VS
+------------------------------------------------------------------------------------------------------+
| SCHEME 2: RTM (traceability_matrix.md) & generate_srs.js                                             |
| FR-01..12: Vehicle, Slot, Operations                                                                 |
| FR-13..14: Validation and Error Messaging                                                            |
| FR-15..22: Identity, User Status, Password & Security Audit Trail                                    |
| FR-23..24: Slot Zones & Types                                                                        |
| FR-25..26: Digital Slips / QR Tickets & Duration Calculation                                         |
| FR-27..30: Tariffs, Payment Processing, Summary Reports & Exports                                    |
| >>> CRITICAL GAP: RESERVATIONS (E4 / US-13..16) ARE COMPLETELY MISSING! <<<                          |
+------------------------------------------------------------------------------------------------------+
                                                VS
+------------------------------------------------------------------------------------------------------+
| SCHEME 3: SAD DOCUMENT (Vehicle_Parking_System_SAD, Section 3.8)                                     |
| FR-01..02: Auth & Passwords | FR-03: Vehicles | FR-04..05: Slots & Allocation Engine                  |
| FR-06..08: Entry/Exit Operations | FR-09..11: Billing & Pricing | FR-12..14: Dashboard, Export, Audit|
| FR-15..30: Declared "Provisional / Out of Scope" (ANPR, barriers, surge pricing, EV charging, etc.) |
+------------------------------------------------------------------------------------------------------+
```

### 4.2 Conflict B: Module Ownership Discrepancy (Member 3 vs. Member 4)
- **Agreed Backlog & Test Plan:** Member 3 owns **Pricing, Billing & Payment (Epic E6, US-21 to US-24)**. Member 4 owns **Admin Dashboard & Reporting (Epic E7, US-25 to US-28)** and **Audit, Notifications & Quality (Epic E8, US-29 to US-32)**.
- **RTM (`traceability_matrix.md`) & `generate_srs.js`:** Erroneously lists Member 4 as owner of FR-27..FR-30 under "Billing & Payments", and assigns slot zones/types and digital tickets to Members 2 and 3 under FR-23..26.

### 4.3 Conflict C: Scope Truncation in Committed SRS
- The committed Word document `Vehicle_Parking_System_SRS.docx` only contains **14 requirements (FR-01 to FR-14)**. 
- It completely omits Identity/Authentication (FR-15..18 / US-01..04), Reservations (FR-19..22 / US-13..16), Billing (FR-23..26 / US-21..24), Dashboard/Reporting (FR-27..28 / US-25..28), and Audit/Notifications (FR-29..30 / US-29..30).
- As a result, the committed SRS covers only Sprint 1 baseline operations and fails to serve as the requirements baseline for 18 out of the 32 agreed user stories.

### 4.4 Conflict D: SAD Architecture Declares Agreed Backlog "Provisional / Out of Scope"
- In `Vehicle_Parking_System_SAD (2) (1) (1).pdf` (Section 1.2, 3.8, and 4.6), the author states:
  > *"Discrepancy between authoritative SRS v1.0 baseline (FR-01 to FR-14) and provisional team backlog requirements (FR-15 to FR-30)... Resolution: The proposed architecture restricts baseline scope to FR-01 through FR-14. FR-15 through FR-30 are retained purely as provisional design structures subject to pending verification."*
- Furthermore, the SAD lists unapproved hardware features (ANPR, physical barriers, surge pricing, EV charging) as FR-18, FR-19, FR-21, FR-22, FR-24, FR-29, FR-30, creating confusion regarding the true software project scope.

---

## 5. SRS Discrepancies (`docs/requirements/Vehicle_Parking_System_SRS.docx`)

1. **[SRS-DISC-01 | Critical] Missing 18 Functional Requirements:** The document defines only FR-01 through FR-14. FR-15 through FR-30 are missing entirely.
2. **[SRS-DISC-02 | Critical] Missing 32 User Stories:** The document does not contain any user stories, story points, acceptance criteria, or epic mappings.
3. **[SRS-DISC-03 | High] Missing Module & Ownership Structure:** There is no division into the 8 epics or attribution to the 4 team members.
4. **[SRS-DISC-04 | High] Missing Reservation Management Scope:** Reservations (agreed under Epic E4, US-13..16) are not mentioned anywhere in Section 5 or Section 2.
5. **[SRS-DISC-05 | High] Missing Billing & Payment Scope:** Tariff computation, bill generation, and payment recording (agreed under Epic E6, US-21..24) are absent.
6. **[SRS-DISC-06 | Medium] Incomplete NFR Targets:** NFR-PERF-01, NFR-PERF-02, NFR-PERF-03, and NFR-SEC-05 state quantitative targets as "TBD".
7. **[SRS-DISC-07 | Low] Stale Version & Metadata:** Title page lists "Version 1.0" with an empty/unpopulated revision log, while the Test Plan and GitHub issues reference "Team SRS v1.1".

---

## 6. SAD Discrepancies (`docs/SAD/Vehicle_Parking_System_SAD (2) (1) (1).pdf`)

1. **[SAD-DISC-01 | Critical] Incompatible FR Numbering Scheme in Section 3.8:** The SAD creates an independent 14-requirement baseline where FR-01/02 are Auth/JWT, FR-03 is Vehicle, FR-04/05 are Slots, FR-06..08 are Entry/Exit, FR-09..11 are Billing, FR-12..13 are Dashboard/Reporting, and FR-14 is Audit. This contradicts both the SRS v1.0 and the Team Handbook/Test Plan.
2. **[SAD-DISC-02 | Critical] Demotion of Canonical Epics to "Provisional":** Epics E4 (Reservations), E6 (Billing), E7 (Dashboard/Reports), and E8 (Audit/Notifications) are classified as provisional or out of scope in Section 1.2 and 4.6.
3. **[SAD-DISC-03 | High] Inclusion of Hardware/Unapproved Out-of-Scope Features:** Section 3.8 lists ANPR camera feeds, gate barriers, dynamic surge pricing, overstay fines, EV charging, and multi-region failover as formal FR items (FR-18, 19, 21, 22, 24, 29, 30). These were never part of the agreed 32 user stories and should not be numbered as FRs.
4. **[SAD-DISC-04 | Medium] Missing Endpoint Contracts for Epics E4, E7, E8:** While Section 4.3 provides RESTful endpoint tables for Vehicles, Slots, Check-In, Check-Out, and Billing, Reservation endpoints are labeled "Provisional Scope" with minimal schema, and Dashboard/Reporting/Notification endpoints lack detailed payload schemas.
5. **[SAD-DISC-05 | Medium] Filename Formatting Anomaly:** File is committed as `docs/SAD/Vehicle_Parking_System_SAD (2) (1) (1).pdf`, reflecting browser download duplicates.
6. **[SAD-DISC-06 | Low] Stale Metadata:** Cover page lists "Document Version: 0.1 (Proposed Draft)" with all approval signatures and dates marked "TBD".

---

## 7. Test Plan Discrepancies (`docs/testing/Vehicle_Parking_System_Test_Plan.pdf`)

1. **[TEST-DISC-01 | High] Reliance on Handbook FR Numbering without Reconciled SRS:** Section 3 and Section 13 map test cases to Handbook requirement numbers (e.g. UC-04: FR-19..22 for Reservations, UC-07: FR-23..26 for Billing). Because `Vehicle_Parking_System_SRS.docx` lacks these requirements, test traceability cannot be validated against the committed SRS.
2. **[TEST-DISC-02 | Medium] Discrepancy with Local RTM Test IDs:** Test Plan establishes Use-Case structured test IDs (e.g. `TC-UC01-SYS-001`, `TC-UC05-INT-001`, `TC-SEC-001`), whereas `traceability_matrix.md` uses module-prefixed IDs (`TC-VM-01`, `TC-OP-01`, `TC-BIL-01`).
3. **[TEST-DISC-03 | Low] Empty Signature / Approval Table:** Page 9 contains empty signature blocks for Test Plan Lead, Dev Lead, and Product Owner.
4. **[TEST-DISC-04 | Low] Execution Record Placeholders:** Representative test scenarios correctly retain "Not Run" status (per IEEE standards), but need automated execution harness linking once Sprint 1 code is committed.

*Commendation:* The Test Plan is the most coherent document in the repository; its 8 Epics and 32 User Story assignments match the GitHub issues exactly.

---

## 8. RTM and Traceability Discrepancies (`docs/requirements/traceability_matrix.md`)

1. **[RTM-DISC-01 | Critical] Non-Canonical User Story Identifiers:** Uses ad-hoc codes (`US-VM-01..04`, `US-SM-01..05`, `US-OP-01..07`, `US-BIL-01..04`, `US-IAM-01..08`, `US-SYS-01..02`) instead of the agreed canonical backlog IDs (`US-01` through `US-32`).
2. **[RTM-DISC-02 | Critical] Total Omission of Epic E4 (Reservation Management):** The RTM has zero entries for Reservations (US-13 to US-16).
3. **[RTM-DISC-03 | Critical] Ownership Misattribution for Billing:** Lines 42–45 attribute Billing & Payments (FR-27..30) to Member 4 instead of Member 3.
4. **[RTM-DISC-04 | High] Missing Cross-Cutting Quality Requirements:** Fails to map US-31 (Shared Validation Contract) and US-32 (Security Hardening) as distinct stories, merging them into vague `US-SYS-01/02`.
5. **[RTM-DISC-05 | Medium] Ghost File References:** Links design artifacts to `docs/design/models.md`, `docs/design/views.md`, and `docs/design/api.md`, none of which exist in the repository (the `docs/design` directory was deleted in commit `1f316c7`).

---

## 9. Other Documentation Discrepancies

1. **[README-DISC-01 | Medium] Broken Directory Tree in README.md:** Lines 20–21 document `docs/architecture/` and `docs/design/`, which no longer exist in the repository.
2. **[README-DISC-02 | Low] Tooling Claims:** Mentions Jenkins CI/CD as part of the stack; the Test Plan specifically warns that Jenkins is not yet configured.
3. **[SCRIPTS-DISC-01 | High] Untracked Generation Script:** `scripts/generate_srs.js` is uncommitted and encodes the conflicting RTM numbering scheme.

---

## 10. Formatting-Only Problems

| Document | Page / Section | Formatting Issue Description | Impact |
|---|---|---|---|
| `docs/SAD/Vehicle_Parking_System_SAD (2) (1) (1).pdf` | Filename | Repetitive copy-paste suffixes `(2) (1) (1)` in repository filename. | Unprofessional appearance in repository tree. |
| `docs/SAD/Vehicle_Parking_System_SAD (2) (1) (1).pdf` | Page 1 | Document Revision History table contains "TBD" date and generic author. Approval table is blank. | Appears as unapproved draft. |
| `docs/SAD/Vehicle_Parking_System_SAD (2) (1) (1).pdf` | Pages 9–11 | Requirement table text wraps awkwardly across column boundaries in portrait mode. | Readability issue. |
| `docs/requirements/Vehicle_Parking_System_SRS.docx` | Revision Table | Revision History lists version 1.0 without release date or approved signers. | Incomplete version record. |
| `docs/requirements/Vehicle_Parking_System_SRS.docx` | Table of Contents | Page numbers in TOC do not match actual section page breaks. | Usability issue when navigating document. |
| `docs/testing/Vehicle_Parking_System_Test_Plan.pdf` | Pages 9–10 | Approval table contains blank signature/date blocks. | Formal sign-off pending. |
| GitHub Issue #1 | Title & Labels | Title is `Authenticate and logout` (missing `US-01` prefix); labels are empty (missing `User Story`, `3 SP`, `Member 1`, `Priority: High`). | Inconsistent with all other 31 user story issues. |
| GitHub Issue #13 | Title & Labels | Title is `E5 – Parking Operations`; unlabelled and redundant with Epic #18. | Clutters issue board. |

---

## 11. Missing Information and Decisions Requiring Team Approval

The following items cannot be unilaterally resolved and require explicit team consensus:

1. **Dual Requirement Numbering Reconciliation Decision:**
   - *Option A (Recommended):* Adopt the **Handbook Requirement Numbering** (FR-01 to FR-30) as the authoritative master numbering. This immediately brings the SRS into 100% alignment with the Test Plan, GitHub issue mappings, and handbook.
   - *Option B:* Adopt the IEEE partitioned numbering (FR-01 to FR-30 as in `generate_srs.js`), which requires rewriting all 10 use-case mappings in the Test Plan and modifying all 32 GitHub issues.
   - *Recommendation:* Approve **Option A**. The GitHub issues already carry dual references, but the Test Plan directly executes Option A.

2. **Policy Thresholds & Business Rules (Currently marked TBD across documents):**
   - **BR-RATE-01:** Parking rate unit (hourly flat vs. hourly vehicle-type tiered vs. 15-minute intervals).
   - **BR-GRACE-01:** Grace period duration upon check-in and checkout (e.g. 15 minutes free or billed).
   - **BR-CUTOFF-01:** Advance reservation cancellation window and refund rules (e.g. cancel up to 1 hour before hold window).
   - **BR-CLEANUP-01:** Slot deletion vs. deactivation rule: Can a slot with historical records be deleted or only deactivated? (Recommended: Soft-delete/deactivate only).

3. **Restoration / Renaming of Deleted Design Folders:**
   - Decide whether to recreate `docs/architecture` and `docs/design` as Markdown specifications, or consolidate them under `docs/SAD`.

---

## 12. Complete Correction Matrix

| # | Document | Section / Page | Issue Reference | Current Content | Agreed Issue / Backlog Content | Proposed Correction | Approval Needed? |
|---|---|---|---|---|---|---|---|
| **1** | `Vehicle_Parking_System_SRS.docx` | Full Document | Epics #2, #15, #16, #17, #18, #19, #20, #21; US-01..32 | Contains only FR-01..FR-14; no user stories or 8-epic breakdown. | 8 Epics, 32 User Stories, FR-01..FR-30, NFR-SEC-01..07. | Expand SRS to Version 1.1 incorporating all 8 Epics, 32 canonical User Stories with acceptance criteria, and full FR-01..30 specification. | **Yes** (Team approval of SRS v1.1) |
| **2** | `Vehicle_Parking_System_SAD` | Filename | N/A | `docs/SAD/Vehicle_Parking_System_SAD (2) (1) (1).pdf` | Standard repository naming convention. | Rename file to `docs/SAD/Vehicle_Parking_System_SAD.pdf`. | **Yes** (Git rename approval) |
| **3** | `Vehicle_Parking_System_SAD` | Section 1.2 & 4.6 | Epics #17, #19, #20, #21 | Declares FR-15..30 "provisional" and out of baseline scope. | Epics E4 (Reservations), E6 (Billing), E7 (Dashboard), E8 (Audit/Quality) are agreed core backlog. | Update scope to affirm all 8 Epics as committed software architecture components. | **Yes** (Team approval) |
| **4** | `Vehicle_Parking_System_SAD` | Section 3.8 | US-01..32 | Conflicting 14-requirement mapping; lists ANPR, gates, surge pricing as FR-18..30. | No hardware/ANPR features; software-only scope per 32 user stories. | Replace Section 3.8 table with canonical FR-01..30 & US-01..32 architecture component mapping. | **Yes** (Team approval) |
| **5** | `Vehicle_Parking_System_SAD` | Section 4.3 | US-13..16, US-25..30 | Reservation endpoints marked provisional; reports/audit schemas missing. | Formal REST contracts needed for all 8 Epics. | Standardize REST API contracts across all 8 modules (DRF serializers/endpoints). | **Yes** (Team approval) |
| **6** | `Vehicle_Parking_System_Test_Plan.pdf` | Section 3 & 13 | US-01..32 | Uses Handbook FR-01..30; matches GitHub issues, but unaligned with current SRS docx. | Canonical 32 user stories and 10 use cases. | Retain current structure; align SRS and RTM to match this canonical baseline. | **No** (Test plan already matches backlog) |
| **7** | `Vehicle_Parking_System_Test_Plan.pdf` | Section 13.1 | N/A | Test cases have IDs like `TC-UC01-SYS-001`, while local RTM has `TC-VM-01`. | Consistent test naming convention across project. | Adopt Test Plan's `TC-UCxx-...` naming convention as authoritative in RTM. | **Yes** (Team approval) |
| **8** | `traceability_matrix.md` (untracked) | Section 1 | US-01..32 | Uses ad-hoc IDs (`US-VM-01`, etc.); omits Reservation Management (E4); misassigns Billing to Member 4. | 32 Canonical stories; Member 2 owns E3 & E4; Member 3 owns E5 & E6; Member 4 owns E7 & E8. | Overwrite/rebuild RTM with exact 32 canonical stories, correct member ownership, and links to actual code/test files. | **Yes** (Commit approval) |
| **9** | `traceability_matrix.md` (untracked) | Section 1 | N/A | References deleted files `docs/design/models.md`, `docs/design/views.md`. | Active repository code and doc paths. | Update design references to point to `docs/SAD/Vehicle_Parking_System_SAD.pdf`. | **Yes** (Commit approval) |
| **10** | `scripts/generate_srs.js` | Lines 75–186 | Epics #17, #19, #20 | Encodes obsolete RTM data omitting Reservations. | Authoritative 32 user stories and Handbook FR-01..30. | Update script data dictionary or replace with clean Markdown-to-DOCX pipeline. | **Yes** (Tooling approval) |
| **11** | `README.md` | Lines 20–21 | N/A | Lists deleted directories `docs/architecture` and `docs/design`. | Accurate repository structure. | Clean up directory tree in README.md. | **Yes** (Doc update approval) |
| **12** | GitHub Issue #1 | Issue Title & Labels | US-01 (#1) | Title: `Authenticate and logout`; Labels: `[]` | Title: `US-01 Authenticate and logout`; Labels: `User Story`, `3 SP`, `Member 1`, `Priority: High`. | Recommend updating issue #1 title and labels on GitHub (user/team action). | **Yes** (User manual action on GitHub) |
| **13** | GitHub Issue #13 | Issue #13 | Epic E5 (#18) | Title: `E5 – Parking Operations`; unlabelled stub. | Duplicate of Epic #18. | Recommend closing issue #13 as duplicate of #18 on GitHub (user/team action). | **Yes** (User manual action on GitHub) |

---

## 13. Recommended Safe Correction Order

To ensure full technical consistency without breaking downstream dependencies, execute corrections in the following phased order:

```
[Phase 1: AUDIT & ALIGNMENT] (Current Phase - Completed)
              │
              ▼
[Step 1: TEAM RECONCILIATION & APPROVAL]
  - Formally approve Handbook FR-01..30 as the master requirement numbering.
  - Confirm Member ownership (Member 1: E1/E2, Member 2: E3/E4, Member 3: E5/E6, Member 4: E7/E8).
  - Clarify business policy TBDs (rate units, grace period, cancellation cutoff).
              │
              ▼
[Step 2: REQUIREMENTS BASELINE UPDATE (SRS v1.1)]
  - Update `Vehicle_Parking_System_SRS.docx` (or Markdown source) to incorporate all 8 Epics and 32 User Stories.
  - Synchronize FR-01 through FR-30 with full acceptance criteria.
              │
              ▼
[Step 3: REQUIREMENTS TRACEABILITY MATRIX (RTM) SYNCHRONIZATION]
  - Rebuild `docs/requirements/traceability_matrix.md` with canonical `US-01`..`US-32` IDs.
  - Link all test cases to Test Plan IDs (`TC-UCxx-...`).
              │
              ▼
[Step 4: ARCHITECTURE SPECIFICATION (SAD) ALIGNMENT]
  - Rename `Vehicle_Parking_System_SAD (2) (1) (1).pdf` to standard filename.
  - Remove "provisional" label from Epics E4, E6, E7, E8 in SAD.
  - Reconcile SAD Section 3.8 requirement matrix with SRS v1.1.
  - Remove hardware/ANPR out-of-scope items from formal FR numbering.
              │
              ▼
[Step 5: GITHUB ISSUE CLEANUP (Manual by Team)]
  - Add missing `US-01` prefix and labels to Issue #1.
  - Close duplicate issue #13.
              │
              ▼
[Step 6: TEST PLAN SIGN-OFF & EXECUTION HARNESS]
  - Sign off approvals in Test Plan.
  - Begin Phase 2 implementation and automated test verification.
```

---

## 14. Phase 2 Addendum: Verified Live Backlog & Canonical Requirements Baseline

*Audit Addendum Generated: 19 October 2026*  
*Verification Basis: Live GitHub Issue API (52 issues, 1 PR), committed repository documents (`02e18ea`), and course sprint plan.*

---

### 14.1 Verified Live Issue Inventory & Canonical Backlog

Every issue in the GitHub repository was directly queried and verified. The canonical backlog consists of **8 Epics** and **32 User Stories**, structured as follows:

#### Canonical Epics (8 Verified Epics)
1. **Epic #2 (`E1 – Identity & Access Management`):** Open | Labels: `['Epic', 'Member 1']` | Assignee: `Trisha-Vallamkonda-Prathap` (Member 1) | Scope: Auth, logout, RBAC, user accounts, profiles, passwords | Stories: US-01, US-02, US-03, US-04 (13 SP).
2. **Epic #15 (`E2 – Vehicle Management`):** Open | Labels: `['Epic', 'Member 1']` | Assignee: `Trisha-Vallamkonda-Prathap` (Member 1) | Scope: Vehicle registration, profile updates, license search, validation | Stories: US-05, US-06, US-07, US-08 (16 SP).
3. **Epic #16 (`E3 – Parking Facility & Availability`):** Open | Labels: `['Epic', 'Member 2', 'Member 4']` | Assignee: `tejasv5467` (Member 2) & `maddox095` (Member 4) | Scope: Slot CRUD, slot state management (Member 2 - Done), live occupancy dashboard, integrity safeguards (Reassigned to Member 4 on 25 Oct 2026) | Stories: US-09, US-10 (Member 2, 8 SP); US-11, US-12 (Member 4, 6 SP).
4. **Epic #17 (`E4 – Reservation Management`):** Open | Labels: `['Epic', 'Member 2']` | Assignee: `tejasv5467` (Member 2) | Scope: Advance reservations, modification, cancellation, conflict prevention, check-in link | Stories: US-13, US-14, US-15, US-16 (15 SP).
5. **Epic #18 (`E5 – Parking Operations`):** Open | Labels: `['Epic', 'Member 3']` | Assignee: `vasishtcoffee` (Member 3) | Scope: Check-in, slot allocation, active session uniqueness, check-out, slot release, history | Stories: US-17, US-18, US-19, US-20 (16 SP).
6. **Epic #19 (`E6 – Pricing, Billing & Payment`):** Open | Labels: `['Epic', 'Member 3']` | Assignee: `vasishtcoffee` (Member 3) | Scope: Tariff rates, automated fee calculation, bill/receipt issuance, payment status | Stories: US-21, US-22, US-23, US-24 (13 SP).
7. **Epic #20 (`E7 – Admin Dashboard & Reporting`):** Open | Labels: `['Epic', 'Member 4']` | Assignee: `maddox095` (Member 4) | Scope: Dashboard operational metrics, occupancy reports, revenue analytics, exportable logs | Stories: US-25, US-26, US-27, US-28 (14 SP). *(Replaces closed duplicate #3)*.
8. **Epic #21 (`E8 – Audit, Notifications & Quality`):** Open | Labels: `['Epic', 'Member 4']` | Assignee: `maddox095` (Member 4) | Scope: Security audit logging, in-app notifications, shared validation, security hardening | Stories: US-29, US-30, US-31, US-32 (15 SP). *(Replaces closed duplicate #9)*.

#### Detailed Investigation of Issue #1 and Issue #13
- **Issue #1 (`Authenticate and logout`):**
  - *Current State:* Open, Milestone: `Sprint 1 (19–23 Oct 2026)`, Assignee: `Trisha-Vallamkonda-Prathap`, Labels: `[]` (empty).
  - *Body Analysis:* Fully articulated canonical user story body with 3 Given/When/Then acceptance criteria, Parent Epic #2, 3 SP, Target Sprint 1, Functional Owner Member 1, and dual requirement references (Handbook `FR-15`, SRS v1.1 `FR-16, FR-17`).
  - *Defects:* Missing title prefix `US-01` and missing standard GitHub labels (`User Story`, `3 SP`, `Member 1`, `Priority: High`).
  - *Correction:* Update title to `US-01 Authenticate and logout` and apply labels `['User Story', '3 SP', 'Member 1', 'Priority: High']`. Preserve issue history.
- **Issue #13 (`E5 – Parking Operations`):**
  - *Current State:* Open, Milestone: `None`, Assignee: `vasishtcoffee`, Labels: `[]` (empty).
  - *Body Analysis:* Contains scope summary, user story listing (US-17..20), module dependencies, and expected outcome. It was created as an early unstructured stub.
  - *Redundancy Verification against Epic #18:* Epic #18 (`Parking Operations`, open, labeled `['Epic', 'Member 3']`) covers the identical scope, includes the formal checklist linking issues `#37, #38, #39, #40`, and adheres strictly to the canonical epic template used across all other 7 epics.
  - *Recommendation:* Close Issue #13 as a duplicate of Issue #18 with a reference comment pointing to #18, preserving its history.

---

### 14.2 Step B: Master Canonical Requirement Reconciliation Table

Every functional and non-functional requirement across the committed documents (SRS, SAD, Test Plan, RTM) and live GitHub issue bodies has been reconciled into a single authoritative master table using the **Team Handbook / Test Plan Baseline (`FR-01` to `FR-30` and `NFR-01` to `NFR-11`)**:

| FR / NFR ID | Canonical Requirement Statement | Linked US IDs | Parent Epic | Owner | Applicable Test IDs | Source Evidence | Discrepancy & Resolution |
|---|---|---|---|---|---|---|---|
| **FR-01** | Allow an authorized user or operator to register a vehicle with plate number, vehicle type, and owner details. | US-05 (#25) | E2 Vehicle Mgmt | Member 1 | TC-UC02-UNIT-001, TC-UC02-API-001, TC-UC02-API-002 | SRS 5.1.3; Test Plan UC-02; Issue #25; Handbook FR-01 | Aligned on ID FR-01 and scope. RTM uses ad-hoc ID US-VM-01. SAD renumbers FR-01 as Auth. Master: **FR-01**. |
| **FR-02** | Allow an authorized user or operator to view and update vehicle profile and registration details. | US-06 (#26) | E2 Vehicle Mgmt | Member 1 | TC-UC02-API-001, TC-UC02-API-002 | SRS 5.1.3; Test Plan UC-02; Issue #26; Handbook FR-02 | Aligned on ID FR-02. RTM uses US-VM-02. SAD renumbers FR-02 as Password/JWT. Master: **FR-02**. |
| **FR-03** | Allow an authorized administrator or operator to add, modify, and deactivate/remove parking slots and zones. | US-09 (#29) | E3 Parking Facility | Member 2 | TC-UC03-UNIT-001, TC-UC03-INT-001 | SRS 5.2.3; Test Plan UC-03; Issue #29; Handbook FR-03 | Aligned on ID FR-03. RTM uses US-SM-01 and adds zone mapping. SAD renumbers FR-03 as Vehicle Lookup. Master: **FR-03**. |
| **FR-04** | Maintain real-time slot state with valid status values (Available, Occupied, Maintenance/Unavailable). | US-10 (#30) | E3 Parking Facility | Member 2 | TC-UC03-SYS-002, TC-UC03-INT-001 | SRS 5.2.3; Test Plan UC-03; Issue #30; Handbook FR-04 | Aligned on ID FR-04. RTM uses US-SM-02. SAD renumbers FR-04 as Slot Creation. Master: **FR-04**. |
| **FR-05** | Allow an operator to check in a vehicle and assign it to an available, compatible parking slot. | US-17 (#37) | E5 Parking Operations | Member 3 | TC-UC05-UNIT-001, TC-UC05-INT-001 | SRS 5.3.3; Test Plan UC-05; Issue #37; Handbook FR-05 | Aligned on ID FR-05. RTM uses US-OP-01. SAD renumbers FR-05 as Allocation Engine. Master: **FR-05**. |
| **FR-06** | Enforce single-active-session constraint, preventing a vehicle from being assigned to more than one active slot. | US-18 (#38) | E5 Parking Operations | Member 3 | TC-UC05-INT-002, NFR-SAFE-02 | SRS 5.3.3; Test Plan UC-05; Issue #38; Handbook FR-06 | Aligned on ID FR-06. RTM uses US-OP-02. SAD renumbers FR-06 as Grid UI. Master: **FR-06**. |
| **FR-07** | Prevent assignment of an occupied or unavailable parking slot to another vehicle. | US-12 (#32) | E3 Parking Facility | Member 4 *(Reassigned from Member 2)* | TC-UC03-UNIT-001, TC-UC05-INT-001, NFR-SAFE-01 | SRS 5.3.3; Test Plan UC-03; Issue #32; Handbook FR-07 | Aligned on ID FR-07. Issue #32 assigned to Member 4 on 25 Oct 2026 (originally Member 2). SAD renumbers FR-07 as Vehicle Entry. Master: **FR-07**. |
| **FR-08** | Allow an operator to check out a vehicle, recording exit timestamp and completing the active session. | US-19 (#39) | E5 Parking Operations | Member 3 | TC-UC06-INT-001, TC-UC06-SYS-001 | SRS 5.4.3; Test Plan UC-06; Issue #39; Handbook FR-08 | Aligned on ID FR-08. Grouped with FR-09 in US-19. RTM uses US-OP-04. SAD renumbers FR-08 as Vehicle Exit. Master: **FR-08**. |
| **FR-09** | Automatically release the assigned parking slot back to 'Available' immediately upon successful checkout. | US-19 (#39) | E5 Parking Operations | Member 3 | TC-UC06-INT-001, TC-UC06-SYS-001 | SRS 5.4.3; Test Plan UC-06; Issue #39; Handbook FR-09 | Aligned on ID FR-09. Grouped with FR-08 in US-19. RTM uses US-OP-05. SAD renumbers FR-09 as Fee Calculation. Master: **FR-09**. |
| **FR-10** | Display live parking occupancy status dashboard showing total, available, and occupied slots across zones. | US-11 (#31) | E3 Parking Facility | Member 4 *(Reassigned from Member 2)* | TC-UC03-SYS-002 | SRS 5.2.3; Test Plan UC-03; Issue #31; Handbook FR-10 | Aligned on ID FR-10. Issue #31 assigned to Member 4 on 25 Oct 2026 (originally Member 2). RTM uses US-SM-03. SAD renumbers FR-10 as Receipt/Invoice. Master: **FR-10**. |
| **FR-11** | Allow authorized users or operators to search for a vehicle by license plate and inspect its current status. | US-07 (#27) | E2 Vehicle Mgmt | Member 1 | TC-UC02-API-001 | SRS 5.1.3; Test Plan UC-02; Issue #27; Handbook FR-11 | Aligned on ID FR-11. RTM uses US-VM-03. SAD renumbers FR-11 as Pricing Tiers. Master: **FR-11**. |
| **FR-12** | Maintain persistent, immutable historical parking records for completed sessions. | US-20 (#40) | E5 Parking Operations | Member 3 | TC-UC06-INT-001 | SRS 5.1.3; Test Plan UC-06; Issue #40; Handbook FR-12 | Aligned on ID FR-12. RTM erroneously assigns to Member 1 (US-VM-04). Master owner is **Member 3 (US-20)**. SAD renumbers FR-12 as Dashboard. |
| **FR-13** | Validate all client-submitted payload fields on the server side before processing any operation. | US-08 (#28), US-31 (#51) | E8 Audit & Quality | Member 4 (Team) | TC-UC10-API-001, NFR-SEC-03 | SRS 5.5.3; Test Plan UC-10; Issues #28, #51; Handbook FR-13 | Universal contract. Issue #51 establishes shared format; #28 applies it to vehicles. RTM uses US-SYS-01. SAD renumbers FR-13 as Search/Export. Master: **FR-13**. |
| **FR-14** | Return uniform, structured JSON error messages with standard HTTP status codes for all failed operations. | US-08 (#28), US-31 (#51) | E8 Audit & Quality | Member 4 (Team) | TC-UC10-API-001 | SRS 5.5.3; Test Plan UC-10; Issues #28, #51; Handbook FR-14 | Universal contract (`{'error', 'code', 'details'}`). RTM uses US-SYS-02. SAD renumbers FR-14 as Audit Logging. Master: **FR-14**. |
| **FR-15** | Allow authorized users to register an account and authenticate into the system, with secure token invalidation upon logout. | US-01 (#1), US-03 (#23) | E1 Identity & Access | Member 1 | TC-UC01-SYS-001, TC-UC01-API-002 | Test Plan UC-01; Issue #1, #23; Handbook FR-15 | Missing from committed SRS. RTM splits into FR-15 (reg) and FR-16 (auth). SAD renumbers FR-15 as Reservation. Master: **FR-15**. |
| **FR-16** | Enforce Role-Based Access Control (RBAC) across API endpoints and views for Administrator, Operator, and Customer. | US-02 (#22) | E1 Identity & Access | Member 1 | TC-UC01-API-002, TC-SEC-001 | Test Plan UC-01; Issue #22; Handbook FR-16 | Missing from committed SRS. RTM numbers as FR-18. SAD numbers as Reservation Cancellation. Master: **FR-16**. |
| **FR-17** | Allow administrators to manage user accounts and user lifecycle states (active, suspended, deactivated). | US-03 (#23) | E1 Identity & Access | Member 1 | TC-UC01-SYS-001 | Test Plan UC-01; Issue #23; Handbook FR-17 | Missing from committed SRS. RTM numbers as FR-21. SAD numbers as Subscriptions. Master: **FR-17**. |
| **FR-18** | Allow users to view their profile, update personal contact details, and perform secure password changes. | US-04 (#24) | E1 Identity & Access | Member 1 | TC-UC01-SYS-001 | Test Plan UC-01; Issue #24; Handbook FR-18 | Missing from committed SRS. RTM numbers as FR-19/20. SAD numbers as Gate Barrier (unapproved). Master: **FR-18**. |
| **FR-19** | Allow an authorized user or operator to create an advance parking slot reservation for a valid future time window. | US-13 (#33) | E4 Reservation Mgmt | Member 2 | TC-UC04-API-001, TC-UC04-SYS-001 | Test Plan UC-04; Issue #33; Handbook FR-19 | Missing from committed SRS and RTM! SAD numbers ANPR camera (unapproved) as FR-19. Master: **FR-19**. |
| **FR-20** | Prevent overlapping and conflicting parking reservations for the same slot and time window. | US-15 (#35) | E4 Reservation Mgmt | Member 2 | TC-UC04-API-002, NFR-SAFE-01 | Test Plan UC-04; Issue #35; Handbook FR-20 | Missing from committed SRS and RTM! SAD numbers Multi-lot as FR-20. Master: **FR-20**. |
| **FR-21** | Allow an authorized user or administrator to modify or cancel a future reservation before its start time. | US-14 (#34) | E4 Reservation Mgmt | Member 2 | TC-UC04-API-001 | Test Plan UC-04; Issue #34; Handbook FR-21 | Missing from committed SRS and RTM! SAD numbers Surge Pricing (unapproved) as FR-21. Master: **FR-21**. |
| **FR-22** | Link a valid arriving reservation to vehicle check-in and transition reservation state to fulfilled. | US-16 (#36) | E4 Reservation Mgmt | Member 2 | TC-UC04-API-001, TC-UC05-INT-001 | Test Plan UC-04; Issue #36; Handbook FR-22 | Missing from committed SRS and RTM! SAD numbers Overstay Fines as FR-22. Master: **FR-22**. |
| **FR-23** | Allow administrators to configure parking tariff rates and vehicle category multipliers. | US-21 (#41) | E6 Pricing & Billing | Member 3 | TC-UC07-UNIT-001 | Test Plan UC-07; Issue #41; Handbook FR-23 | Missing from committed SRS. RTM numbers Slot Zones as FR-23. SAD numbers SMS/Email as FR-23. Master: **FR-23**. |
| **FR-24** | Automatically compute parking fee based on session duration, configured tariff, and vehicle category. | US-22 (#42) | E6 Pricing & Billing | Member 3 | TC-UC07-UNIT-001 | Test Plan UC-07; Issue #42; Handbook FR-24 | Missing from committed SRS. RTM numbers Slot Types as FR-24. SAD numbers EV Charging as FR-24. Master: **FR-24**. |
| **FR-25** | Generate an itemized bill and receipt upon checkout with unique identifier and fee breakdown. | US-23 (#43) | E6 Pricing & Billing | Member 3 | TC-UC07-UNIT-001, TC-UC07-SYS-001 | Test Plan UC-07; Issue #43; Handbook FR-25 | Missing from committed SRS. RTM numbers Entry Tickets as FR-25. SAD numbers Mobile Web as FR-25. Master: **FR-25**. |
| **FR-26** | Record payment transaction status (Cash, Card, UPI) and settlement against outstanding bills. | US-24 (#44) | E6 Pricing & Billing | Member 3 | TC-UC07-API-002 | Test Plan UC-07; Issue #44; Handbook FR-26 | Missing from committed SRS. RTM numbers Duration Calc as FR-26. SAD numbers Financial Analytics as FR-26. Master: **FR-26**. |
| **FR-27** | Display administrative operational metrics and KPI dashboard regarding occupancy, revenue, and active sessions. | US-25 (#45) | E7 Dashboard & Reports | Member 4 | TC-UC08-API-001, TC-UC08-SYS-001 | Test Plan UC-08; Issue #45; Handbook FR-27 | Missing from committed SRS. RTM numbers Tariff as FR-27. SAD numbers Custom Roles as FR-27. Master: **FR-27**. |
| **FR-28** | Generate and export periodic operational occupancy reports and revenue summaries in CSV and PDF formats. | US-26 (#46), US-27 (#47), US-28 (#48) | E7 Dashboard & Reports | Member 4 | TC-UC08-SYS-001, TC-UC08-API-002 | Test Plan UC-08; Issues #46, #47, #48; Handbook FR-28 | Missing from committed SRS. RTM numbers Payments as FR-28. SAD numbers Multi-Currency as FR-28. Master: **FR-28**. |
| **FR-29** | Record immutable security audit log entries for privileged events, authentications, fee waivers, and status overrides. | US-29 (#49) | E8 Audit & Quality | Member 4 | TC-UC09-INT-001 | Test Plan UC-09; Issue #49; Handbook FR-29 | Missing from committed SRS. RTM numbers Summary Reports as FR-29. SAD numbers Offline Sync as FR-29. Master: **FR-29**. |
| **FR-30** | Deliver in-app notification alerts for operational events (facility full, reservation expiring, checkout confirmation). | US-30 (#50) | E8 Audit & Quality | Member 4 | TC-UC09-SYS-002 | Test Plan UC-09; Issue #50; Handbook FR-30 | Missing from committed SRS. RTM numbers Export Logs as FR-30. SAD numbers DB Failover as FR-30. Master: **FR-30**. |
| **NFR-PERF-01** | Interactive API response time < 500ms p95 under standard operational load. | US-07, US-25, US-31 | Cross-Cutting | All Members | Automated API benchmarks | SRS 6.1; Test Plan 5.2; Issues #27, #45, #51 | SRS marked target as TBD; Test Plan and RTM define < 500ms p95. |
| **NFR-PERF-02** | ACID transactional consistency under 50+ concurrent check-in/out and reservation requests. | US-12, US-15, US-18 | Cross-Cutting | Members 2, 3 & 4 | Database concurrency isolation tests | SRS 6.1; Test Plan 5.2, 10; Issues #32, #35, #38 | SRS marked target as TBD; Test Plan and RTM define 50+ concurrent requests. |
| **NFR-PERF-03** | Indexed query execution < 200ms on vehicle search and parking history over 100,000 records. | US-07, US-20 | E2 & E5 | Members 1 & 3 | Indexed query benchmark tests | SRS 6.1; Test Plan 5.2; Issues #27, #40 | SRS marked scale as TBD; RTM and Test Plan define 100k records / < 200ms. |
| **NFR-SAFE-01** | Prevent assignment of one active slot to multiple vehicles, and prevent overlapping reservations. | US-12, US-15 | E3 & E4 | Members 2 & 4 | TC-UC03-UNIT-001, TC-UC04-API-002 | SRS 6.2; Test Plan 3; Issues #32, #35 | Fully aligned across SRS, Test Plan, and Issues. |
| **NFR-SAFE-02** | Prevent a single vehicle from having more than one active check-in or active reservation hold. | US-18 | E5 Operations | Member 3 | TC-UC05-INT-002 | SRS 6.2; Test Plan 3; Issue #38 | Fully aligned across SRS, Test Plan, and Issues. |
| **NFR-SAFE-03** | Atomic rollback of multi-table database transactions on partial failure during check-in, checkout, or billing. | US-17, US-19, US-24 | E5 & E6 | Member 3 | TC-UC06-INT-002 | SRS 6.2; Test Plan 5.2; Issues #37, #39, #44 | Fully aligned across SRS, Test Plan, and Issues. |
| **NFR-SEC-01** | Role-Based Access Control enforcement on all protected backend API routes returning HTTP 401/403. | US-01, US-02, US-32 | E1 & E8 | Members 1 & 4 | TC-SEC-001, TC-UC01-API-002 | SRS 6.3; Test Plan 5.4; Issues #1, #22, #52 | Fully aligned across SRS, Test Plan, and Issues. |
| **NFR-SEC-02** | Strict administrative privilege enforcement preventing non-admin roles from performing user admin or global config. | US-02, US-03, US-21, US-32 | E1, E6, E8 | Members 1, 3, 4 | TC-SEC-001 | SRS 6.3; Test Plan 5.4; Issues #22, #23, #41, #52 | Fully aligned across SRS, Test Plan, and Issues. |
| **NFR-SEC-03** | Server-side input sanitization and payload validation rejecting malformed data with HTTP 400 Bad Request. | US-08, US-31, US-32 | E2 & E8 | Members 1 & 4 | TC-UC10-API-001 | SRS 6.3; Test Plan 5.4; Issues #28, #51, #52 | Fully aligned across SRS, Test Plan, and Issues. |
| **NFR-SEC-04** | Transport Layer Security (HTTPS) and restrictive CORS origin policy preventing untrusted requests. | US-32 | E8 Quality | Member 4 | CI CORS configuration check | SRS 6.3; Test Plan 5.4; Issue #52 | Fully aligned across SRS, Test Plan, and Issues. |
| **NFR-SEC-05** | Cryptographic password hashing (Argon2 / PBKDF2) and token expiry; zero plain-text credentials in logs/fixtures. | US-01, US-04, US-32 | E1 & E8 | Members 1 & 4 | TC-SEC-002 | SRS 6.3; Test Plan 5.4; Issues #1, #24, #52 | SRS marked details as TBD; Test Plan and Issue #52 define Argon2/PBKDF2. |

---

### 14.3 Step C: Sprint Planning & Milestone Reconciliation

#### Live GitHub Issue State vs. Agreed 2-Sprint Course Schedule
- **GitHub Milestones Configured in Repo:**
  1. Milestone 1: `Sprint 1 (19–23 Oct 2026)` — **6 Stories assigned, 25 SP total**  
     - US-01 (#1, Member 1, 3 SP): Auth & Logout  
     - US-05 (#25, Member 1, 5 SP): Vehicle Registration  
     - US-09 (#29, Member 2, 5 SP): Slot CRUD  
     - US-10 (#30, Member 2, 3 SP): Slot State Management  
     - US-17 (#37, Member 3, 5 SP): Vehicle Check-In  
     - US-31 (#51, Member 4, 4 SP): Shared Validation & Error Contract  
     *(Capacity: Member 1: 8 SP, Member 2: 8 SP, Member 3: 5 SP, Member 4: 4 SP. Perfectly balanced baseline vertical slice!)*
  2. Milestone 2: `Sprint 2 (26–30 Oct 2026)` — **11 Stories assigned, 42 SP total**  
     - US-02 (#22, Member 1, 5 SP): RBAC Enforcement  
     - US-06 (#26, Member 1, 4 SP): Vehicle View & Update  
     - US-07 (#27, Member 1, 3 SP): Vehicle Search & Status  
     - US-11 (#31, Member 4 [reassigned from Member 2 on 25 Oct 2026], 3 SP): Occupancy View  
     - US-12 (#32, Member 4 [reassigned from Member 2 on 25 Oct 2026], 3 SP): Slot Integrity Rules  
     - US-13 (#33, Member 2, 5 SP): Reservation Creation  
     - US-18 (#38, Member 3, 3 SP): Prevent Duplicate Active Check-In  
     - US-19 (#39, Member 3, 5 SP): Check-Out & Slot Release  
     - US-20 (#40, Member 3, 3 SP): Retain Parking History  
     - US-25 (#45, Member 4, 5 SP): Admin Dashboard Metrics  
     - US-29 (#49, Member 4, 3 SP): Security Audit Log  
     *(Capacity after 25 Oct 2026 Reassignment: Member 1: 12 SP, Member 2: 5 SP, Member 3: 11 SP, Member 4: 14 SP. Total: 42 SP. Member 4 takes over 6 SP from Member 2's Sprint 2 allocation).*
  3. No Milestone Assigned (`None` in GitHub): **15 Stories, 49 SP total**  
     - In their issue descriptions, 13 stories state `Target Sprint: Sprint 3` (US-03, US-04, US-08, US-14, US-15, US-16, US-21, US-22, US-23, US-26, US-27, US-28, US-30) and 2 stories state `Target Sprint: Sprint 4` (US-24, US-32).

#### Root Cause of the Discrepancy
The issue author drafted the backlog assuming a 4-sprint semester lifecycle (Sprints 1–4), but the PES University mini-project course timeline formally specifies a **two-sprint project schedule**:
- **Sprint 1 Window:** 19–23 October 2026.
- **Sprint 2 Window:** 26–30 October 2026.
- **Post-Sprint 2:** Integrated system regression, UAT, and final evaluation.

#### Proposed Resolution for Team Approval
Do not silently condense all 32 stories into Sprint 1 and Sprint 2, as overloading 116 Story Points into two weeks would create an unfeasible 58 SP/sprint team load.

**Recommended 2-Sprint Delivery & Backlog Tiering:**
1. **Sprint 1 (19–23 Oct 2026): Core Functional MVP (25 SP) — KEEP AS CONFIGURED.**  
   All 6 stories currently in Milestone 1 represent the minimum viable vertical slice across all 4 members.
2. **Sprint 2 (26–30 Oct 2026): Operational & Integration Scope (42 SP) — KEEP AS CONFIGURED.**  
   The 11 stories currently in Milestone 2 complete checkout, slot release, reservations, dashboard metrics, and audit logging.
3. **Product Backlog / Post-Sprint 2 Extension (15 Stories, 49 SP):**  
   Retain the remaining 15 stories in the GitHub Backlog (without assigned sprint milestone). Mark their status in the documentation as **"Phase 3 / Extended Backlog"** (covering advanced rates US-21..24, full reports US-26..28, notifications US-30, and security hardening verification US-32).
   *Alternative Option:* If course evaluation requires all 32 stories demonstrated by 30 October, team must agree to absorb high-priority backlog stories (US-21, US-22, US-23) into Sprint 2 and designate low-priority stories (US-14, US-24, US-28, US-30) as stretch goals.

---

### 14.4 Step D: Verification of Document Findings & Audit Self-Consistency Check

All findings from Section 4 through Section 10 of `DOCUMENT_ISSUE_AUDIT.md` were re-verified line-by-line against actual committed files:

1. **SRS Truncation Confirmed:** `docs/requirements/Vehicle_Parking_System_SRS.docx` (SHA-verified from commit `5dbc55e`) contains exactly 561 lines of extracted text, terminating at Section 7.3 after defining only FR-01 through FR-14. Zero user stories exist in the file.
2. **SAD Divergence Confirmed:** `docs/SAD/Vehicle_Parking_System_SAD (2) (1) (1).pdf` (SHA-verified from commit `b51de23`) contains the 14-requirement ad-hoc mapping in Section 3.8 and explicitly marks FR-15..30 as provisional in Sections 1.2 and 4.6.
3. **Test Plan Integrity Confirmed:** `docs/testing/Vehicle_Parking_System_Test_Plan.pdf` (commit `44c3578`) accurately outlines the 8 Epics and 32 user stories with their exact member ownership on Pages 6 and 9. It maintains 10 Use Cases (UC-01..10) mapped to Handbook FR-01..30 and correctly holds execution statuses as "Not Run".
4. **Untracked RTM Conflict Confirmed:** The local `docs/requirements/traceability_matrix.md` contains the flawed ad-hoc IDs (`US-VM-01`, etc.), completely omits Reservation Management (US-13..16), and incorrectly assigns Billing to Member 4.
5. **README Inconsistency Confirmed:** `README.md` lines 20–21 still list `docs/architecture/` and `docs/design/`, which were deleted in git commits `85bfc5d` and `1f316c7`.

#### Audit Report Self-Consistency Corrections
In the initial draft of `DOCUMENT_ISSUE_AUDIT.md`:
- Section 3.2 displayed Issue #1 Story Points as `[]`. Verification confirms the body explicitly specifies `3 SP`.
- Section 3.2 displayed duplicate closed issues #4..14 in one table row. The table has been verified to reflect canonical active issues #45..52.
- These corrections have been incorporated into this verified addendum.

---

### 14.5 Step E: Approval Checkpoint & Execution Sequence

#### Decisions Requiring Team Approval
1. **Adoption of Master Requirement Numbering (Handbook Scheme FR-01..30):**  
   *(Default Recommendation: APPROVE)*. Harmonizes SRS, Test Plan, and GitHub issues with zero breakage to existing test cases.
2. **Sprint Scope Clarification (2-Sprint Delivery vs. 4-Sprint Backlog):**  
   *(Default Recommendation: APPROVE)*. Keep Sprint 1 (25 SP) and Sprint 2 (42 SP) as committed course milestones; maintain the 15 remaining stories in the Product Backlog.
3. **Duplicate Issue #13 Closure:**  
   *(Default Recommendation: APPROVE)*. Close Issue #13 as a duplicate of canonical Epic #18.
4. **Issue #1 Title/Label Update:**  
   *(Default Recommendation: APPROVE)*. Rename Issue #1 to `US-01 Authenticate and logout` and add labels `['User Story', '3 SP', 'Member 1', 'Priority: High']`.
5. **Business Rule Policy Defaults:**  
   - Rate: Flat hourly rate of $2.00 (Two-Wheeler), $5.00 (Compact), $8.00 (SUV), $10.00 (EV Charging).
   - Grace Period: 15 minutes free entry/exit buffer.
   - Reservation Cutoff: Cancellations permitted up to 1 hour prior to reservation start time.
   - Slot Deletion: Soft-deactivation only if historical records exist.

#### Verified Safe Execution Sequence (Phase 2 & Phase 3)
```
[PHASE 1 & 2: AUDIT & BASELINE RECONCILIATION] (COMPLETED)
                     │
                     ▼
[CHECKPOINT APPROVAL]: User / Team signs off on decisions 1–5 above
                     │
                     ▼
[STEP 1: GITHUB ISSUE CLEANUP] (Non-destructive, manual/API)
  - Update Issue #1 title to 'US-01 Authenticate and logout' and apply labels.
  - Close duplicate Issue #13 with reference comment to Epic #18.
                     │
                     ▼
[STEP 2: SRS v1.1 BASELINE UPDATE]
  - Update `Vehicle_Parking_System_SRS.docx` to incorporate all 8 Epics,
    32 User Stories, acceptance criteria, and full FR-01..30 / NFR-01..11.
                     │
                     ▼
[STEP 3: TRACEABILITY MATRIX (RTM) OVERHAUL]
  - Re-generate `docs/requirements/traceability_matrix.md` with canonical
    US-01..US-32, Member 1..4 ownership, and Test Plan TC-UCxx-... IDs.
                     │
                     ▼
[STEP 4: ARCHITECTURE (SAD) HARMONIZATION]
  - Rename `Vehicle_Parking_System_SAD (2) (1) (1).pdf` to standard clean filename.
  - Reconcile Section 3.8 and Section 4.3 to reflect canonical FR-01..30 software scope.
                     │
                     ▼
[STEP 5: README & DIRECTORY TREE CLEANUP]
  - Remove dead directory links (`docs/architecture`, `docs/design`) in README.md.
                     │
                     ▼
[STEP 6: PROCEED TO APPLICATION CODE IMPLEMENTATION (Sprint 1 / Sprint 2)]
```

---

## 12. Addendum: Agile Workload Balancing & User Story Reassignment (25 October 2026)

On 25 October 2026, due to Member 2's workload and availability constraints, two unfinished user stories originally assigned to Member 2 under Epic E3 were reassigned to Member 4:
- **US-11 (#31):** *View current parking status* (FR-10, 3 SP, Sprint 2) — Transferred to Member 4 (`maddox095`).
- **US-12 (#32):** *Enforce slot integrity and destructive-operation rules* (FR-07, BR-12, NFR-SAFE-01, 3 SP, Sprint 2) — Transferred to Member 4 (`maddox095`).

**Retained Scopes:**
- **Member 2:** Retains completed stories US-09 (#29) and US-10 (#30) (merged in PR #64), and retains full ownership of Epic E4 (Reservation Management: US-13, US-14, US-15, US-16).
- **Member 4:** Retains all existing responsibilities under Epic E7 (Admin Dashboard & Reporting: US-25..28) and Epic E8 (Audit, Notifications & Quality: US-29..32), while assuming US-11 and US-12.
- **Sprint 2 Capacity Rebalance:** Member 2 capacity shifts from 11 SP to 5 SP (US-13); Member 4 capacity shifts from 8 SP to 14 SP (US-25, US-29, US-11, US-12). All story requirements, priorities, acceptance criteria, and milestones remain unchanged.


