# Vehicle Parking System Final Verification Report

8 November 2026 | Version 2.0

The integrated application passes the complete PostgreSQL regression, frontend checks and the measured local acceptance targets. The report records actual executions on application commit `0c883054fc84897bf303c3b766b60e0152fac1e9`. Performance measurements include the vehicle-search batching refinement and source SHA-256 values in the raw report.

## Execution environment
The test host uses Windows-11-10.0.26300-SP0, 16 logical CPUs and 15.29 GiB physical memory. Python is 3.12.12; Django is 5.2.18; PostgreSQL is 18.1; Node is 22.19.0; npm is 10.9.3. Backend regression and performance tests use isolated temporary PostgreSQL databases on a dedicated loopback instance. Existing application data is unchanged. Test databases are removed after the runs.

## Regression and quality checks
| Check | Observed result |
| --- | --- |
| Complete backend regression | 611 passed; 0 failed; 0 skipped; 168.656 seconds; PostgreSQL |
| Frontend helper tests | 94 passed; 0 failed; 0 skipped |
| Frontend ESLint | Passed |
| Frontend production build | Passed |
| Django system check | Passed; zero issues |
| Migration drift check | Passed; no changes detected |
| Bandit 1.9.4 high severity | Zero high-severity findings; 14151 source lines inspected |

The raw regression report lists all 611 executed backend test IDs. The test catalogue maps 25 canonical functional/security acceptance families to those executable modules. PostgreSQL regression includes real lock/concurrency and rollback cases; these counts are separate from the HTTP performance races. Frontend helper tests and build do not represent a browser UAT execution.

## CRUD latency
The local standard-load profile uses four simultaneous client workers. Each of 100 cycles creates, reads, updates and deletes a parking slot through real authenticated HTTP requests. Five warm-up cycles are excluded. Each operation must have p95 below 500 ms, with valid success status codes.
| Operation | Samples | p50 ms | p95 ms | Maximum ms | Target | Result |
| --- | --- | --- | --- | --- | --- | --- |
| create | 100 | 60.242 | 82.803 | 86.395 | <500 ms | Passed |
| read | 100 | 55.178 | 77.108 | 81.313 | <500 ms | Passed |
| update | 100 | 73.524 | 90.438 | 113.026 | <500 ms | Passed |
| delete | 100 | 70.749 | 93.39 | 107.221 | <500 ms | Passed |

## Search and history at 100000 records
The fixture contains 100000 vehicles and 100000 completed parking sessions before the measurements. Each route has five warm-ups and 100 serial samples. The target is p95 below 200 ms. HTTP timings include authentication, database work, serialization and reading the complete response body, providing a stricter measurement than SQL execution alone.
| Scenario | Samples | p50 ms | p95 ms | Maximum ms | Result |
| --- | --- | --- | --- | --- | --- |
| exact_search | 100 | 62.064 | 83.84 | 87.058 | Passed |
| partial_search | 100 | 116.399 | 140.21 | 191.127 | Passed |
| history_page | 100 | 78.147 | 98.398 | 102.455 | Passed |
| filtered_history | 100 | 88.888 | 111.02 | 119.307 | Passed |

Partial search returns at most 50 results and preserves role scoping. Owners are joined and active sessions prefetched in batches. The dedicated regression test verifies three queries for serialization of a 25-vehicle result page. The measured partial-query input is KA-01-FA; exact lookup selects a fixture vehicle near the dataset midpoint. History uses page_size=20 with and without the selected plate filter.

## Fifty request consistency
Fifty client threads wait on a barrier and issue requests together. Latency is recorded, while the acceptance condition is transaction consistency and exactly one successful conflicting operation.
| Race | Observed HTTP counts | Expected outcome | Result |
| --- | --- | --- | --- |
| same_slot_50 | 409: 49, 201: 1 | 1 x 201; 49 x 409 | Passed |
| same_vehicle_50 | 409: 49, 201: 1 | 1 x 201; 49 x 409 | Passed |
| same_checkout_50 | 404: 49, 200: 1 | 1 x 200; 49 x 404 | Passed |

After all races the database has zero duplicate active slots, zero duplicate active vehicles and zero active records associated with available slots. Fault-injection regression tests separately verify full transaction rollback for checkout and slot operations.

## Security evidence
Role/ownership, account status, strong password, access/refresh revocation, safe error, CSRF/CORS and production redirect/cookie tests pass in the complete backend suite. Audit tests exercise current producers and application immutability; notification tests exercise recipient isolation, deduplication and dispatch failure isolation. Bandit findings are scoped to the configured high-severity scan. The independent GitHub security workflow runs the source and secret scans on the uploaded revision.

## Reproduction
From backend, configure a PostgreSQL account with test-database creation permission, install requirements-postgres.txt, and run python manage.py test --verbosity 2. From frontend run npm ci, npm test, npm run lint and npm run build.

From the repository root run python scripts/verify_acceptance.py --output docs/testing/reports/performance.json with DB_ENGINE, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST and DB_PORT configured. It creates a randomly named test database and never seeds DB_NAME. Keep the host otherwise idle during measured samples. p95 uses nearest rank ceil(0.95*N); failed statuses cause acceptance to fail and the command exits nonzero.

## Evidence interpretation
The results establish the listed local workload on the recorded host and database. They do not estimate public-network latency, TLS proxy overhead or a hosting service capacity. Certificate/proxy checks belong to deployment verification. Automated acceptance, submitted PR review and final team/instructor acceptance are recorded as distinct activities. The release design decisions describe the exact interfaces and policies used for demonstration.

## Evidence files
- [Performance raw samples and source hashes](reports/performance.json)
- [Regression test IDs and execution metadata](reports/regression.json)
- [Canonical test cases](TEST_CASES.md)
- [Requirements traceability](../requirements/traceability_matrix.md)
- [Team delivery register](../meeting-notes/DELIVERY_REGISTER.md)
- [Release design decisions](../design/RELEASE_DESIGN_DECISIONS.md)
