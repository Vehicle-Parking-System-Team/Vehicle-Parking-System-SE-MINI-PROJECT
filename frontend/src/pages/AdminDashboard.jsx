import { useEffect, useState } from 'react'
import { useAuth } from '../context/useAuth'
import { parseApiError } from '../utils/apiErrors'
import BayIcon from '../components/BayIcon'
import './AdminDashboard.css'

const money = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 2,
})
const clock = new Intl.DateTimeFormat('en-IN', {
  timeZone: 'Asia/Kolkata',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
})
const states = [
  ['available', 'Available'],
  ['occupied', 'Occupied'],
  ['reserved', 'Reserved'],
  ['maintenance', 'Maintenance'],
]

function Metric({ label, value, note, icon, accent = '' }) {
  return (
    <article className={`dashboard-metric ${accent}`}>
      <div>
        <span>{label}</span>
        <BayIcon name={icon} />
      </div>
      <strong>{value}</strong>
      <small>{note}</small>
    </article>
  )
}

function ActivityChart({ rows }) {
  const max = Math.max(
    4,
    ...rows.flatMap((row) => [row.arrivals, row.departures]),
  )
  const points = (key) =>
    rows
      .map((row) => `${38 + row.hour * 25},${168 - (row[key] / max) * 130}`)
      .join(' ')
  return (
    <svg
      viewBox="0 0 640 206"
      role="img"
      aria-label="Hourly arrivals and departures today. Exact values are in the hourly data table below."
    >
      {[0, 0.5, 1].map((tick) => (
        <g key={tick} className="dashboard-chart-grid">
          <line x1="38" x2="613" y1={168 - tick * 130} y2={168 - tick * 130} />
          <text x="25" y={172 - tick * 130} textAnchor="end">
            {Math.round(max * tick)}
          </text>
        </g>
      ))}
      <polyline points={points('arrivals')} className="dashboard-arrivals" />
      <polyline
        points={points('departures')}
        className="dashboard-departures"
      />
      {rows.map((row) => (
        <g key={row.hour}>
          <circle
            cx={38 + row.hour * 25}
            cy={168 - (row.arrivals / max) * 130}
            r="3"
            className="dashboard-arrival-point"
          >
            <title>
              {row.hour}:00 · {row.arrivals} arrivals
            </title>
          </circle>
          <circle
            cx={38 + row.hour * 25}
            cy={168 - (row.departures / max) * 130}
            r="3"
            className="dashboard-departure-point"
          >
            <title>
              {row.hour}:00 · {row.departures} departures
            </title>
          </circle>
        </g>
      ))}
      {[0, 4, 8, 12, 16, 20, 23].map((hour) => (
        <text key={hour} x={38 + hour * 25} y="195" textAnchor="middle">
          {String(hour).padStart(2, '0')}:00
        </text>
      ))}
    </svg>
  )
}

function RevenueChart({ rows, currentHour }) {
  const max = Math.max(1, ...rows.map((row) => Number(row.revenue)))
  return (
    <svg
      viewBox="0 0 640 206"
      role="img"
      aria-label="Collected revenue by payment hour today. Exact amounts are in the hourly data table below."
    >
      <line
        className="dashboard-chart-baseline"
        x1="28"
        x2="620"
        y1="168"
        y2="168"
      />
      {rows.map((row) => (
        <rect
          key={row.hour}
          x={30 + row.hour * 24.5}
          y={168 - (Number(row.revenue) / max) * 135}
          width="15"
          height={Math.max(
            row.hour > currentHour ? 2 : 3,
            (Number(row.revenue) / max) * 135,
          )}
          rx="3"
          className={
            row.hour > currentHour
              ? 'dashboard-future-bar'
              : 'dashboard-revenue-bar'
          }
        >
          <title>
            {row.hour}:00 ·{' '}
            {row.hour > currentHour ? 'Upcoming' : money.format(row.revenue)}
          </title>
        </rect>
      ))}
      {[0, 4, 8, 12, 16, 20, 23].map((hour) => (
        <text key={hour} x={37 + hour * 24.5} y="195" textAnchor="middle">
          {String(hour).padStart(2, '0')}:00
        </text>
      ))}
    </svg>
  )
}

export default function AdminDashboard() {
  const { fetchWithAuth } = useAuth()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [revision, setRevision] = useState(0)
  const [autoRefresh, setAutoRefresh] = useState(true)

  useEffect(() => {
    let ignore = false
    let pending = false
    const controller = new AbortController()
    async function load() {
      if (pending) return
      pending = true
      setLoading(true)
      try {
        const response = await fetchWithAuth('/api/reports/dashboard/', {
          cache: 'no-store',
          signal: controller.signal,
        })
        const body = await response.json()
        if (!response.ok) throw parseApiError(body)
        if (!ignore) {
          setData(body)
          setError(null)
        }
      } catch (failure) {
        if (!ignore)
          setError(failure.message || 'Dashboard could not be loaded.')
      } finally {
        pending = false
        if (!ignore) setLoading(false)
      }
    }
    load()
    const timer = autoRefresh
      ? setInterval(() => {
          if (!document.hidden) load()
        }, 30000)
      : null
    return () => {
      ignore = true
      controller.abort()
      clearInterval(timer)
    }
  }, [fetchWithAuth, revision, autoRefresh])

  const currentHour = data
    ? Number(
        new Intl.DateTimeFormat('en-GB', {
          timeZone: data.timezone,
          hour: '2-digit',
          hourCycle: 'h23',
        }).format(new Date(data.as_of)),
      )
    : 0
  const elapsedRows =
    data?.activity.filter((row) => row.hour <= currentHour) || []
  const busiest = elapsedRows.reduce(
    (peak, row) => (row.arrivals > (peak?.arrivals || 0) ? row : peak),
    null,
  )
  const estimates = data?.estimates

  return (
    <section className="admin-dashboard" aria-labelledby="dashboard-title">
      <div className="bay-page-heading dashboard-heading">
        <div>
          <span className="bay-eyebrow">THE BIG PICTURE</span>
          <h1 id="dashboard-title">
            Space in motion<span>.</span>
          </h1>
          <p>
            Your facility, at a glance. Every arrival. Every space. Every rupee.
          </p>
        </div>
        <div className="dashboard-controls">
          <button
            type="button"
            className="bay-button bay-button-primary"
            disabled={loading}
            onClick={() => setRevision((value) => value + 1)}
          >
            <BayIcon name="refresh" size={16} />
            {loading ? 'Refreshing…' : 'Refresh data'}
          </button>
          <label>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(event) => setAutoRefresh(event.target.checked)}
            />
            Auto-refresh · 30s
          </label>
        </div>
      </div>
      <div className="dashboard-update" role="status">
        <span className={`dashboard-status-dot ${error ? 'is-stale' : ''}`} />
        {data
          ? `${error ? 'Showing previous data' : 'Last updated'} · ${clock.format(new Date(data.as_of))} IST`
          : loading
            ? 'Loading facility metrics…'
            : 'Metrics unavailable'}
        <span>Asia/Kolkata</span>
      </div>
      {error && (
        <div className="bay-alert" role="alert">
          {error}{' '}
          {data
            ? 'Figures below may be out of date.'
            : 'Use Refresh data to retry.'}
        </div>
      )}
      {data && (
        <>
          <div className="dashboard-metrics" aria-label="Facility metrics">
            <Metric
              label="Occupancy"
              value={`${data.occupancy_percent}%`}
              note={`${data.slot_distribution.occupied} of ${data.total_slots} active slots`}
              icon="layers"
              accent="dashboard-olive"
            />
            <Metric
              label="Available spaces"
              value={data.free_slots}
              note="Ready for the next arrival"
              icon="map"
            />
            <Metric
              label="Active sessions"
              value={data.active_sessions}
              note="Currently open parking sessions"
              icon="car"
            />
            <Metric
              label="Collected today"
              value={money.format(data.today_revenue)}
              note="Paid receipts · since midnight IST"
              icon="bolt"
              accent="dashboard-blush"
            />
          </div>

          <div className="dashboard-main-grid">
            <article className="dashboard-panel dashboard-activity">
              <header>
                <div>
                  <span className="bay-eyebrow">DAILY RHYTHM</span>
                  <h2>Arrivals & departures</h2>
                </div>
                <span className="dashboard-period">Today · IST</span>
              </header>
              <div className="dashboard-flow-totals">
                <strong>
                  {data.arrivals_today}
                  <small>arrivals</small>
                </strong>
                <strong>
                  {data.departures_today}
                  <small>departures</small>
                </strong>
                <p>
                  {busiest
                    ? `Busiest arrival hour · ${String(busiest.hour).padStart(2, '0')}:00`
                    : 'No arrivals recorded today'}
                </p>
              </div>
              <ActivityChart rows={elapsedRows} />
              <div className="dashboard-legend">
                <span className="dashboard-key-arrivals">Arrivals</span>
                <span className="dashboard-key-departures">
                  Departures · dashed
                </span>
                <small>Current hour is partial</small>
              </div>
            </article>

            <article className="dashboard-panel dashboard-capacity">
              <header>
                <div>
                  <span className="bay-eyebrow">ROOM TO MOVE</span>
                  <h2>Space allocation</h2>
                </div>
                <BayIcon name="map" />
              </header>
              <div className="dashboard-capacity-number">
                <strong>{data.free_slots}</strong>
                <span>
                  spaces available
                  <br />
                  of {data.total_slots} active slots
                </span>
              </div>
              <div className="dashboard-capacity-track" aria-hidden="true">
                {states.map(([key]) => (
                  <span
                    key={key}
                    className={`dashboard-state-${key}`}
                    style={{ flexGrow: data.slot_distribution[key] }}
                  />
                ))}
              </div>
              <dl className="dashboard-distribution">
                {states.map(([key, label]) => (
                  <div key={key}>
                    <dt>
                      <i className={`dashboard-state-${key}`} />
                      {label}
                    </dt>
                    <dd>{data.slot_distribution[key]}</dd>
                  </div>
                ))}
              </dl>
              <p className="dashboard-note">
                Active slots in active zones. Reserved and maintenance spaces
                are excluded from availability.
              </p>
            </article>

            <article className="dashboard-panel dashboard-revenue">
              <header>
                <div>
                  <span className="bay-eyebrow">THE DAY IN VALUE</span>
                  <h2>Revenue pulse</h2>
                </div>
                <span className="dashboard-period">INR</span>
              </header>
              <div className="dashboard-revenue-total">
                {money.format(data.today_revenue)}
                <small>Collected today · by payment time</small>
              </div>
              <RevenueChart rows={data.activity} currentHour={currentHour} />
              <p className="dashboard-note">
                Paid receipts only. Pending payments and waivers are excluded.
                Pale marks indicate upcoming hours.
              </p>
            </article>

            <article className="dashboard-panel dashboard-outlook">
              <header>
                <div>
                  <span className="bay-eyebrow">A LOOK AHEAD</span>
                  <h2>Today's outlook</h2>
                </div>
                <span className="dashboard-estimate-badge">Estimates</span>
              </header>
              <div className="dashboard-estimate">
                <span>End-of-day collected revenue</span>
                <strong>
                  {estimates.end_of_day_revenue === null
                    ? 'Gathering data'
                    : money.format(estimates.end_of_day_revenue)}
                </strong>
                <p>
                  Today's collection pace × 24 hours. Available after 01:00 IST.
                </p>
              </div>
              <div className="dashboard-estimate">
                <span>Occupied slots in one hour</span>
                <strong>
                  {estimates.next_hour_occupied_slots}
                  <small> / {data.total_slots}</small>
                </strong>
                <p>
                  Current occupied + last 60 minutes' arrivals (
                  {estimates.recent_arrivals}) − departures (
                  {estimates.recent_departures}), capped at usable capacity.
                </p>
              </div>
              <p className="dashboard-note">
                Pace-based estimates assume recent activity continues. They do
                not account for future bookings, demand changes, or payment
                delays.
              </p>
            </article>
          </div>

          <div className="dashboard-secondary-metrics">
            <div>
              <BayIcon name="car" />
              <span>
                Average completed stay
                <strong>
                  {data.average_stay_minutes === null
                    ? 'No completed stays'
                    : `${data.average_stay_minutes} min`}
                </strong>
              </span>
            </div>
            <div>
              <BayIcon name="refresh" />
              <span>
                Today's slot turnover
                <strong>
                  {data.total_slots
                    ? `${(data.arrivals_today / data.total_slots).toFixed(2)}×`
                    : 'No active capacity'}
                </strong>
              </span>
            </div>
            <div>
              <BayIcon name="arrow" />
              <span>
                Net arrivals today
                <strong>
                  {data.arrivals_today - data.departures_today >= 0 ? '+' : ''}
                  {data.arrivals_today - data.departures_today} sessions
                </strong>
              </span>
            </div>
          </div>

          <article className="dashboard-panel">
            <header>
              <div>
                <span className="bay-eyebrow">ACROSS YOUR FACILITY</span>
                <h2>Zone overview</h2>
              </div>
              <span className="dashboard-period">
                {data.zones.length} active zones with slots
              </span>
            </header>
            {data.zones.length ? (
              <div className="dashboard-table-scroll">
                <table className="dashboard-table">
                  <caption className="dashboard-sr-only">
                    Current slot distribution by active zone
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">Zone</th>
                      <th scope="col">Occupancy</th>
                      {states.map(([key, label]) => (
                        <th scope="col" key={key}>
                          {label}
                        </th>
                      ))}
                      <th scope="col">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.zones.map((zone) => (
                      <tr key={zone.zone_id}>
                        <th scope="row">{zone.zone_name}</th>
                        <td>
                          <div className="dashboard-zone-meter">
                            <span
                              style={{
                                width: `${(zone.occupied / zone.total_slots) * 100}%`,
                              }}
                            />
                          </div>
                          {Math.round((zone.occupied / zone.total_slots) * 100)}
                          %
                        </td>
                        {states.map(([key]) => (
                          <td key={key}>{zone[key]}</td>
                        ))}
                        <td>{zone.total_slots}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="dashboard-empty">
                No active parking slots yet. Add zones and slots in Facility
                overview to start tracking capacity.
              </p>
            )}
          </article>
          <details className="dashboard-panel dashboard-hourly">
            <summary>
              Explore hourly data <span>Exact chart values · IST</span>
            </summary>
            <div className="dashboard-table-scroll">
              <table className="dashboard-table">
                <caption className="dashboard-sr-only">
                  Hourly activity and collected revenue, current hour partial
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Hour (IST)</th>
                    <th scope="col">Arrivals</th>
                    <th scope="col">Departures</th>
                    <th scope="col">Collected revenue</th>
                  </tr>
                </thead>
                <tbody>
                  {elapsedRows.map((row) => (
                    <tr key={row.hour}>
                      <th scope="row">
                        {String(row.hour).padStart(2, '0')}:00
                        {row.hour === currentHour ? ' · so far' : ''}
                      </th>
                      <td>{row.arrivals}</td>
                      <td>{row.departures}</td>
                      <td>{money.format(row.revenue)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
          <p className="dashboard-footnote">
            Activity covers all parking records; capacity covers active
            inventory. Turnover = today's arrivals ÷ active slots. Average stay
            uses sessions completed today. Counters refresh from current data.
          </p>
        </>
      )}
    </section>
  )
}
