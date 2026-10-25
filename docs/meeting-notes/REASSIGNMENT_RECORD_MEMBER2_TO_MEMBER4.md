# Agile User Story Reassignment Record: Member 2 to Member 4

**Project:** Vehicle Parking System (SE Mini-Project)  
**Date of Record:** 25 October 2026  
**Effective Date:** 25 October 2026  
**Scrum Master & Integration Lead:** Member 1  
**Authoritative Scope:** Documentation Baseline Synchronization  

---

## 1. Executive Summary & Context

Due to temporary workload and availability constraints on the part of **Member 2** (`tejasv5467`), an agile sprint workload balancing decision was executed on **25 October 2026**. **Member 4** (`maddox095`) has taken over the two unfinished user stories originally assigned to Member 2 that are currently in an active or ready state (**US-11** and **US-12**).

This update constitutes an **ownership and responsibility reassignment only**. There are **no changes** to functional scope, acceptance criteria, story point estimates, system architecture, database schema, API contracts, verification cases, or sprint milestone targets.

> [!NOTE]
> GitHub issue assignees and labels for Issue #31 (`US-11`) and Issue #32 (`US-12`) will be manually adjusted in the GitHub repository by the repository administrator following this documentation update. No direct GitHub API label/assignee mutations were performed by automated agents.

---

## 2. Reassigned User Stories Detailed Specification

### Story 1: US-11 (#31) — View Current Parking Status

- **User Story ID:** `US-11` (GitHub Issue #31)
- **Title:** View current parking status
- **Original Owner:** Member 2 (`tejasv5467`)
- **New Owner:** Member 4 (`maddox095`)
- **Effective Reassignment Date:** 25 October 2026
- **Parent Epic:** `E3: Parking Facility & Availability` (GitHub Issue #16)
- **Milestone:** Sprint 2 (26–30 October 2026)
- **Story Points:** 3 SP
- **Priority:** Medium
- **Implementation Status:** Ready / In Progress (Unchanged)
- **Traceable Functional Requirements:** `FR-10` (Live parking occupancy status dashboard for operators and users)
- **Architectural Reference:** `docs/SAD/Vehicle_Parking_System_SAD.md` §3.4.4 (Slot Allocation Engine & Occupancy Dashboard)
- **Planned Target Files:** `frontend/src/pages/Dashboard.jsx`, `backend/parking_slots/views.py`
- **Verification Case ID:** `TC-UC03-SYS-002` (Live Occupancy Dashboard Verification)
- **Dependencies:** 
  - Depends on `US-09` (Slot & Zone CRUD) and `US-10` (Slot State Management) — both completed and merged in PR #64.
  - Reuses shared validation and error handling contracts (`US-31`).
- **Acceptance Criteria (Unchanged):**
  1. Operators and authorized users can access a live facility occupancy dashboard displaying total slots, occupied slots, available slots, and slots under maintenance.
  2. Metrics can be viewed globally for the facility or filtered per individual parking zone.
  3. Real-time slot state changes (check-in, check-out, maintenance toggles) reflect accurately in dashboard queries without data corruption.
  4. Unauthenticated requests are rejected with standard HTTP 401/403 responses.

---

### Story 2: US-12 (#32) — Enforce Slot Integrity and Destructive-Operation Rules

- **User Story ID:** `US-12` (GitHub Issue #32)
- **Title:** Enforce slot integrity and destructive-operation rules
- **Original Owner:** Member 2 (`tejasv5467`)
- **New Owner:** Member 4 (`maddox095`)
- **Effective Reassignment Date:** 25 October 2026
- **Parent Epic:** `E3: Parking Facility & Availability` (GitHub Issue #16)
- **Milestone:** Sprint 2 (26–30 October 2026)
- **Story Points:** 3 SP
- **Priority:** High
- **Implementation Status:** Ready / In Progress (Unchanged)
- **Traceable Functional Requirements:** `FR-07` (Prevent assignment to occupied or unavailable parking slot), `BR-12` (Destructive slot deactivation safeguards), `NFR-SAFE-01` (Single active slot allocation uniqueness constraint)
- **Architectural Reference:** `docs/SAD/Vehicle_Parking_System_SAD.md` §3.4.4, §3.4.5, `DEC-02`, `DEC-03`
- **Planned Target Files:** `backend/parking_slots/services.py`, `backend/operations/services.py`
- **Verification Case IDs:** `TC-UC03-SYS-002`, `TC-UC05-INT-001`, `TC-UC03-UNIT-001`
- **Dependencies:**
  - Depends on `US-09` (Soft deactivation flag `is_active`) and `US-10` (`occupy_slot` and `release_slot` transactional hooks).
  - Integrates with operations service layer (`US-17` check-in allocation).
- **Acceptance Criteria (Unchanged):**
  1. The system strictly forbids assigning an already occupied slot or a slot marked in Maintenance/Inactive status to an arriving vehicle.
  2. Attempted destructive operations (slot deletion or zone deletion) on slots with active parking sessions or active advance reservations are blocked and return HTTP 409 Conflict.
  3. Deactivations are soft (`is_active = False`) to preserve referential integrity of historical parking records and receipts (`DEC-03`).
  4. Concurrent check-in requests competing for the same slot execute under atomic database locks (`select_for_update`) ensuring zero double-allocation violations (`NFR-SAFE-01`).

---

## 3. Retained Responsibilities Matrix

### Member 2 (`tejasv5467`) Retained Responsibilities

Member 2 retains all completed work and retains full functional ownership of Epic E4:
1. **Completed Deliverables (Sprint 1 — Merged in PR #64):**
   - **US-09 (#29):** Create, modify, and remove parking slots and zones (5 SP) — **DONE**.
   - **US-10 (#30):** Maintain slot state and state transition hooks (3 SP) — **DONE**.
2. **Retained Active & Backlog Stories (Epic E4: Reservation Management):**
   - **US-13 (#33):** Create a parking reservation (5 SP, Sprint 2) — Active.
   - **US-14 (#34):** Modify or cancel a future reservation (2 SP, Sprint 3 Backlog).
   - **US-15 (#35):** Prevent reservation conflicts and overlapping windows (4 SP, Sprint 3 Backlog).
   - **US-16 (#36):** Link valid reservation to check-in session (4 SP, Sprint 3 Backlog).
3. **Architectural Roles:**
   - Architectural contributions to the SAD baseline (`docs/SAD/Vehicle_Parking_System_SAD.md`).

### Member 4 (`maddox095`) Updated Responsibilities

Member 4 retains all previously assigned responsibilities and takes on US-11 and US-12:
1. **Epic E7: Admin Dashboard & Reporting (#20):**
   - **US-25 (#45):** Admin dashboard operational metrics (5 SP, Sprint 2) — Active.
   - **US-26 (#46):** Occupancy and parking-usage reports (3 SP, Sprint 3 Backlog).
   - **US-27 (#47):** Revenue reports (3 SP, Sprint 3 Backlog).
   - **US-28 (#48):** Export reports to CSV/PDF (3 SP, Sprint 3 Backlog).
2. **Epic E8: Audit, Notifications & Quality (#21):**
   - **US-29 (#49):** Persistent security audit log (3 SP, Sprint 2) — Active.
   - **US-30 (#50):** In-app milestone notifications (3 SP, Sprint 3 Backlog).
   - **US-31 (#51):** Shared validation and error-handling contract (4 SP, Sprint 1) — **DONE**.
   - **US-32 (#52):** Security hardening and verification (5 SP, Sprint 4 Backlog).
3. **Newly Reassigned Stories (from Member 2):**
   - **US-11 (#31):** View current parking status (3 SP, Sprint 2) — Active.
   - **US-12 (#32):** Enforce slot integrity and destructive-operation rules (3 SP, Sprint 2) — Active.

---

## 4. Sprint 2 Velocity & Capacity Rebalancing

The transfer shifts 6 Story Points of active Sprint 2 implementation work from Member 2 to Member 4:

| Team Member | Original Sprint 2 Allocation | Shift | Rebalanced Sprint 2 Allocation | Active Sprint 2 Stories |
| :--- | :--- | :--- | :--- | :--- |
| **Member 1** | 12 SP | 0 SP | **12 SP** | US-02 (5 SP), US-06 (4 SP), US-07 (3 SP) |
| **Member 2** | 11 SP | -6 SP | **5 SP** | US-13 (5 SP) |
| **Member 3** | 11 SP | 0 SP | **11 SP** | US-18 (3 SP), US-19 (5 SP), US-20 (3 SP) |
| **Member 4** | 8 SP | +6 SP | **14 SP** | US-25 (5 SP), US-29 (3 SP), **US-11 (3 SP)**, **US-12 (3 SP)** |
| **Sprint 2 Total** | **42 SP** | **0 SP** | **42 SP** | **11 Stories (Balanced distribution)** |

---

## 5. Repository Documentation Audit Trail

The following project documents have been updated to reflect this reassignment:
- `docs/requirements/traceability_matrix.md`: Updated Section 2 table (FR-07, FR-10), Section 4 ownership summary, and Section 5 revision log.
- `docs/SAD/Vehicle_Parking_System_SAD.md`: Updated Section 3.5 traceability mappings (FR-07, FR-10) and Section 7 revision table (v1.1.1).
- `scripts/generate_srs.js`: Updated FR-07 and FR-10 requirement metadata, product function table, Section 5.3 ownership narrative, and Appendix B.3 ownership matrix.
- `docs/requirements/Vehicle_Parking_System_SRS.docx`: Re-compiled from updated `scripts/generate_srs.js`.
- `docs/validation/DOCUMENT_ISSUE_AUDIT.md`: Updated Epic #16, US-11, US-12, FR-07, FR-10, Sprint 2 capacity breakdown, and added Section 12 reassignment addendum.
- `docs/validation/PHASE3_CORRECTION_REPORT.md`: Updated Sprint 2 milestone breakdown, FR-07/FR-10 master mapping, and added Section 10 reassignment addendum.
- `docs/meeting-notes/REASSIGNMENT_RECORD_MEMBER2_TO_MEMBER4.md`: Created as authoritative meeting and reassignment record.
