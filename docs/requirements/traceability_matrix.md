# Vehicle Parking System Requirements Traceability Matrix

Version 2.0 | 8 November 2026

The matrix links canonical requirements to delivered modules, assigned stories and executable acceptance cases. The delivery register records actual assignees, sprint allocation and original pull request authors.

## Functional traceability
| Requirement | Statement | Assigned stories | Module | Canonical cases | Evidence |
| --- | --- | --- | --- | --- | --- |
| FR-15 | The system shall securely authenticate users, issue JWT token pairs (access and refresh), and support secure logout. | US-01 (#1, Member 1) | backend/accounts | TC-AUTH-01 | Implemented; verified within documented design decisions |
| FR-16 | The system shall enforce Role-Based Access Control (RBAC) across Admin, Operator, and Customer roles. | US-02 (#22, Member 1) | backend/accounts | TC-SEC-01 | Implemented; verified within documented design decisions |
| FR-17 | The system shall allow administrators to manage user accounts and user statuses (active, suspended, deactivated). | US-03 (#23, Member 1) | backend/accounts | TC-SEC-01 | Implemented; verified within documented design decisions |
| FR-18 | The system shall allow users to inspect their profile, update personal contact details, and securely change passwords. | US-04 (#24, Member 1) | backend/accounts | TC-AUTH-02 | Implemented; verified within documented design decisions |
| FR-01 | The system shall allow an authorized user/operator to register a vehicle with plate number, vehicle type, and owner information. | US-05 (#25, Member 1) | backend/vehicles | TC-VEH-01 | Implemented; verified within documented design decisions |
| FR-02 | The system shall allow an authorized user/operator to view and update vehicle profile and registration details. | US-06 (#26, Member 1) | backend/vehicles | TC-VEH-01 | Implemented; verified within documented design decisions |
| FR-11 | The system shall allow authorized users/operators to search for a vehicle by license plate and inspect its current parking status. | US-07 (#27, Member 1) | backend/vehicles | TC-VEH-03 | Implemented; verified within documented design decisions |
| FR-03 | The system shall allow an authorized administrator/operator to add, modify, and deactivate parking slots and zones. | US-09 (#29, Member 2) | backend/parking_slots | TC-SLOT-01 | Implemented; verified within documented design decisions |
| FR-04 | The system shall maintain the real-time status of each parking slot (Available, Occupied, Maintenance). | US-10 (#30, Member 2) | backend/parking_slots | TC-SLOT-01 | Implemented; verified within documented design decisions |
| FR-07 | The system shall prevent an occupied or unavailable parking slot from being assigned to another vehicle. | US-12 (#32, Member 4); US-17 (#37, Member 3) | backend/parking_slots | TC-SLOT-02 | Implemented; verified within documented design decisions |
| FR-10 | The system shall provide a live parking occupancy status dashboard for operators and users. | US-11 (#31, Member 4) | backend/parking_slots | TC-SLOT-03 | Implemented; verified within documented design decisions |
| FR-19 | The system shall allow authorized users to create advance parking reservations with scheduled time windows. | US-13 (#33, Member 2) | backend/reservations | TC-RES-01 | Implemented; verified within documented design decisions |
| FR-20 | The system shall prevent reservation slot conflicts and overlapping schedule commitments. | US-15 (#35, Member 2) | backend/reservations | TC-RES-02 | Implemented; verified within documented design decisions |
| FR-21 | The system shall allow authorized users to modify or cancel an existing future reservation. | US-14 (#34, Member 2) | backend/reservations | TC-RES-02 | Implemented; verified within documented design decisions |
| FR-22 | The system shall link a valid reservation to vehicle check-in and automatically release unfulfilled reservations upon expiry. | US-16 (#36, Member 2) | backend/reservations | TC-RES-03 | Implemented; verified within documented design decisions |
| FR-05 | The system shall allow an operator to check in a vehicle and allocate an available compatible parking slot. | US-17 (#37, Member 3) | backend/operations | TC-OPS-01 | Implemented; verified within documented design decisions |
| FR-06 | The system shall enforce a single active parking session constraint per vehicle. | US-18 (#38, Member 3) | backend/operations | TC-OPS-01 | Implemented; verified within documented design decisions |
| FR-08 | The system shall allow an operator to check out a vehicle upon request or exit verification. | US-19 (#39, Member 3) | backend/operations | TC-OPS-02 | Implemented; verified within documented design decisions |
| FR-09 | The system shall automatically release the corresponding parking slot to Available upon vehicle check-out. | US-19 (#39, Member 3) | backend/operations | TC-OPS-02 | Implemented; verified within documented design decisions |
| FR-12 | The system shall maintain a persistent historical audit trail of completed parking sessions. | US-20 (#40, Member 3) | backend/operations | TC-OPS-04 | Implemented; verified within documented design decisions |
| FR-23 | The system shall allow administrators to configure parking tariff rates and pricing models by vehicle class. | US-21 (#41, Member 3) | backend/billing | TC-BILL-01 | Implemented; verified within documented design decisions |
| FR-24 | The system shall automatically calculate parking session duration and compute applicable parking fees. | US-22 (#42, Member 3) | backend/billing | TC-OPS-02, TC-BILL-01 | Implemented; verified within documented design decisions |
| FR-25 | The system shall issue a digital parking slip, generate a QR token upon check-in, and provide payment receipts. | US-23 (#43, Member 3) | backend/billing | TC-OPS-01, TC-BILL-02 | Implemented; verified within documented design decisions |
| FR-26 | The system shall record payment transactions and track payment status across supported methods (Cash, Card, UPI). | US-24 (#44, Member 3) | backend/billing | TC-BILL-02 | Implemented; verified within documented design decisions |
| FR-27 | The system shall provide an administrative dashboard displaying operational summary metrics. | US-25 (#45, Member 4) | backend/reports | TC-REP-01 | Implemented; verified within documented design decisions |
| FR-28 | The system shall generate occupancy, usage, and revenue reports with configurable date-range filtering and export capabilities. | US-26 (#46, Member 4); US-27 (#47, Member 4); US-28 (#48, Member 4) | backend/reports | TC-REP-01, TC-REP-02 | Implemented; verified within documented design decisions |
| FR-13 | The system shall validate all client-submitted input data on the server side before processing. | US-08 (#28, Member 1); US-31 (#51, Member 4) | backend/common | TC-VEH-01, TC-VEH-02, TC-VAL-01 | Implemented; verified within documented design decisions |
| FR-14 | The system shall return uniform structured error responses and standard HTTP status codes. | US-08 (#28, Member 1); US-31 (#51, Member 4) | backend/common | TC-VEH-02, TC-VAL-01 | Implemented; verified within documented design decisions |
| FR-29 | The system shall maintain a persistent audit log recording security events, administrative changes, and critical domain operations. | US-29 (#49, Member 4) | backend/common | TC-AUD-01 | Implemented; verified within documented design decisions |
| FR-30 | The system shall deliver in-app notifications for key parking and reservation lifecycle milestones. | US-30 (#50, Member 4) | backend/common | TC-NOT-01 | Implemented; verified within documented design decisions |

## Non functional traceability
| Requirement | Criterion | Cases | Evidence |
| --- | --- | --- | --- |
| NFR-PERF-01 | p95 below 500 ms for create/read/update/delete at four simultaneous workers; 100 samples per operation after five warm-up cycles. | TC-PERF-01 | Final verification report and raw performance/regression results |
| NFR-PERF-02 | 50 synchronized requests per race; exactly one allocation or checkout succeeds; zero duplicate active vehicles or slots. | TC-PERF-02 | Final verification report and raw performance/regression results |
| NFR-PERF-03 | p95 below 200 ms over 100000 vehicles and 100000 completed sessions; exact/partial search and paginated/filtered history measured separately. | TC-PERF-03 | Final verification report and raw performance/regression results |
| NFR-SAFE-01 | Zero simultaneous active records for one slot. | TC-PERF-02 | Final verification report and raw performance/regression results |
| NFR-SAFE-02 | Zero simultaneous active records for one vehicle. | TC-PERF-02 | Final verification report and raw performance/regression results |
| NFR-SAFE-03 | Fault-injection tests preserve record, fee and slot state after rollback. | TC-OPS-03 | Final verification report and raw performance/regression results |
| NFR-SEC-01 | All exercised unauthorized protected requests return 401 or 403. | TC-SEC-01 | Final verification report and raw performance/regression results |
| NFR-SEC-02 | All exercised non-admin account/tariff/report/audit mutations are denied. | TC-SEC-01 | Final verification report and raw performance/regression results |
| NFR-SEC-03 | Malformed payloads return 400 and field details; semantic slot incompatibility uses 422. | TC-VAL-01 | Final verification report and raw performance/regression results |
| NFR-SEC-04 | Production settings redirect HTTP to HTTPS, set Secure cookies and restrict origins; configuration tests verify these controls. Live TLS is checked at deployment. | TC-SEC-02 | Final verification report and raw performance/regression results |
| NFR-SEC-05 | Passwords use Django hashes; expired/revoked access and refresh tokens are rejected; secrets are supplied through environment variables. | TC-AUTH-02 | Final verification report and raw performance/regression results |
| NFR-SEC-06 | Parameterized ORM queries and React text rendering are verified by regression/source checks; scoped scans report tool and severity. | TC-SEC-03 | Final verification report and raw performance/regression results |
| NFR-SEC-07 | The current authentication, account, tariff, cancellation, override and settlement producers append actor/event/resource/time snapshots. | TC-AUD-01 | Final verification report and raw performance/regression results |

## Evidence and document references
- [SRS](Vehicle_Parking_System_SRS.md) defines requirements and measurable acceptance.
- [SAD](../SAD/Vehicle_Parking_System_SAD.md) defines components, API and design decisions.
- [Test catalogue](../testing/TEST_CASES.md) defines canonical cases.
- [Final verification](../testing/FINAL_VERIFICATION_REPORT.md) records observed results.
- [Delivery register](../meeting-notes/DELIVERY_REGISTER.md) records all 32 stories, points, sprint and ownership.
