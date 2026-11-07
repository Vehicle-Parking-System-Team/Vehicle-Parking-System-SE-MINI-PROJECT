# Vehicle Parking System Test Cases

Version 2.0 | 8 November 2026

Each case is executed through the named automated regression modules. The module contains the detailed fixtures, assertions and negative variants. The full run and performance output are recorded in FINAL_VERIFICATION_REPORT.md.

## TC-AUTH-01
Requirements: FR-15.

Preconditions: Active user; valid and invalid credentials.

Procedure: Submit login then access protected identity and logout.

Expected result: Valid login works; invalid credentials and revoked sessions are denied.

Executable source: backend/accounts/tests/test_auth.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-AUTH-02
Requirements: FR-18 NFR-SEC-05.

Preconditions: Authenticated account with an existing token pair.

Procedure: Update profile; change password; retry old tokens.

Expected result: Profile persists; password is hashed; old access and refresh tokens are rejected.

Executable source: backend/accounts/tests/test_profile_password.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-SEC-01
Requirements: FR-16 FR-17 NFR-SEC-01 NFR-SEC-02.

Preconditions: Admin Operator and Customer accounts.

Procedure: Exercise role matrix and administrative account changes.

Expected result: Only permitted roles succeed; lifecycle and last-admin safeguards hold.

Executable source: backend/accounts/tests/test_rbac.py; backend/accounts/tests/test_user_management.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-VEH-01
Requirements: FR-01 FR-02 FR-13.

Preconditions: Authenticated vehicle owner.

Procedure: Register vehicle then read and update its profile.

Expected result: Normalized unique identity and ownership are preserved.

Executable source: backend/vehicles/tests/test_vehicle_registration.py; backend/vehicles/tests/test_vehicle_profile.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-VEH-02
Requirements: FR-13 FR-14.

Preconditions: Supported plate formats and duplicate variants.

Procedure: Submit valid malformed and concurrent duplicate registrations.

Expected result: Valid formats persist; invalid inputs return 400; duplicates return 409.

Executable source: backend/vehicles/tests/test_vehicle_validation.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-VEH-03
Requirements: FR-11.

Preconditions: Vehicle owners and active/completed sessions.

Procedure: Search exact and partial plates; serialize 25 search results.

Expected result: Live state and ownership are correct; partial result serialization uses three queries.

Executable source: backend/vehicles/tests/test_vehicle_search.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-SLOT-01
Requirements: FR-03 FR-04.

Preconditions: Active facility zone and compatible slot.

Procedure: Create update transition and remove eligible slot.

Expected result: Zone uniqueness and allowed state transitions are enforced.

Executable source: backend/parking_slots/tests.py; backend/parking_slots/test_services.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-SLOT-02
Requirements: FR-07 NFR-SAFE-01.

Preconditions: Slot with an active parking record.

Procedure: Attempt destructive changes and conflicting allocation.

Expected result: Active sessions retain their slot; conflicts are rejected atomically.

Executable source: backend/parking_slots/test_integrity.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-SLOT-03
Requirements: FR-10.

Preconditions: Public and authenticated availability requests.

Procedure: Read filtered availability and compare permitted fields.

Expected result: Slot/zone/type/state are shown without vehicle owner identity.

Executable source: backend/parking_slots/test_availability.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-RES-01
Requirements: FR-19.

Preconditions: Customer-owned vehicle and future compatible window.

Procedure: Create reservation with valid and invalid ownership/window.

Expected result: Valid reservation persists; incompatible ownership or times are rejected.

Executable source: backend/reservations/tests.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-RES-02
Requirements: FR-20 FR-21.

Preconditions: Existing confirmed reservations.

Procedure: Modify cancel and overlap reservations including buffer boundaries.

Expected result: Confirmed booking windows remain consistent and conflicts are rejected.

Executable source: backend/reservations/test_conflicts.py; backend/reservations/test_modification.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-RES-03
Requirements: FR-22.

Preconditions: Confirmed reservation and matching vehicle.

Procedure: Check in with reservation code and exercise invalid linkage.

Expected result: Valid reservation becomes Fulfilled and links to one parking session.

Executable source: backend/operations/test_reservation_checkin.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-OPS-01
Requirements: FR-05 FR-06 FR-25.

Preconditions: Registered vehicle and compatible available slot.

Procedure: Check in; inspect token and snapshots; attempt duplicate entry.

Expected result: One ACTIVE record and signed ticket are persisted with the occupied slot.

Executable source: backend/operations/tests.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-OPS-02
Requirements: FR-08 FR-09 FR-24.

Preconditions: Active session with configured tariff.

Procedure: Check out at grace and hourly boundaries; repeat checkout.

Expected result: Correct Decimal fee; record completes and slot releases once.

Executable source: backend/operations/test_checkout.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-OPS-03
Requirements: NFR-SAFE-03.

Preconditions: Safe fault-injection boundary in a transaction.

Procedure: Raise a persistence/release exception before transaction completion.

Expected result: Fee session and slot mutations roll back together.

Executable source: backend/operations/test_checkout.py; backend/parking_slots/test_integrity.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-OPS-04
Requirements: FR-12.

Preconditions: Completed sessions with historical snapshots.

Procedure: Read paginated/filtered history after changing current labels.

Expected result: Completed historical identity is retained with access controls.

Executable source: backend/operations/test_history.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-BILL-01
Requirements: FR-23 FR-24.

Preconditions: Vehicle class tariff and known durations.

Procedure: Configure rate and calculate grace/hour/multiplier cases.

Expected result: Configured rate and exact monetary rounding reconcile.

Executable source: backend/rates/tests.py; backend/rates/test_vehicle_multiplier.py; backend/operations/test_us22_fee_acceptance.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-BILL-02
Requirements: FR-25 FR-26.

Preconditions: Completed session with fee snapshots.

Procedure: Generate receipt twice; settle or waive; retry invalid transitions.

Expected result: Receipt and settlement are idempotent; amount mirrors and permissions hold.

Executable source: backend/billing/tests.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-REP-01
Requirements: FR-27 FR-28.

Preconditions: Known slots sessions and settlement records.

Procedure: Query dashboard occupancy and collected revenue by interval.

Expected result: Aggregates reconcile; Admin access is enforced.

Executable source: backend/reports/test_dashboard.py; backend/reports/tests.py; backend/reports/test_revenue.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-REP-02
Requirements: FR-28.

Preconditions: Known and empty report datasets.

Procedure: Export CSV/PDF; inspect filters headers snapshots and formula protection.

Expected result: Valid complete documents follow the same canonical report calculations.

Executable source: backend/reports/test_exports.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-AUD-01
Requirements: FR-29 NFR-SEC-07.

Preconditions: Authentication and domain event producers.

Procedure: Trigger events; read as Admin; attempt update/delete.

Expected result: Actor/time/resource snapshots persist; application mutation is rejected.

Executable source: backend/common/tests/test_audit.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-NOT-01
Requirements: FR-30.

Preconditions: Recipient accounts and full/checkout/expiry events.

Procedure: Produce events; inspect own inbox; dismiss; simulate dispatch error.

Expected result: Recipient scoping deduplication and best-effort dispatch hold.

Executable source: backend/notifications/tests.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-VAL-01
Requirements: FR-13 FR-14.

Preconditions: Validation conflict and unexpected exceptions.

Procedure: Exercise exception handler and frontend error helper.

Expected result: Stable error/code/details envelope preserves status and hides internals.

Executable source: backend/common/tests/test_exceptions.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-SEC-02
Requirements: NFR-SEC-04.

Preconditions: Production settings and allowed/disallowed origins.

Procedure: Exercise CORS CSRF HTTPS redirect and cookie configuration.

Expected result: Configured production controls match the origin and transport policy.

Executable source: backend/common/tests/test_security.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-SEC-03
Requirements: NFR-SEC-06.

Preconditions: SQL-like input and representative source tree.

Procedure: Exercise safe query input and run Bandit high-severity scan.

Expected result: Input stays data; scoped source scan has no high-severity findings.

Executable source: backend/common/tests/test_security.py; backend/vehicles/tests/test_vehicle_search.py.

Actual result: Passed in the complete PostgreSQL regression on 8 November 2026.

## TC-PERF-01
Scenario: CRUD latency.

Preconditions: Dedicated PostgreSQL test database and backend dependencies.

Procedure: Run 100 cycles with four concurrent workers and five warm-ups; compare each operation p95 with 500 ms.

Executable source: scripts/verify_acceptance.py.

Actual result: See the raw samples and computed acceptance flags in reports/performance.json and the final verification report.

## TC-PERF-02
Scenario: Concurrent allocation and checkout.

Preconditions: Dedicated PostgreSQL test database and backend dependencies.

Procedure: Run same-slot, same-vehicle and same-checkout races with 50 synchronized requests; assert one success and zero integrity violations.

Executable source: scripts/verify_acceptance.py.

Actual result: See the raw samples and computed acceptance flags in reports/performance.json and the final verification report.

## TC-PERF-03
Scenario: Search and history volume.

Preconditions: Dedicated PostgreSQL test database and backend dependencies.

Procedure: Seed 100000 vehicles and completed sessions; measure exact/partial search and paginated/filtered history against 200 ms.

Executable source: scripts/verify_acceptance.py.

Actual result: See the raw samples and computed acceptance flags in reports/performance.json and the final verification report.
