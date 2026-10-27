# Software Architecture Document (SAD) — Vehicle Parking System

**Project:** Vehicle Parking System (SE Mini-Project)<br>
**Repository:** `Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT`<br>
**Document Version:** 1.2.0 (Implemented architecture snapshot)<br>
**Document Author / Architect:** Member 2 (Facility & Availability Architecture Lead)<br>
**Integration Lead & Scrum Master:** Member 1<br>
**Baseline Date:** October 2026; implementation snapshot 27 October 2026<br>
**Status:** Current implementation and planned architecture distinguished; synchronized with SRS/RTM v1.2.0 and the Sprint 1 test-plan addendum

---

## 1. Introduction

### 1.1 Purpose
This Software Architecture Document (SAD) provides a comprehensive architectural overview of the **Vehicle Parking System**. It captures the system's structural patterns, component responsibilities, data models, interface definitions, security controls, and runtime behaviors required to implement the 30 agreed Functional Requirements (`FR-01` to `FR-30`), 11 Non-Functional Requirements (`NFR-PERF-01..03`, `NFR-SAFE-01..03`, `NFR-SEC-01..07`), and 32 canonical User Stories (`US-01` to `US-32`).

### 1.2 Scope & System Boundaries
The Vehicle Parking System is a multi-tier, modular web application designed for automated parking facility operations. The core software scope encompasses:
- User registration, JWT-based authentication, and Role-Based Access Control (`Admin`, `Operator`, `Customer`).
- Vehicle registration, search, and historical session inspection.
- Parking slot and zone lifecycle management with real-time bay availability tracking.
- Advance parking reservation scheduling, conflict detection, and automated expiry release.
- Operator-driven vehicle check-in and check-out with automatic slot allocation and release.
- Anti-passback enforcement (single active session constraint per vehicle and per slot).
- Configurable tariff modeling, automated fee computation with a 15-minute grace period, and multi-method payment recording (`Cash`, `Card`, `UPI`).
- Digital parking slip and QR token issuance.
- Facility occupancy dashboards, administrative reporting with CSV/PDF exports, in-app notifications, and immutable security audit logging.

#### Explicit Out-of-Scope Enterprise Extensions
To maintain development integrity for the software engineering mini-project boundaries, physical site IoT hardware dependencies are formally decoupled from the application software layer:
- **Automated Physical Boom Barriers & Loop Detectors:** The core software workflow provides operator-driven verification and digital slips. Physical barrier relay hardware integrations are classified as post-MVP enterprise extensions.
- **Automated Number Plate Recognition (ANPR) Cameras:** Video feed optical character recognition (OCR) and camera hardware integrations are decoupled; operators capture or search license plates via web interfaces.
- **Third-Party Merchant Payment Gateway Production Integration:** Live commercial merchant banking (e.g., Razorpay/Stripe live webhooks) requires external corporate entity KYC. Core implementation operates with verified operator payment status recording.
- **Multi-Facility Distributed Federation & Offline Mesh Sync:** The application is architected as a centralized modular monolith backed by PostgreSQL; distributed edge replication is an enterprise roadmap proposal.

### 1.3 Target Audience
- **Software Engineers & Backend Developers:** To construct Django apps, DRF views, serializers, database migrations, and service-layer business rules.
- **Frontend Engineers:** To construct the React SPA, routing guards, state management, and operational dashboards.
- **Test & QA Engineers:** To map architectural components to test cases defined in the Software Test Plan (`TC-UCxx-...`).
- **Scrum Master & Integration Lead:** To track sprint backlog deliverables across Sprints 1 through 4.

### 1.4 Terminology & Definitions
- **Admin:** System administrator with full privileges to configure tariffs, manage user accounts, inspect audit trails, and oversee facility bays.
- **Operator:** Staff member operating entry/exit terminals, responsible for registering walk-in vehicles, checking vehicles in/out, verifying slips, and recording payments.
- **Customer:** Authenticated user with self-service privileges to view real-time occupancy, book advance reservations, view parking history, and manage personal profile.
- **Parking Bay / Slot:** An individual demarcated physical bay assigned a unique identifier, zone, floor, and vehicle class constraint (`Two-Wheeler`, `Compact`, `SUV`, `EV Charging`).
- **Active Session:** A parking session in progress where an allocated slot is `OCCUPIED` and the vehicle has checked in but not yet checked out.
- **Anti-Passback:** Validation rule preventing a vehicle from entering or being allocated a second slot while an active session exists (`FR-06`).
- **QR Token:** Digital session identifier encoded as a QR code and displayed on digital parking slips for rapid exit scanning (`FR-25`).

---

## 2. Document Governance & Canonical Traceability

This document supersedes all preliminary architectural drafts and aligns strictly with the project baseline:
1. **Software Requirements Specification (SRS v1.2.0):** Defines functional requirements `FR-01` to `FR-30` and decisions `DEC-01` to `DEC-15`.
2. **Requirements Traceability Matrix (RTM v1.2.0):** Maps all requirements to Epics E1–E8, Stories US-01–US-32, and Test Plan cases.
3. **Software Test Plan (v1.0):** Authoritative test cases `TC-UC01-UNIT-001` through `TC-SEC-002`.
4. **Live GitHub Backlog:** 8 Epics (#2, #15, #16, #17, #18, #19, #20, #21) and 32 User Stories (#1, #22–#52).

---

## 3. System Architecture

### 3.1 Architectural Goals & Quality Attributes

These are target qualities, not claims that all related functionality or NFRs have passed. Section 6 and the consistency report identify delivered scope and open gaps.
1. **Maintainability & Modular Separation:** Employ a clean Modular Monolith architecture on the backend, organizing code by functional domains (`accounts`, `vehicles`, `parking_slots`, `reservations`, `operations`, `billing`, `reports`, `common`, `notifications`).
2. **Strict Concurrency & ACID Integrity:** Enforce atomic transactional integrity during check-in, check-out, and reservation booking. Use database row-level locking (`select_for_update()`) to ensure zero double-booking under concurrent load (`NFR-PERF-02`, `NFR-SAFE-01..03`).
3. **Stateless Security:** Leverage JSON Web Tokens (JWT) with short-lived access tokens (15 min) and persistent refresh tokens (7 days) with server-side revocation on logout (`NFR-SEC-01`, `NFR-SEC-05`).
4. **Auditability & Traceability:** Maintain an append-only, immutable audit trail for administrative actions, security transitions, overrides, and cancellations (`NFR-SEC-07`).

### 3.2 Technology Stack
- **Frontend Client:** React 19, Vite 8, local CSS and Three.js; native browser fetch and React state/context navigation. No Tailwind, Axios or React Router dependency is declared.
- **Backend Application:** Python 3.12+ locally / 3.13 in CI, Django, DRF and SimpleJWT; exact supported dependency constraints are in `backend/requirements.txt`.
- **Database Engine:** PostgreSQL target (PostgreSQL 18 in integrity CI); SQLite fallback for local development and the general CI job.
- **Communication Protocol:** REST JSON using relative `/api` client requests. Vite proxies to local Django over HTTP. Production HTTPS/CORS acceptance is not established.

### 3.3 Architecture Overview Diagram

This diagram is the logical target architecture. Reservation, reporting, audit and notification components shown here are planned; see section 6 for the implemented module inventory.

```
+-----------------------------------------------------------------------------------+
|                           PRESENTATION LAYER (React SPA)                          |
|  +--------------------+  +---------------------+  +----------------------------+  |
|  | Operator Workspace |  |  Customer Portal    |  |  Admin Analytics Dashboard |  |
|  | (Entry/Exit/Slips) |  | (Reservations/Map)  |  |  (Tariff/Users/Audit Logs) |  |
|  +--------------------+  +---------------------+  +----------------------------+  |
|             |                       |                            |                |
|             +-----------------------+----------------------------+                |
|                                     | HTTP/REST (JSON + Bearer JWT)               |
+-------------------------------------v---------------------------------------------+
|                        APPLICATION / SERVICE LAYER (Django / DRF)                 |
|  +-----------------------------------------------------------------------------+  |
|  | API Gateway & Security: CORS, JWT Auth, Permission Guards (Admin/Oper/Cust) |  |
|  +-----------------------------------------------------------------------------+  |
|       |              |             |              |             |             |   |
|  +---------+   +----------+   +----------+   +----------+   +-------+   +-----+--+|
|  | Auth &  |   | Vehicle  |   |  Slots & |   | Reserv-  |   | Oper- |   | Billing||
|  | Users   |   | Mgmt     |   |  Zones   |   | ations   |   | ations|   | & Rates||
|  | (§3.4.2)|   | (§3.4.3) |   | (§3.4.4) |   | (§3.4.7) |   |§3.4.5)|   |(§3.4.6)||
|  +---------+   +----------+   +----------+   +----------+   +-------+   +-----+--+|
|       |              |             |              |             |             |   |
|  +-----------------------------------------------------------------------------+  |
|  | Cross-Cutting: Input Validation (§3.4.9), Audit Log, Exception Envelope     |  |
|  +-----------------------------------------------------------------------------+  |
+-------------------------------------v---------------------------------------------+
|                      PERSISTENCE & DATA LAYER (PostgreSQL 15+)                    |
|  +-----------------------------------------------------------------------------+  |
|  | Tables: users, vehicles, slots, reservations, records, tariffs, bills, audit|  |
|  | Constraints: Unique Active Slot, Unique Active Vehicle, Foreign Keys, ACID  |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

### 3.4 Component Descriptions & Module Architecture

#### 3.4.1 User Interface Component (React SPA)
- Renders authentication, vehicle registration/profile/search, Admin/Operator facility management and public read-only availability.
- Uses React state/context navigation, browser fetch, local CSS and a lazy Three.js facility scene.
- Stores the auth session in browser localStorage and manages token refresh in AuthContext.
- Check-in/checkout/slip, reservation, history/rates and executive admin/audit flows remain planned frontend work.

#### 3.4.2 Authentication & Authorization Module (`backend/accounts/`)
- Manages identity verification via JWT token pairs (`FR-15`).
- Enforces Role-Based Access Control (`Admin`, `Operator`, `Customer`) across DRF endpoints and React navigation (`FR-16`).
- Planned: admin user account administration to activate, suspend or deactivate (`FR-17`); no administration API exists yet.
- Planned: self-service profile updates and password change (`FR-18`); current auth returns profile information but has no change-password/profile-update route.
- Enforces public registration privilege safeguard: public registrations create `Customer` accounts only (`DEC-13`).

#### 3.4.3 Vehicle Management Module (`backend/vehicles/`)
- Registers vehicles with license plate, vehicle class (`Two-Wheeler`, `Compact`, `SUV`, `EV Charging`), and owner info (`FR-01`).
- Provides vehicle profile inspection and detail updates (`FR-02`).
- Provides instant search by license plate returning vehicle details and active parking status (`FR-11`).
- Enforces license plate format normalization (alphanumeric, uppercase, whitespace trimmed) and duplicate prevention.

#### 3.4.4 Parking Slot Allocation Engine (`backend/parking_slots/`)
- Manages slots and zones: add, modify properties, and deactivate bays (`FR-03`).
- Tracks real-time bay availability status: stored `available`, `occupied`, `maintenance`, `reserved` (`FR-04`, `DEC-02`).
- Enforces soft deactivation (`is_active=False`) for bays with historical session references (`DEC-03`, `BR-07`).
- Allocates an exact-class or legacy `any` available slot, with optional explicit `slot_id`. Candidate ordering is zone name, slot number, then primary key, not verified physical proximity. Nearest-slot and smaller-footprint/EV compatibility remain design gaps (`DEC-04`, `DEC-14`).
- Protects occupied or maintenance bays from duplicate assignment (`FR-07`).
- Powers public read-only availability (`GET /api/parking/availability/`), with zone/exact-type filtering and 30-second/manual client refresh (`FR-10`). It exposes no vehicle or owner identities. Management remains active Admin/Operator only.

#### 3.4.5 Parking Operations Module (`backend/operations/`)
- Orchestrates check-in: verifies active session uniqueness, assigns compatible slot, transitions bay to `OCCUPIED`, creates active `ParkingRecord`, and generates a signed ticket token returned in record JSON (`FR-05`); printable slip/QR image remains planned.
- Enforces anti-passback constraint: rejects check-in if vehicle already has an active session (`FR-06`, `BR-01`).
- Orchestrates check-out: locates active record, records check-out timestamp, transitions session to completed, and computes duration (`FR-08`).
- Automatically restores bay status to `AVAILABLE` upon checkout (`FR-09`, `BR-04`).
- Retains completed parking records and check-in/fee snapshots. `GET /api/parking/history/` provides paginated Admin/Operator access, with plate/vehicle/slot/date filters. This is application history, not an append-only security audit store (`FR-12`, BR-05).

#### 3.4.6 Billing & Pricing Module (`backend/rates/`; remaining billing planned)

The bullets below describe the target billing scope. Current code implements ParkingRate configuration and ordinary hourly/grace fee calculation only. `backend/billing/`, invoice/payment records, penalty application, receipt generation and QR images are absent.
- Configures vehicle-class tariff schedules: hourly base rates, initial flat-rate durations, and weekend multipliers (`FR-23`).
- Automated fee computation: evaluates 15-minute entry grace period (0 fee if exit <= 15 min), applies vehicle-class rate, and rounds up to next full hour (`FR-24`, `DEC-06`).
- Development baseline defaults: Two-Wheeler: ₹20/hr; Compact: ₹40/hr; SUV: ₹60/hr (`DEC-06`, `DEC-07`). Currency is `INR` (`₹`).
- Digital parking slip and QR token issuance: encodes `{sessionId, vehiclePlate, slotNumber, checkInTime, signature}` (`FR-25`, `DEC-08`).
- Payment transaction recording: records `Cash`, `Card`, or `UPI` method with operator confirmation and receipt issuance (`FR-26`, `DEC-07`).

#### 3.4.7 Reservation Module (`backend/reservations/`, planned)
- Advance reservation creation: allows customers to reserve a compatible bay up to 7 days ahead for a defined future window (`FR-19`, `DEC-15`).
- Prevents scheduling conflicts: rejects reservations where the bay is already committed for an overlapping window (`FR-20`).
- Reservation modification and cancellation: permits customer cancellation up to 1 hour prior to reservation start time (`FR-21`, `DEC-15`).
- Check-in integration & auto-expiry: links valid reservation to arriving check-in; unfulfilled reservations expire 15 minutes past start time and release bay (`FR-22`, `DEC-15`).

#### 3.4.8 Reporting & Analytics Module (`backend/reports/`, planned)
- Provides admin dashboard metrics: live occupancy rate, active session count, today's revenue, and bay turnover (`FR-27`).
- Historical reporting: generates occupancy, throughput, and revenue reports filtered by date range and vehicle class (`FR-28`).
- Export engine: exports structured reports in CSV and PDF formats (`FR-28`).

#### 3.4.9 Audit, Notifications & Common Component (`backend/common/`; notifications and audit planned)
- Server-side payload validation: validates all incoming client parameters, rejecting malformed input with HTTP 400 (`FR-13`, `NFR-SEC-03`).
- Uniform structured error responses: wraps errors in `{error, code, details}` schema (`FR-14`).
- Planned security & event audit logging: appends immutable log entries for user status changes, manual overrides, cancellations, and tariff updates; 90-day retention (`FR-29`, `DEC-12`).
- Planned in-app notification delivery: dispatches alerts for reservation confirmations, expiry warnings, and payment receipts (`FR-30`).

---

### 3.5 Traceability Matrix to Canonical System Requirements

The table below reconciles the architecture components with the canonical baseline:

| Req ID | Canonical Requirement Title | Epic & Story Mapping | Architectural Component | Planned Target File Paths | Test Plan Case ID |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FR-01** | Vehicle Registration | E2 / US-05 (#25) | Vehicle Management Module (§3.4.3) | `backend/vehicles/models.py`<br>`frontend/src/pages/Vehicles.jsx` | `TC-UC02-UNIT-001`<br>`TC-UC02-API-001` |
| **FR-02** | Vehicle Profile & Update | E2 / US-06 (#26) | Vehicle Management Module (§3.4.3) | `backend/vehicles/views.py`<br>`frontend/src/pages/Vehicles.jsx` | `TC-UC02-API-002` |
| **FR-03** | Slot & Zone Lifecycle | E3 / US-09 (#29) | Slot Allocation Engine (§3.4.4) | `backend/parking_slots/models.py`<br>`frontend/src/pages/Slots.jsx` | `TC-UC03-UNIT-001` |
| **FR-04** | Real-Time Slot State Management | E3 / US-10 (#30) | Slot Allocation Engine (§3.4.4) | `backend/parking_slots/services.py` | `TC-UC03-INT-001` |
| **FR-05** | Check-In & Slot Allocation | E5 / US-17 (#37) | Operations Module (§3.4.5) | `backend/operations/views.py` | `TC-UC05-UNIT-001`<br>`TC-UC05-INT-001` |
| **FR-06** | Single Active Session Constraint | E5 / US-18 (#38) | Operations Module (§3.4.5) | `backend/operations/services.py` | `TC-UC05-INT-002` |
| **FR-07** | Occupied Slot Protection | E3 / US-12 (#32) *(Owner: Member 4 [reassigned from Member 2])*<br>E5 / US-17 (#37) *(Owner: Member 3)* | Slot Engine & Operations (§3.4.4, §3.4.5) | `backend/operations/services.py` | `TC-UC03-SYS-002`<br>`TC-UC05-INT-001` |
| **FR-08** | Vehicle Check-Out Operations | E5 / US-19 (#39) | Operations Module (§3.4.5) | `backend/operations/views.py` | `TC-UC06-INT-001` |
| **FR-09** | Automatic Slot Release | E5 / US-19 (#39) | Operations Module (§3.4.5) | `backend/operations/services.py` | `TC-UC06-INT-002` |
| **FR-10** | Live Occupancy Dashboard | E3 / US-11 (#31) *(Owner: Member 4 [reassigned from Member 2])* | Slot Allocation Engine (§3.4.4) | `frontend/src/pages/Slots.jsx (read-only availability)` | `TC-UC03-SYS-002` |
| **FR-11** | Search Vehicle by License Plate | E2 / US-07 (#27) | Vehicle Management Module (§3.4.3) | `backend/vehicles/views.py`<br>`frontend/src/pages/Search.jsx` | `TC-UC02-API-001`<br>`TC-UC02-API-002` |
| **FR-12** | Persistent Parking History Trail | E5 / US-20 (#40) | Operations Module (§3.4.5) | `backend/operations/models.py`<br>`backend/operations/views.py (history API; frontend absent)` | `TC-UC06-SYS-001` |
| **FR-13** | Server-Side Input Validation | E2 / US-08 (#28)<br>E8 / US-31 (#51) | Common Validation Layer (§3.4.9) | `domain serializers` | `TC-UC10-API-001` |
| **FR-14** | Uniform Structured Error Responses | E2 / US-08 (#28)<br>E8 / US-31 (#51) | Common Exception Layer (§3.4.9) | `backend/common/exceptions.py` | `TC-UC10-API-001` |
| **FR-15** | User Authentication & Logout | E1 / US-01 (#1) | Security & IAM Module (§3.4.2) | `backend/accounts/views.py`<br>`frontend/src/context/AuthContext.jsx` | `TC-UC01-UNIT-001`<br>`TC-UC01-SYS-001` |
| **FR-16** | Role-Based Access Control (RBAC) | E1 / US-02 (#22) | Security & IAM Module (§3.4.2) | `backend/accounts/permissions.py`<br>`frontend/src/routes/ProtectedRoute.jsx` | `TC-UC01-API-002` |
| **FR-17** | User Account Administration | E1 / US-03 (#23) | Security & IAM Module (§3.4.2) | `backend/accounts/views.py` | `TC-UC04-API-001` |
| **FR-18** | Profile & Password Management | E1 / US-04 (#24) | Security & IAM Module (§3.4.2) | `backend/accounts/serializers.py`<br>`frontend/src/pages/Profile.jsx` | `TC-UC04-API-002`<br>`TC-UC04-SYS-001` |
| **FR-19** | Advance Reservation Scheduling | E4 / US-13 (#33) | Reservation Module (§3.4.7) | `backend/reservations/models.py`<br>`frontend/src/pages/Reservations.jsx` | `TC-UC04-API-001` |
| **FR-20** | Prevent Reservation Conflicts | E4 / US-15 (#35) | Reservation Module (§3.4.7) | `backend/reservations/services.py` | `TC-UC04-SYS-001` |
| **FR-21** | Modify or Cancel Reservation | E4 / US-14 (#34) | Reservation Module (§3.4.7) | `backend/reservations/views.py` | `TC-UC04-API-001` |
| **FR-22** | Link Reservation & Auto-Release | E4 / US-16 (#36) | Reservation Module (§3.4.7) | `backend/reservations/services.py` | `TC-UC04-SYS-001` |
| **FR-23** | Tariff Rate Configuration | E6 / US-21 (#41) | Billing & Pricing Module (§3.4.6) | `backend/rates/models.py` | `TC-UC07-UNIT-001` |
| **FR-24** | Automated Fee Computation | E6 / US-22 (#42) | Billing & Pricing Module (§3.4.6) | `backend/rates/calculations.py (ordinary fee); remaining billing planned` | `TC-UC07-API-002` |
| **FR-25** | Digital Slip & QR Token | E6 / US-23 (#43) | Billing & Pricing Module (§3.4.6) | `backend/rates/calculations.py (ordinary fee); remaining billing planned` | `TC-UC07-SYS-001` |
| **FR-26** | Payment Status Recording | E6 / US-24 (#44) | Billing & Pricing Module (§3.4.6) | `backend/billing/views.py` | `TC-UC08-SYS-001` |
| **FR-27** | Admin Dashboard Summary Metrics | E7 / US-25 (#45) | Reporting & Analytics (§3.4.8) | `frontend/src/pages/AdminDashboard.jsx` | `TC-UC08-API-001` |
| **FR-28** | Occupancy & Revenue Reports | E7 / US-26..28 (#46..48) | Reporting & Analytics (§3.4.8) | `backend/reports/views.py`<br>`frontend/src/pages/Reports.jsx` | `TC-UC08-API-002`<br>`TC-UC08-SYS-001` |
| **FR-29** | System Security Audit Log | E8 / US-29 (#49) | Common Audit Layer (§3.4.9) | `backend/common/models.py` | `TC-UC09-INT-001`<br>`TC-UC09-SYS-001` |
| **FR-30** | In-App Milestone Notifications | E8 / US-30 (#50) | Notification Module (§3.4.9) | `backend/notifications/models.py`<br>`frontend/src/components/Notifications.jsx` | `TC-UC09-SYS-002` |

---

## 4. System Design & Data Models

### 4.1 Relational Data Model (PostgreSQL Schema)

The domain data model is organized into cohesive Django app models with strict referential constraints:

The following legacy conceptual model includes planned entities and naming; it is not the current Django schema. `CustomUser` maps to `accounts.User`, `TariffRate` to `rates.ParkingRate`; planned Reservation/Invoice/AuditLog entities do not exist yet. The implemented subset follows below.

```mermaid
erDiagram
    User ||--o{ ParkingRecord : "operates"
    User ||--o{ Reservation : "creates"
    User ||--o{ AuditLog : "triggers"
    Vehicle ||--o{ ParkingRecord : "session_for"
    Vehicle ||--o{ Reservation : "booked_for"
    ParkingSlot ||--o{ ParkingRecord : "allocated_to"
    ParkingSlot ||--o{ Reservation : "held_by"
    ParkingRecord ||--o| ParkingInvoice : "generates"
    TariffRate ||--o{ ParkingInvoice : "computes_from"

    User {
        int id PK
        string username UK
        string email UK
        string password_hash
        string role "Admin | Operator | Customer"
        string status "active | suspended | deactivated"
        datetime created_at
    }

    Vehicle {
        int id PK
        string plate_number UK
        string vehicle_type "Two-Wheeler | Compact | SUV | EV Charging"
        string owner_name
        string owner_phone
        datetime created_at
    }

    ParkingSlot {
        int id PK
        string slot_number UK
        string zone
        int floor
        string slot_type "Two-Wheeler | Compact | SUV | EV Charging"
        string status "AVAILABLE | OCCUPIED | MAINTENANCE | RESERVED"
        boolean is_active
    }

    Reservation {
        int id PK
        int user_id FK
        int vehicle_id FK
        int slot_id FK
        datetime start_time
        datetime end_time
        string status "CONFIRMED | CHECKED_IN | CANCELLED | EXPIRED"
        datetime created_at
    }

    ParkingRecord {
        int id PK
        int vehicle_id FK
        int slot_id FK
        int operator_id FK
        datetime check_in_time
        datetime check_out_time
        string status "ACTIVE | COMPLETED"
        string ticket_qr_token UK
    }

    TariffRate {
        int id PK
        string vehicle_type UK
        decimal hourly_rate
        int grace_period_minutes
        boolean is_active
    }

    ParkingInvoice {
        int id PK
        int parking_record_id FK,UK
        int duration_hours
        decimal total_amount
        string payment_method "Cash | Card | UPI"
        string payment_status "PENDING | PAID | WAIVED"
        datetime paid_at
        string receipt_number UK
    }

    AuditLog {
        int id PK
        int user_id FK
        string event_type
        string ip_address
        jsonb action_details
        datetime timestamp
    }
```

### 4.2 Implemented data model and operational sequences

```mermaid
erDiagram
    User ||--o{ Vehicle : owns
    User o|--o{ ParkingRecord : operates
    ParkingZone ||--o{ ParkingSlot : contains
    Vehicle ||--o{ ParkingRecord : records
    ParkingSlot ||--o{ ParkingRecord : hosts
    ParkingRate {
        string vehicle_type UK
        decimal hourly_rate
        int grace_period_minutes
        decimal penalty_fee
    }
    ParkingRecord {
        int vehicle_id FK
        int slot_id FK
        string status "ACTIVE or COMPLETED"
        datetime check_in_time
        datetime check_out_time
        string ticket_qr_token UK
        decimal fee_amount
        decimal hourly_rate_snapshot
        int grace_period_minutes_snapshot
        string registration_number_snapshot
        string vehicle_type_at_checkin_snapshot
        string slot_number_snapshot
        string zone_name_snapshot
    }
```

ParkingRate is looked up by vehicle type rather than a ParkingRecord foreign key. Nullable snapshots preserve legacy rows without inventing historical values. ParkingSlot stores lowercase `available`, `occupied`, `maintenance`, `reserved`; ParkingRecord stores uppercase `ACTIVE`/`COMPLETED`. Bay numbers are unique per zone, not globally. Conditional unique constraints prevent multiple ACTIVE records for the same slot or vehicle.

#### 4.2.1 Check-in (`POST /api/parking/check-in/`)

An active Admin/Operator supplies `registration_number` and optional `slot_id`. The service normalizes the plate, locks the vehicle and candidate zone/slot rows, rejects an existing active record, checks availability/compatibility, and atomically occupies the bay and creates the record with check-in snapshots and a signed ticket token. It returns HTTP 201 record JSON. Full/no-compatible allocation returns 409; incompatible explicit selection uses 422. There is no scanner or printable slip UI.

#### 4.2.2 Checkout (`POST /api/parking/check-out/`)

An active Admin/Operator supplies `registration_number`; the serializer rejects extra inputs, including client-supplied fee/payment fields. The transaction locks the vehicle/active record and slot, finds the current configured rate, applies the inclusive configured grace period, then rounds the full elapsed duration up to whole hours outside grace. It saves fee/rate/grace/type snapshots, completes the record, and releases the slot atomically. It returns HTTP 200 with the calculated fee in INR. Duplicate checkout or release failure cannot partially commit fee/completion changes. Missing/invalid configuration fails safely. Payment status, payment method, invoice, penalties, receipts and scanned-token exit verification are not implemented.

#### 4.2.3 Completed history (`GET /api/parking/history/`)

An active Admin/Operator may read completed records with checkout timestamps. Page size defaults to 20, with a maximum of 100. Plate/vehicle/slot and check-in date filters are supported. Snapshot fields preserve completed-session identity when current vehicle/slot labels change. No dedicated frontend history view is implemented.

---

## 5. Security & Error Handling Architecture

### 5.1 Authentication, Tokens & Password Policies (`DEC-09`, `DEC-10`, `DEC-13`)
- **Access Tokens:** Stateless JWT with 15-minute lifetime containing `{user_id, username, role}`.
- **Refresh Tokens:** 7-day lifetime stored securely; refresh endpoint issues new access token.
- **Logout Invalidation:** Logout blacklists the refresh token and increments `User.token_version`; the custom JWT authenticator rejects previously issued access tokens immediately. Role/account checks remain enforced by owning endpoints.
- **Password Hashing:** Passwords hashed using Django default PBKDF2 with SHA-256 (`NFR-SEC-05`).
- **Complexity Enforcer:** Passwords must have >= 8 characters, >= 1 uppercase, >= 1 lowercase, >= 1 digit, >= 1 special character.
- **Privilege Safeguard:** Public registration creates `Customer` accounts only. Elevation to `Operator` or `Admin` requires an existing Administrator (`NFR-SEC-02`, `DEC-13`).

### 5.2 Standard Error Response Schema (`FR-14`)
DRF exceptions handled by `common.exceptions.exception_handler` use the shared contract. Explicit Response objects bypass the handler and require their own review; do not assume every future endpoint is automatically compliant.

```json
{
  "error": "The selected slot is unavailable.",
  "code": "CONFLICT",
  "details": {}
}
```

`error` is public-safe display text, `code` a stable machine value, and `details` preserves validation structure. HTTP status and DRF headers are preserved. Unexpected errors return generic `INTERNAL_ERROR` and sanitized diagnostic metadata, without raw exception messages or secrets. See [the full contract](../design/US31-error-contract.md) and [verification evidence](../testing/US31-test-evidence.md).

---

## 6. Implementation Target Status & Project Roadmap

### 6.1 Current implementation as of 27 October 2026

Application baseline: `c98346e7a219114a03f84a53cb2a0d017deb3315`.

| Component | Implemented scope | Remaining scope |
| --- | --- | --- |
| `backend/accounts/` | Customer registration, login/refresh/logout, current user, account/token checks | Full US-02/03/04 roles/admin/profile stories remain open |
| `backend/vehicles/` | Registration, profile update, plate search/current status | US-08 broader validation story remains open |
| `backend/parking_slots/` | Slot/zone CRUD, floor, guarded state transitions, public availability, concurrency safeguards | DEC-04/14 functionality gaps recorded below |
| `backend/operations/` | Check-in, checkout with ordinary fee, completed history, snapshots and active-record constraints | Scanner/receipt/payment flows and dedicated frontend operations/history views |
| `backend/rates/` | Rate configuration and ordinary hourly/grace calculation | Penalty application, advanced billing, invoices/payment recording |
| `backend/common/` | Shared DRF errors and sanitized diagnostic logging | Security audit domain is not implemented |
| `frontend/src/` | Auth, vehicles, search, management and public availability; React 19/CSS/Three.js | Reservations, operations forms, history, rates, executive reporting, audit and notifications |
| Reservations, reporting, audit and notifications | No corresponding application domains/routes | Remain planned, not scaffolded production features |

Current root routes are `/api/auth/`, `/api/v1/vehicles/` (plus `/api/vehicles/` registration alias), `/api/parking/`, and `/api/v1/rates/`. Existing design documents describe each delivered contract. Current-module presence is not proof of whole-story or NFR acceptance.

See [the Sprint 1 review](../meeting-notes/SPRINT1_REVIEW.md), [test-plan addendum](../testing/SPRINT1_TEST_SUMMARY.md) and [functional gap report](../validation/SPRINT1_DOCUMENT_SYNC.md). Planned DEC-04 nearest allocation, DEC-14 footprint/EV compatibility, QR images, exit scanning, invoices and payment workflows are not redefined as complete merely because partial implementations exist.

### 6.2 External Dependencies & Post-MVP Scope
1. **Commercial Production Tariff Rate Schedule (`FR-23`):** Production rate approval rests with facility management. The development baseline executes with nominal defaults (₹20 Two-Wheeler, ₹40 Compact, ₹60 SUV).
2. **Production Merchant Gateway Integration (`FR-26`):** Live merchant processing credentials depend on external banking KYC. Sprint implementation operates with operator-verified payment recording.
3. **Automated Barrier & ANPR Hardware (`SAD §1.2`):** Physical gate relays, inductive loop detectors, and OCR camera feeds are decoupled from the software engineering scope as future enterprise hardware proposals.

---

## 7. Document Revision History

| Version | Date | Author / Role | Changes Description |
| :--- | :--- | :--- | :--- |
| **1.0.0** | 19 Oct 2026 | Member 2 (Architecture Lead) | Initial SAD draft PDF export (`Vehicle_Parking_System_SAD (2) (1) (1).pdf`). |
| **1.1.0** | 19 Oct 2026 | Member 1 & Member 2 | Harmonized SAD markdown baseline: corrected §3.8 traceability to canonical FR-01..30, aligned roles to Admin/Operator/Customer, eliminated hardware assumptions, formalized DEC-01..15, and reconciled with SRS v1.1 and Test Plan v1.0. |
| **1.1.1** | 25 Oct 2026 | Member 1 (Integration Lead) | Documented story ownership reassignment: US-11 (#31, FR-10) and US-12 (#32, FR-07) transferred from Member 2 to Member 4 due to Member 2 workload/availability constraints; Member 2 retains US-09, US-10 (Done) and Epic E4 (US-13..16); Member 4 assumes US-11, US-12 alongside Epics E7 and E8. |
| **1.2.0** | 27 Oct 2026 | Project documentation maintenance | Recorded implemented domains, actual routes/schema/transactions, public privacy boundary, error envelope, evidence and remaining functional gaps; retained planned scope explicitly. |
