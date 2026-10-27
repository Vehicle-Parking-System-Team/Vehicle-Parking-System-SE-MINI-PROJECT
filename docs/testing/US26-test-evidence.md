# US-26 occupancy report execution evidence

Issue: [#46](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/46).
Contract: [occupancy report API and calculation rules](../design/US26-occupancy-reports.md).
Executed locally on 27 October 2026 with merged US-02/US-22 base `03335a9`.
This records API verification; no report screen or browser/system acceptance is claimed.

## Environment and results

| Check | Environment / command | Observed result |
| --- | --- | --- |
| Django system check | Windows, Python 3.12.12, Django 5.2.18; `python manage.py check` | Pass; no issues |
| Occupancy API tests, SQLite | `python manage.py test reports --verbosity 1` | 22 passed; 0.205 seconds |
| Occupancy API tests, PostgreSQL | PostgreSQL 18, psycopg 3.3.6; same 22 tests | 22 passed; 0.379 seconds |
| Full backend regression, SQLite | `python manage.py test --verbosity 1` from `backend/` | 358 discovered; 349 passed, 9 PostgreSQL concurrency skips; 129.109 seconds |
| Python source scan | Bandit 1.9.4; `python -m bandit -r backend/reports --severity-level high` | Zero findings at every severity; no suppressions |
| Secret scan | Gitleaks 8.30.1; `gitleaks dir <source-snapshot> --redact --no-banner` | No detected leaks in tracked/proposed files; ignored local files and Git history excluded |
| US-26 CI, browser UI, load/performance acceptance | Not part of the local execution below | Read current PR checks separately; no UI or load acceptance in this increment |

Every Django run supplied a generated environment signing key. PostgreSQL used a
new isolated temporary cluster, a generated password and an ephemeral loopback
port. Django created/destroyed its test database, and the temporary server was
stopped afterward. Existing application databases were not used. Test durations
describe these local runs and do not establish request-latency or load targets.

The full regression includes merged US-02 and US-22 changes. The SQLite skips
are existing PostgreSQL concurrency cases; the PostgreSQL run above covers all
22 new report cases, not the complete parking concurrency suite. Sanitized
fault-injection logs are expected output from passing backend tests.

## Test inventory

All cases below are in `backend/reports/tests.py` and passed on SQLite and
PostgreSQL. They expand the Test Plan reporting scenario TC-UC08-API-002 without
claiming its planned UI/system scenario TC-UC08-SYS-001.

| Case | Method | Expected behavior |
| --- | --- | --- |
| TC-US26-001 | `test_hourly_utilization_uses_slot_time_and_exposes_baseline` | Known 45/30 minute overlaps yield 37.5%/25%; baseline and no-cache headers present |
| TC-US26-002 | `test_daily_grouping_splits_midnight_and_preserves_totals` | Midnight split preserves occupied minutes and entry count |
| TC-US26-003 | `test_default_daily_report_reconciles_with_hourly_totals` | Default daily totals equal hourly totals; duration-weighted 31.25% |
| TC-US26-004 | `test_sessions_are_clipped_to_requested_range` | Carry-in/out session contributes only requested overlap |
| TC-US26-005 | `test_inclusive_start_and_exclusive_end` | Boundary-touching intervals do not add occupied time |
| TC-US26-006 | `test_partial_hours_use_actual_requested_duration` | Partial buckets use 30/15 minute denominators |
| TC-US26-007 | `test_active_and_completed_sessions_stop_at_captured_now` | No activity or elapsed capacity beyond captured time |
| TC-US26-008 | `test_zero_activity_and_zero_capacity_return_zero_rows` | Empty zone retains buckets, returns zero values and no peaks |
| TC-US26-009 | `test_future_range_has_zero_observed_time` | Future periods have zero elapsed time |
| TC-US26-010 | `test_current_capacity_includes_inactive_and_maintenance_slots` | Disclosed current inventory remains the denominator |
| TC-US26-011 | `test_zone_filter_and_current_zone_attribution` | Zone filter and current slot-zone attribution agree |
| TC-US26-012 | `test_all_zones_include_empty_zone_without_n_plus_one_queries` | All zones included using two data queries |
| TC-US26-013 | `test_utc_offsets_convert_to_local_time` | UTC timestamps normalize to Asia/Kolkata |
| TC-US26-014 | `test_peak_hours_accumulate_across_dates_and_include_ties` | Peak usage accumulates across days; tie handling additionally covered in TC-US26-002 |
| TC-US26-015 | `test_invalid_filters_return_shared_validation_errors` | Reversed/equal ranges, malformed input, invalid interval/zone and excessive range return structured 400 |
| TC-US26-016 | `test_required_date_filters` | Missing start/end reported in validation details |
| TC-US26-017 | `test_unknown_zone_returns_application_not_found` | Structured 404 with `NOT_FOUND`, rather than accepting an unmatched route |
| TC-US26-018 | `test_result_limit_rejects_large_zone_period_products` | Oversized output rejected with structured 400 |
| TC-US26-019 | `test_unauthenticated_and_non_admin_access_is_denied` | Anonymous 401; Operator/Customer 403 |
| TC-US26-020 | `test_inactive_admin_is_denied` | Suspended/deactivated/inactive administrators denied |
| TC-US26-021 | `test_real_bearer_token_and_read_only_response` | Real administrator JWT succeeds; records unchanged; identity/ticket fields absent |
| TC-US26-022 | `test_write_methods_are_not_exposed` | POST returns 405 |

## Acceptance boundary

This increment supplies date/hour/zone reporting, peak-hour data, invalid-range
validation and zero-value records. The agreed current-inventory baseline is
explicit in the API. Exact historical capacity utilization cannot be inferred
without capacity/status history; current slot moves and inventory changes may
change a past report. There are no model changes, report UI, financial metrics,
exports, or changes to authentication/parking/billing services.

The implementation requires PR review before merge. The results above establish
local verification only; read current PR checks for CI results. No merge,
deployment or issue closure is claimed by this evidence file.
