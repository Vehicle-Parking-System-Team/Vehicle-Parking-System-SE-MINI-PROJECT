import { useState } from 'react'
import { useAuth } from '../context/useAuth'
import { parseApiError } from '../utils/apiErrors'

export default function ReportExport() {
  const { fetchWithAuth } = useAuth()
  const [report, setReport] = useState('logs')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function download(event) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const query = new URLSearchParams({ report })
    for (const [key, value] of form) if (value) query.set(key, value)
    setBusy(true)
    setError('')
    try {
      const response = await fetchWithAuth(`/api/reports/export/?${query}`, { cache: 'no-store' })
      if (!response.ok) throw parseApiError(await response.json())
      const url = URL.createObjectURL(await response.blob())
      const link = document.createElement('a')
      link.href = url
      link.download = `${report}.${form.get('export_format')}`
      link.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (failure) {
      setError(failure.message || 'Report could not be downloaded.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <details className="dashboard-panel report-export">
      <summary>Export reports · CSV / PDF</summary>
      <p className="dashboard-note">Asia/Kolkata dates, inclusive start and exclusive end. Logs use check-in time; revenue uses paid receipts by payment time. Occupancy uses current inventory.</p>
      <form className="report-export-form" onSubmit={download} aria-busy={busy}>
        <label>Report<select value={report} onChange={(event) => setReport(event.target.value)}>
          <option value="logs">Parking logs</option><option value="occupancy">Occupancy</option><option value="revenue">Collected revenue</option>
        </select></label>
        <label>Start date<input name="start" type="date" required /></label>
        <label>End date (exclusive)<input name="end" type="date" required /></label>
        {report !== 'revenue' ? <label>Zone ID (optional)<input name="zone" type="number" min="1" /></label> : null}
        {report === 'logs' ? <label>Session status<select name="status"><option value="">All</option><option>ACTIVE</option><option>COMPLETED</option></select></label> : null}
        {report !== 'occupancy' ? <label>Vehicle type<select name="vehicle_type"><option value="">All</option><option>Compact</option><option>SUV</option><option>Two-Wheeler</option><option>EV Charging</option></select></label> : null}
        {report === 'revenue' ? <label>Payment method<select name="payment_method"><option value="">All</option><option>Cash</option><option>Card</option><option>UPI</option></select></label> : null}
        {report !== 'logs' ? <label>Interval<select name="interval"><option value="day">Daily</option><option value="hour">Hourly</option></select></label> : null}
        <label>File format<select name="export_format"><option value="csv">CSV</option><option value="pdf">PDF (up to 10,000 rows)</option></select></label>
        <button className="bay-button bay-button-primary" disabled={busy}>{busy ? 'Preparing download…' : 'Download report'}</button>
      </form>
      {error ? <p className="bay-alert" role="alert">{error}</p> : null}
    </details>
  )
}
