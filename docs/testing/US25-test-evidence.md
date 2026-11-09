# US-25 — Dashboard verification

Current integrated delivery: [documentation index](../README.md) and [final verification](../testing/FINAL_VERIFICATION_REPORT.md). The dated scope below records this story or sprint increment.
Executed 3 November 2026 against the merged US-27 and US-29 baseline on
`feature/US-25-admin-dashboard-metrics`. Contract:
[admin dashboard metrics](../design/US25-admin-dashboard.md).

## Automated checks

| Check | Result |
| --- | --- |
| Full backend regression, SQLite | 588 tests run; successful, 12 existing database/platform skips (265.648 seconds) |
| Reporting and audit modules, isolated PostgreSQL 18 | 97 tests passed, no skips (8.221 seconds) |
| Dashboard regressions | 14 tests in `reports.test_dashboard`, included in both runs |
| Django system check | No issues |
| Migration drift | `makemigrations --check --dry-run`: no changes |
| Frontend helper suite | 94 tests passed |
| Frontend lint | Passed; two existing set-state-in-effect warnings in Users/Profile |
| Production build | Passed; existing large Three.js scene chunk warning remains |
| Bandit, `backend/reports`, high severity | Passed, no high-severity findings |
| Whitespace check | `git diff --check` passed |

Commands (with a generated `DJANGO_SECRET_KEY`; PostgreSQL used a separate local
cluster/test database and generated credentials):

```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --verbosity 0
python manage.py test reports common.tests.test_audit --verbosity 1
python -m bandit -r backend/reports --severity-level high --quiet
npm test
npm run lint
npm run build
git diff --check
```

The PostgreSQL CI job now includes `reports`, retaining existing integrity,
concurrency and audit checks. Read PR checks for the latest hosted CI result.

## Acceptance and calculation coverage

`reports.test_dashboard.DashboardTests` covers empty inventory, distributions
and zone totals, inactive inventory, active-record precedence, actual check-in,
checkout and payment services followed by fresh reads, local-midnight and
captured-time boundaries, revenue reconciliation and large exact-cent totals,
hourly activity, valid/zero/invalid durations, revenue-estimate warm-up, bounded
next-hour estimates, anonymous/non-admin/disabled-admin denials, real bearer
authentication, no personal data, read-only behavior and seven data queries.

## Browser verification

Chrome review used an isolated SQLite preview database with generated sample
records and fresh temporary accounts. Preview fixtures, credentials, databases,
logs and screenshots are excluded from Git; no sample metrics ship in the UI.

- Checked desktop, tablet and narrow mobile layouts (measured CSS widths 1440,
  768, 376 and 320). Fixed the additional navigation item's overflow; navigation
  and data tables scroll within their containers. No whole-page horizontal
  overflow remained at 320px after the fix.
- Reviewed all chart, capacity, estimate, summary and zone panels. Verified
  expandable exact hourly values, manual refresh, paused automatic updates
  (update time remained unchanged across more than one refresh period), and
  admin navigation/default landing.
- Injected HTTP 503 for the local dashboard request: first-load failure showed
  an unavailable message and retry without metric cards; later failure retained
  previous figures with a stale-data warning. Normal retry restored the data
  and cleared the warning. Test interception and viewport overrides were cleared.

This is local browser smoke verification, not a committed browser automation
suite. Production load/SLA, independent accessibility certification and
statistical forecast accuracy have not been established. Estimates explicitly
describe their pace assumptions in both the API contract and interface.
