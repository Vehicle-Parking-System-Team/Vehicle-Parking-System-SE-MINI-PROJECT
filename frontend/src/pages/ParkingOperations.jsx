import { useRef, useState } from 'react'
import QRCode from 'qrcode'
import { useAuth } from '../context/useAuth'
import { parseApiError } from '../utils/apiErrors'
import { requestSlots } from '../utils/slots'
import './ParkingOperations.css'

async function request(fetchWithAuth, path, body) {
  const response = await fetchWithAuth(path, body === undefined ? { cache: 'no-store' } : {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const { message, fieldErrors, formErrors } = parseApiError(data)
    throw new Error([...Object.values(fieldErrors).flat(), ...formErrors].join(' ') || message)
  }
  if (!data) throw new Error('The parking service returned an empty response.')
  return data
}

function useOperation() {
  const running = useRef(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function run(action) {
    if (running.current) return
    running.current = true
    setBusy(true)
    setError('')
    try {
      await action()
    } catch (error) {
      setError(error.message)
    } finally {
      running.current = false
      setBusy(false)
    }
  }
  return { run, busy, error }
}

const dateTime = (value) => new Date(value).toLocaleString()
const money = (value, currency = 'INR') => new Intl.NumberFormat(undefined, {
  style: 'currency', currency,
}).format(value)

function duration(seconds) {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${hours}h ${minutes}m ${seconds % 60}s`
}

function EntryTicket({ record, qr }) {
  return (
    <article className="parking-result parking-entry-ticket" aria-label="Entry ticket">
      <h2>Entry ticket #{record.id}</h2>
      <p>{record.registration_number} · {record.vehicle_type}</p>
      <p>Bay {record.slot_number} · {record.zone_name}</p>
      <p>Entry time {dateTime(record.check_in_time)}</p>
      {qr ? <img src={qr} alt="Signed parking entry ticket QR code" width="220" height="220" /> : (
        <p>Signed ticket token <code>{record.ticket_qr_token}</code></p>
      )}
      <button type="button" onClick={() => window.print()}>Print entry ticket</button>
    </article>
  )
}

function CheckIn({ fetchWithAuth }) {
  const [plate, setPlate] = useState('')
  const [lookup, setLookup] = useState(null)
  const [mode, setMode] = useState('auto')
  const [bay, setBay] = useState('')
  const [reservation, setReservation] = useState('')
  const [record, setRecord] = useState(null)
  const [qr, setQr] = useState('')
  const { run, busy, error } = useOperation()

  function search(event) {
    event.preventDefault()
    setLookup(null)
    setRecord(null)
    setBay('')
    setReservation('')
    setMode('auto')
    run(async () => {
      const vehicle = await request(fetchWithAuth, `/api/v1/vehicles/by-plate/${encodeURIComponent(plate.trim())}/`)
      setLookup({ vehicle, slots: null })
    })
  }

  function changeMode(event) {
    const next = event.target.value
    setMode(next)
    if (next !== 'manual' || lookup.slots) return
    run(async () => {
      const slots = await requestSlots(fetchWithAuth, '?status=available')
      const type = lookup.vehicle.vehicle_type.trim().toLowerCase()
      setLookup({
        ...lookup,
        slots: (slots.results ?? slots).filter((slot) =>
          slot.is_active && slot.zone_is_active &&
          ['any', type].includes(slot.vehicle_type.trim().toLowerCase())),
      })
    })
  }

  function checkIn(event) {
    event.preventDefault()
    run(async () => {
      const body = { registration_number: lookup.vehicle.registration_number }
      if (mode === 'manual') body.slot_id = Number(bay)
      if (mode === 'reservation') body.reservation_code = reservation.trim().toUpperCase()
      const data = await request(fetchWithAuth, '/api/parking/check-in/', body)
      setLookup(null)
      setQr('')
      setRecord(data)
      if (data.ticket_qr_token) {
        const image = await QRCode.toDataURL(data.ticket_qr_token, { width: 264 }).catch(() => '')
        setQr(image)
      }
    })
  }

  return (
    <>
      <form className="parking-form" onSubmit={search}>
        <fieldset disabled={busy}>
          <label>Vehicle plate<input value={plate} onChange={(event) => {
            setPlate(event.target.value)
            setLookup(null)
          }} maxLength={20} required /></label>
          <button>Find vehicle</button>
        </fieldset>
      </form>
      {lookup && (
        <form className="parking-form" onSubmit={checkIn}>
          <h2>{lookup.vehicle.registration_number} · {lookup.vehicle.vehicle_type}</h2>
          <fieldset disabled={busy}>
            <label>Allocation<select value={mode} onChange={changeMode}>
              <option value="auto">Automatic</option>
              <option value="manual">Choose a bay</option>
              <option value="reservation">Redeem reservation</option>
            </select></label>
            {mode === 'manual' && (
              <label>Compatible bay<select value={bay} required onChange={(event) => setBay(event.target.value)}>
                <option value="">{lookup.slots?.length === 0 ? 'No compatible bays available' : 'Select a bay'}</option>
                {lookup.slots?.map((slot) => (
                  <option key={slot.id} value={slot.id}>{slot.zone_name} · {slot.slot_number}</option>
                ))}
              </select></label>
            )}
            {mode === 'reservation' && (
              <label>Reservation code<input value={reservation} onChange={(event) => setReservation(event.target.value)} maxLength={32} required /></label>
            )}
            <button disabled={mode === 'manual' && !bay}>Check in</button>
          </fieldset>
        </form>
      )}
      {busy && <p role="status">Working…</p>}
      {error && <p role="alert">{error}</p>}
      {record && <EntryTicket record={record} qr={qr} />}
    </>
  )
}

function Checkout({ fetchWithAuth }) {
  const [field, setField] = useState('registration_number')
  const [query, setQuery] = useState('')
  const [preview, setPreview] = useState(null)
  const [receipt, setReceipt] = useState(null)
  const { run, busy, error } = useOperation()

  function search(event) {
    event.preventDefault()
    setPreview(null)
    setReceipt(null)
    run(async () => {
      const params = new URLSearchParams({ [field]: query.trim() })
      setPreview(await request(fetchWithAuth, `/api/parking/check-out/?${params}`))
    })
  }

  function checkout() {
    run(async () => {
      const result = await request(fetchWithAuth, '/api/parking/check-out/', {
        registration_number: preview.registration_number,
        expected_record_id: preview.id,
      })
      setReceipt(result.receipt)
      setPreview(null)
    })
  }

  return (
    <>
      <form className="parking-form" onSubmit={search}>
        <fieldset disabled={busy}>
          <label>Search by<select value={field} onChange={(event) => {
            setField(event.target.value)
            setQuery('')
            setPreview(null)
          }}>
            <option value="registration_number">Vehicle plate</option>
            <option value="slot_number">Bay number</option>
          </select></label>
          <label>{field === 'slot_number' ? 'Bay number' : 'Vehicle plate'}
            <input value={query} onChange={(event) => {
              setQuery(event.target.value)
              setPreview(null)
            }} maxLength={field === 'slot_number' ? 30 : 20} required />
          </label>
          <button>Find active session</button>
        </fieldset>
      </form>
      {busy && <p role="status">Working…</p>}
      {error && <p role="alert">{error}</p>}
      {preview && (
        <article className="parking-result">
          <h2>{preview.registration_number} · Bay {preview.slot_number}</h2>
          <p>{preview.zone_name} · Entered {dateTime(preview.check_in_time)}</p>
          <p>{duration(preview.duration_seconds)} elapsed · {preview.billable_hours} billable hours</p>
          <p>{money(preview.hourly_rate, preview.currency)}/hour · {preview.vehicle_multiplier}× multiplier · {preview.grace_period_minutes} min grace</p>
          <p>Estimated fee <strong>{money(preview.fee_amount, preview.currency)}</strong>. The final fee is calculated at checkout.</p>
          <button type="button" disabled={busy} onClick={checkout}>Complete checkout</button>
        </article>
      )}
      {receipt && (
        <article className="parking-result">
          <h2>Checkout complete · Receipt {receipt.invoice_number}</h2>
          <p>Bay {receipt.slot_number} released · {receipt.registration_number}</p>
          <p>Receipt reference <code>{receipt.receipt_id}</code></p>
          <p>{receipt.duration_display} parked · {receipt.billable_hours} billable hours</p>
          <dl>
            <dt>Hourly rate</dt><dd>{money(receipt.hourly_rate, receipt.currency)}</dd>
            <dt>Base amount</dt><dd>{money(receipt.base_amount, receipt.currency)}</dd>
            <dt>Multiplier adjustment</dt><dd>{money(receipt.multiplier_adjustment, receipt.currency)}</dd>
            <dt>Total</dt><dd>{money(receipt.total_fee, receipt.currency)}</dd>
            <dt>Payment status</dt><dd>{receipt.payment_status}</dd>
          </dl>
        </article>
      )}
    </>
  )
}

function History({ fetchWithAuth }) {
  const [result, setResult] = useState(null)
  const [applied, setApplied] = useState('')
  const [page, setPage] = useState(1)
  const { run, busy, error } = useOperation()

  function load(filters, target) {
    run(async () => {
      const params = new URLSearchParams(filters)
      params.set('page', target)
      const data = await request(fetchWithAuth, `/api/parking/history/?${params}`)
      setResult(data)
      setPage(target)
      setApplied(filters)
    })
  }

  function filter(event) {
    event.preventDefault()
    const params = new URLSearchParams()
    for (const [key, value] of new FormData(event.currentTarget)) {
      if (value.trim()) params.set(key, value.trim())
    }
    setResult(null)
    load(params.toString(), 1)
  }

  return (
    <>
      <form className="parking-form" onSubmit={filter}>
        <fieldset disabled={busy}>
          <label>Vehicle plate<input name="registration_number" maxLength={20} /></label>
          <label>Vehicle ID<input name="vehicle_id" type="number" min="1" /></label>
          <label>Bay ID<input name="slot_id" type="number" min="1" /></label>
          <label>Check-in from<input name="start_date" type="date" /></label>
          <label>Check-in through<input name="end_date" type="date" /></label>
          <button>Load history</button>
        </fieldset>
      </form>
      {busy && <p role="status">Loading sessions…</p>}
      {error && <p role="alert">{error}</p>}
      {result?.count === 0 && <p>No completed sessions match these filters.</p>}
      {result?.count > 0 && (
        <div className="parking-result parking-history">
          <table>
            <caption>{result.count} matching completed sessions</caption>
            <thead><tr>
              <th scope="col">Session</th><th scope="col">Plate</th><th scope="col">Bay</th>
              <th scope="col">Check-in</th><th scope="col">Checkout</th>
              <th scope="col">Fee</th><th scope="col">Payment</th>
            </tr></thead>
            <tbody>{result.results.map((row) => (
              <tr key={row.id}>
                <td>{row.id}</td><td>{row.registration_number}</td><td>{row.zone_name} · {row.slot_number}</td>
                <td>{dateTime(row.check_in_time)}</td><td>{dateTime(row.check_out_time)}</td>
                <td>{row.fee_amount == null ? '—' : money(row.fee_amount)}</td><td>{row.payment_status}</td>
              </tr>
            ))}</tbody>
          </table>
          <nav aria-label="History pages">
            <button disabled={busy || !result.previous} onClick={() => load(applied, page - 1)}>Previous</button>
            <span>Page {page}</span>
            <button disabled={busy || !result.next} onClick={() => load(applied, page + 1)}>Next</button>
          </nav>
        </div>
      )}
    </>
  )
}

const screens = {
  'check-in': ['Staff check-in', CheckIn],
  'check-out': ['Staff checkout', Checkout],
  'parking-history': ['Parking session history', History],
}

export default function ParkingOperations({ page }) {
  const { fetchWithAuth } = useAuth()
  const [title, Screen] = screens[page]
  return (
    <section className="parking-operations">
      <header className="bay-page-heading"><h1>{title}</h1></header>
      <Screen fetchWithAuth={fetchWithAuth} />
    </section>
  )
}
