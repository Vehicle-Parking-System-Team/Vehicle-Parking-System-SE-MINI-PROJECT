# Vehicle Parking System — Requirements Traceability Matrix (RTM)

**Project:** Vehicle Parking System (SE Mini-Project)  
**Repository:** Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT  
**Version:** 1.1.1 (Member 2 to Member 4 Reassignment)  
**Baseline Date:** October 2026 (Updated 25 October 2026)  
**Integration Lead & Scrum Master:** Member 1  
**Agile Traceability Pipeline:** Requirement (FR/NFR) → Epic / User Story (US) → Design (SAD) → Implementation (Code File) → Test Case (Software Test Plan) → Status

---

## 1. Traceability Principles & Backlog Alignment Notice

> [!NOTE]
> **Product Backlog State:** The project repository currently maintains 8 Epics (#2, #15, #16, #17, #18, #19, #20, #21) and 32 canonical User Stories (#1, #22–#52). In accordance with the agile project plan, 17 user stories are prioritized across active milestones (Sprint 1: 6 stories, 25 SP; Sprint 2: 11 stories, 42 SP), while the remaining 15 user stories (49 SP) remain in the product backlog allocated to subsequent sprints (Sprint 3 / Sprint 4). The matrix below reflects this verified baseline without artificially marking future backlog stories as absent or fabricated.

---

## 2. Functional Requirements Traceability Matrix

| Req ID | Requirement Description | User Story ID & GitHub Issue | Parent Epic | Owner | SAD Architecture Reference | Planned Implementation Target | Test Plan Case ID | Test Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FR-01** | Register vehicle with plate number, vehicle type, and owner information | US-05 (#25) | E2: Vehicle Management (#15) | Member 1 | docs/SAD/ §3.4.3 Vehicle Management | backend/vehicles/models.py<br>frontend/src/pages/Vehicles.jsx | TC-UC02-UNIT-001<br>TC-UC02-API-001 | Not Run |
| **FR-02** | View and update vehicle profile and registration details | US-06 (#26) | E2: Vehicle Management (#15) | Member 1 | docs/SAD/ §3.4.3 Vehicle Management | backend/vehicles/views.py<br>frontend/src/pages/Vehicles.jsx | TC-UC02-API-002 | Not Run |
| **FR-03** | Add, modify, and deactivate parking slots and zones | US-09 (#29) | E3: Parking Facility & Availability (#16) | Member 2 | docs/SAD/ §3.4.4 Slot Allocation Engine | backend/slots/models.py<br>frontend/src/pages/Slots.jsx | TC-UC03-UNIT-001 | Not Run |
| **FR-04** | Maintain real-time slot state (Available, Occupied, Maintenance) | US-10 (#30) | E3: Parking Facility & Availability (#16) | Member 2 | docs/SAD/ §3.4.4 Slot Allocation Engine | backend/slots/services.py | TC-UC03-INT-001 | Not Run |
| **FR-05** | Check-in vehicle and allocate an available compatible parking slot | US-17 (#37) | E5: Parking Operations (#18) | Member 3 | docs/SAD/ §3.4.5 Parking Operations | backend/operations/views.py | TC-UC05-UNIT-001<br>TC-UC05-INT-001 | Not Run |
| **FR-06** | Enforce single-active-session constraint per vehicle | US-18 (#38) | E5: Parking Operations (#18) | Member 3 | docs/SAD/ §3.4.5 Parking Operations | backend/operations/services.py | TC-UC05-INT-002 | Not Run |
| **FR-07** | Prevent assignment to occupied or unavailable parking slot | US-12 (#32)<br>US-17 (#37) | E3: Parking Facility (#16)<br>E5: Operations (#18) | Member 4 *(Reassigned from Member 2)*<br>Member 3 | docs/SAD/ §3.4.4, §3.4.5 | backend/operations/services.py | TC-UC03-SYS-002<br>TC-UC05-INT-001 | Not Run |
| **FR-08** | Check-out vehicle upon operator request or exit verification | US-19 (#39) | E5: Parking Operations (#18) | Member 3 | docs/SAD/ §3.4.5 Parking Operations | backend/operations/views.py | TC-UC06-INT-001 | Not Run |
| **FR-09** | Automatically release parking slot to Available upon checkout | US-19 (#39) | E5: Parking Operations (#18) | Member 3 | docs/SAD/ §3.4.5 Parking Operations | backend/operations/services.py | TC-UC06-INT-002 | Not Run |
| **FR-10** | Live parking occupancy status dashboard for operators and users | US-11 (#31) | E3: Parking Facility & Availability (#16) | Member 4 *(Reassigned from Member 2)* | docs/SAD/ §3.4.4 Slot Allocation Engine | frontend/src/pages/Dashboard.jsx | TC-UC03-SYS-002 | Not Run |
| **FR-11** | Search vehicle by license plate and inspect current parking status | US-07 (#27) | E2: Vehicle Management (#15) | Member 1 | docs/SAD/ §3.4.3 Vehicle Management | backend/vehicles/views.py<br>frontend/src/pages/Search.jsx | TC-UC02-API-001<br>TC-UC02-API-002 | Pass |
| **FR-12** | Maintain persistent historical audit trail of parking sessions | US-20 (#40) | E5: Parking Operations (#18) | Member 3 | docs/SAD/ §3.4.5 Parking Operations | backend/operations/models.py<br>frontend/src/pages/History.jsx | TC-UC06-SYS-001 | Not Run |
| **FR-13** | Backend data validation for all client-submitted payload fields | US-08 (#28)<br>US-31 (#51) | E2: Vehicle Mgmt (#15)<br>E8: System Admin (#21) | Member 1<br>Member 4 | docs/SAD/ §3.4.9, §4.5 Validation | backend/common/serializers.py | TC-UC10-API-001 | Not Run |
| **FR-14** | Uniform structured error messaging and standard HTTP error codes | US-08 (#28)<br>US-31 (#51) | E2: Vehicle Mgmt (#15)<br>E8: System Admin (#21) | Member 1<br>Member 4 | docs/SAD/ §3.4.9, §4.5 Validation | backend/common/exceptions.py | TC-UC10-API-001 | Not Run |
| **FR-15** | User authentication, token issuance, and secure logout | US-01 (#1) | E1: Identity & Access Management (#2) | Member 1 | docs/SAD/ §3.4.2 Auth, §3.9 Security | backend/accounts/views.py<br>frontend/src/context/AuthContext.jsx | TC-UC01-UNIT-001<br>TC-UC01-SYS-001 | Not Run |
| **FR-16** | Role-Based Access Control enforcement (Admin, Operator, Customer) | US-02 (#22) | E1: Identity & Access Management (#2) | Member 1 | docs/SAD/ §3.4.2 Auth, §3.9 Security | backend/accounts/permissions.py<br>frontend/src/routes/ProtectedRoute.jsx | TC-UC01-API-002 | Not Run |
| **FR-17** | Administrative management of user status (active, suspended, deactivated) | US-03 (#23) | E1: Identity & Access Management (#2) | Member 1 | docs/SAD/ §3.4.2 Auth, §3.9 Security | backend/accounts/views.py | TC-UC04-API-001 | Not Run |
| **FR-18** | User profile inspection, contact details update, and password change | US-04 (#24) | E1: Identity & Access Management (#2) | Member 1 | docs/SAD/ §3.4.2 Auth, §3.9 Security | backend/accounts/serializers.py<br>frontend/src/pages/Profile.jsx | TC-UC04-API-002<br>TC-UC04-SYS-001 | Not Run |
| **FR-19** | Advance parking reservation creation and scheduling | US-13 (#33) | E4: Reservation Management (#17) | Member 2 | docs/SAD/ §3.4.7 Reservation Module | backend/reservations/models.py<br>frontend/src/pages/Reservations.jsx | TC-UC04-API-001 | Not Run |
| **FR-20** | Prevent reservation conflicts and overlapping slot commitments | US-15 (#35) | E4: Reservation Management (#17) | Member 2 | docs/SAD/ §3.4.7 Reservation Module | backend/reservations/services.py | TC-UC04-SYS-001 | Not Run |
| **FR-21** | Modify or cancel an existing future reservation | US-14 (#34) | E4: Reservation Management (#17) | Member 2 | docs/SAD/ §3.4.7 Reservation Module | backend/reservations/views.py | TC-UC04-API-001 | Not Run |
| **FR-22** | Link valid reservation to check-in session and release upon expiry | US-16 (#36) | E4: Reservation Management (#17) | Member 2 | docs/SAD/ §3.4.7 Reservation Module | backend/reservations/services.py | TC-UC04-SYS-001 | Not Run |
| **FR-23** | Configure vehicle-class rates and parking tariff models | US-21 (#41) | E6: Pricing, Billing & Payment (#19) | Member 3 | docs/SAD/ §3.4.6 Billing & Pricing | backend/billing/models.py | TC-UC07-UNIT-001 | Not Run |
| **FR-24** | Automatic duration calculation and parking fee computation | US-22 (#42) | E6: Pricing, Billing & Payment (#19) | Member 3 | docs/SAD/ §3.4.6 Billing & Pricing | backend/billing/services.py | TC-UC07-API-002 | Not Run |
| **FR-25** | Digital parking slip issuance, QR token generation, and receipts | US-23 (#43) | E6: Pricing, Billing & Payment (#19) | Member 3 | docs/SAD/ §3.4.6 Billing & Pricing | backend/billing/services.py | TC-UC07-SYS-001 | Not Run |
| **FR-26** | Record payment transaction status (Cash, Card, UPI) | US-24 (#44) | E6: Pricing, Billing & Payment (#19) | Member 3 | docs/SAD/ §3.4.6 Billing & Pricing | backend/billing/views.py | TC-UC08-SYS-001 | Not Run |
| **FR-27** | Administrative dashboard summary metrics (occupancy, active sessions) | US-25 (#45) | E7: Admin Dashboard & Reporting (#20) | Member 4 | docs/SAD/ §3.4.8 Reporting & Analytics | frontend/src/pages/AdminDashboard.jsx | TC-UC08-API-001 | Not Run |
| **FR-28** | Occupancy, parking usage, and revenue reporting with date filters | US-26 (#46)<br>US-27 (#47)<br>US-28 (#48) | E7: Admin Dashboard & Reporting (#20) | Member 4 | docs/SAD/ §3.4.8 Reporting & Analytics | backend/reports/views.py<br>frontend/src/pages/Reports.jsx | TC-UC08-API-002<br>TC-UC08-SYS-001 | Not Run |
| **FR-29** | Persistent system audit log tracking security and domain events | US-29 (#49) | E8: Audit, Notifications & Quality (#21) | Member 4 | docs/SAD/ §3.4.9 Audit & Notifications | backend/common/models.py | TC-UC09-INT-001<br>TC-UC09-SYS-001 | Not Run |
| **FR-30** | In-app notification delivery for parking and reservation milestones | US-30 (#50) | E8: Audit, Notifications & Quality (#21) | Member 4 | docs/SAD/ §3.4.9 Audit & Notifications | backend/notifications/models.py<br>frontend/src/components/Notifications.jsx | TC-UC09-SYS-002 | Not Run |

---

## 3. Non-Functional Requirements Traceability Matrix (NFR)

| NFR ID | Category | Requirement Statement | Verification Strategy | Target Criteria | Traceable User Story | Test Plan Ref | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **NFR-PERF-01** | Performance | API interactive response time under standard load | Automated API benchmark tests | < 500ms p95 response time for CRUD endpoints | US-31 (#51) | TC-UC10-API-001 | Not Run |
| **NFR-PERF-02** | Concurrency | Concurrent check-in/out consistency without race conditions | Database transactions & isolation tests | ACID transactional consistency under 50+ concurrent requests | US-32 (#52) | TC-UC05-INT-002 | Not Run |
| **NFR-PERF-03** | Scalability | Search and history indexing remains responsive under growth | Indexed queries on license plate & timestamps | < 200ms query time on 100,000 records | US-07 (#27), US-20 (#40) | TC-UC02-API-001 | Pass |
| **NFR-SAFE-01** | Safety | Prevent multi-vehicle assignment to a single slot | Unique database constraints & model validations | 0 double-allocation violations | US-18 (#38) | TC-UC05-INT-002 | Not Run |
| **NFR-SAFE-02** | Safety | Prevent vehicle assignment to multiple active slots | Active session uniqueness validation | 0 duplicate active sessions | US-18 (#38) | TC-UC05-INT-002 | Not Run |
| **NFR-SAFE-03** | Safety | Atomic transaction rollback on partial check-in/out failure | transaction.atomic blocks in Django service layer | Zero partial or corrupted records on error | US-32 (#52) | TC-UC06-SYS-001 | Not Run |
| **NFR-SEC-01** | Security | Role-based permission enforcement on protected routes | DRF permission class tests & frontend router tests | 100% unauthorized requests return HTTP 401/403 | US-02 (#22), US-31 (#51) | TC-SEC-001 | Not Run |
| **NFR-SEC-02** | Security | Prevent privilege escalation by non-admin roles | Unit tests for admin-only endpoint protection | 0 unauthorized administrative actions | US-02 (#22), US-32 (#52) | TC-SEC-001 | Not Run |
| **NFR-SEC-03** | Security | Strict server-side payload validation | DRF serializer validation tests | Rejection of malformed input with HTTP 400 | US-31 (#51) | TC-UC10-API-001 | Not Run |
| **NFR-SEC-04** | Security | Transport Layer Security (HTTPS) and secure CORS origin policy | CI/CD configuration check & CORS whitelist | Restricted to trusted client origins | US-32 (#52) | TC-SEC-002 | Not Run |
| **NFR-SEC-05** | Security | Cryptographic password hashing (Argon2 / PBKDF2) & JWT expiry | Django password validation settings & token unit tests | Zero plain-text credentials stored or transmitted | US-01 (#1), US-04 (#24) | TC-SEC-002 | Not Run |
| **NFR-SEC-06** | Security | Cross-Site Scripting (XSS) and SQL Injection prevention | Django ORM parameterized queries & React sanitization | 0 injection vulnerabilities | US-32 (#52) | TC-SEC-001 | Not Run |
| **NFR-SEC-07** | Security | Audit logging of privileged actions and sensitive data changes | Audit trail verification tests | 100% privileged state modifications logged | US-29 (#49) | TC-UC09-INT-001 | Not Run |

---

## 4. Team Member Functional Ownership Summary

- **Member 1 (Scrum Master & Project Integration Lead):**  
  - *Assigned Epics:* Epic E1 (Identity & Access Management: #2) and Epic E2 (Vehicle Management: #15).  
  - *Assigned User Stories:* US-01 (#1), US-02 (#22), US-03 (#23), US-04 (#24), US-05 (#25), US-06 (#26), US-07 (#27), US-08 (#28).  
  - *Functional Scope:* Authentication, RBAC, user profiles, vehicle registration, profile updates, vehicle search, and duplicate handling.  
  - *Coordination:* SRS & RTM synchronization, Project Plan, Git workflow, Sprint Backlog tracking, Integration coordination.
- **Member 2:**  
  - *Assigned Epics:* Epic E3 (Parking Facility & Availability: #16 — US-09, US-10 Done; US-11, US-12 reassigned) and Epic E4 (Reservation Management: #17).  
  - *Assigned User Stories:* US-09 (#29, Done), US-10 (#30, Done), US-13 (#33), US-14 (#34), US-15 (#35), US-16 (#36). *(Historical: US-11 #31 and US-12 #32 transferred to Member 4 on 25 Oct 2026).*  
  - *Functional Scope:* Parking slots, zones, real-time slot states (completed); advance reservations, reservation modifications, conflict prevention, and hold expiry.
- **Member 3:**  
  - *Assigned Epics:* Epic E5 (Parking Operations: #18) and Epic E6 (Pricing, Billing & Payment: #19).  
  - *Assigned User Stories:* US-17 (#37), US-18 (#38), US-19 (#39), US-20 (#40), US-21 (#41), US-22 (#42), US-23 (#43), US-24 (#44).  
  - *Functional Scope:* Check-in, check-out, slot assignment, single-active-session enforcement, history retention, tariff configuration, fee calculation, digital parking slips, and payment recording.
- **Member 4:**  
  - *Assigned Epics:* Epic E7 (Admin Dashboard & Reporting: #20), Epic E8 (Audit, Notifications & Quality: #21), and Parking Facility & Availability reassigned stories US-11 (#31) and US-12 (#32) from Epic E3 (#16).  
  - *Assigned User Stories:* US-25 (#45), US-26 (#46), US-27 (#47), US-28 (#48), US-29 (#49), US-30 (#50), US-31 (#51), US-32 (#52), US-11 (#31, reassigned from Member 2), US-12 (#32, reassigned from Member 2).  
  - *Functional Scope:* Admin dashboard metrics, occupancy/revenue reports, CSV/PDF export, system audit logging, in-app notifications, centralized validation, security hardening, live occupancy dashboard (US-11), and slot integrity safeguards (US-12).
- **Cross-Cutting (All Members):**  
  - Unified error response schema ({error, code, details}), database transactional integrity, test suite execution, and CI/CD quality gates.

---

## 5. User Story Reassignment Changelog (25 October 2026)

| User Story ID & Issue | Story Title | Original Owner | New Owner | Effective Date | Reason | Requirements & Criteria | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **US-11 (#31)** | View current parking status | Member 2 (`tejasv5467`) | Member 4 (`maddox095`) | 25 Oct 2026 | Member 2 workload / availability; Member 4 assumes unfinished facility stories | FR-10; real-time occupancy status dashboard across zones; Sprint 2, 3 SP, Priority Medium | Ready / In Progress (Unchanged) |
| **US-12 (#32)** | Enforce slot integrity and destructive-operation rules | Member 2 (`tejasv5467`) | Member 4 (`maddox095`) | 25 Oct 2026 | Member 2 workload / availability; Member 4 assumes unfinished facility stories | FR-07, BR-12, NFR-SAFE-01; prevent assignment to occupied/unavailable slots; Sprint 2, 3 SP, Priority High | Ready / In Progress (Unchanged) |

