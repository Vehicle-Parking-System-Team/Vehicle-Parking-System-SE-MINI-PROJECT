import { lazy, Suspense, useEffect, useMemo, useState } from 'react'
import { useAuth } from '../context/useAuth'
import { requestSlots } from '../utils/slots'
import {
  buildFloorLayout,
  floorCode,
  floorLabel,
  slotState,
  STATUS,
  summarizeSlots,
} from '../utils/parkingLayout'
import { DEMO_SLOTS } from '../data/demoSlots'
import BayIcon from '../components/BayIcon'
import SlotEditor from '../components/SlotEditor'
import './Slots.css'

const ParkingScene = lazy(() => import('../components/ParkingScene'))

function StatusBadge({ slot }) {
  const state = slotState(slot)
  return (
    <span className={`bay-status bay-status-${state.toLowerCase()}`}>
      <i />
      {STATUS[state]?.label || state}
    </span>
  )
}

export default function SlotsPage() {
  const { fetchWithAuth } = useAuth()
  const [liveSlots, setLiveSlots] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [revision, setRevision] = useState(0)
  const [loadedAt, setLoadedAt] = useState(null)
  const [demo, setDemo] = useState(false)
  const [floor, setFloor] = useState(0)
  const [selectedId, setSelectedId] = useState(null)
  const [mode, setMode] = useState('3d')
  const [view, setView] = useState('perspective')
  const [resetKey, setResetKey] = useState(0)
  const [query, setQuery] = useState('')
  const [rendererError, setRendererError] = useState('')
  const [editor, setEditor] = useState(null)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    let ignore = false
    requestSlots(fetchWithAuth)
      .then((data) => {
        if (!Array.isArray(data))
          throw new Error('The slot list could not be read.')
        if (!ignore) {
          setLiveSlots(data)
          setLoadedAt(new Date())
        }
      })
      .catch((failure) => {
        if (!ignore) setError(failure)
      })
      .finally(() => {
        if (!ignore) setLoading(false)
      })
    return () => {
      ignore = true
    }
  }, [fetchWithAuth, revision])

  const { floors, activeFloor, floorSlots, layout, stats } = useMemo(() => {
    const source = demo ? DEMO_SLOTS : liveSlots
    const floors = [...new Set(source.map((slot) => slot.floor))].sort(
      (a, b) => (a === null ? 1 : b === null ? -1 : a - b),
    )
    const activeFloor = floors.includes(floor)
      ? floor
      : floors.length
        ? floors[0]
        : 0
    const floorSlots = source.filter((slot) => slot.floor === activeFloor)
    return {
      floors,
      activeFloor,
      floorSlots,
      layout: buildFloorLayout(floorSlots),
      stats: summarizeSlots(floorSlots),
    }
  }, [demo, liveSlots, floor])
  const selected = floorSlots.find((slot) => slot.id === selectedId)
  const filtered = floorSlots.filter((slot) =>
    `${slot.slot_number} ${slot.zone_name} ${slot.vehicle_type}`
      .toLowerCase()
      .includes(query.toLowerCase().trim()),
  )
  const occupiedPercent = stats.total
    ? Math.round((stats.OCCUPIED / stats.total) * 100)
    : 0
  const otherCount = stats.RESERVED + stats.MAINTENANCE + stats.INACTIVE

  function refresh() {
    setLoading(true)
    setError(null)
    setMessage('')
    setRevision((value) => value + 1)
  }

  function switchData() {
    setDemo((value) => !value)
    setSelectedId(null)
    setQuery('')
    setMessage('')
  }

  function savedSlot(slot) {
    setLiveSlots((current) =>
      current.some((item) => item.id === slot.id)
        ? current.map((item) => (item.id === slot.id ? slot : item))
        : [...current, slot],
    )
    setFloor(slot.floor)
    setSelectedId(slot.id)
    setEditor(null)
    setMessage(`Slot ${slot.slot_number} saved.`)
  }

  async function updateSelected(action) {
    if (!selected || demo || saving) return
    setSaving(true)
    setError(null)
    setMessage('')
    try {
      let updated
      if (action === 'maintenance') {
        updated = await requestSlots(fetchWithAuth, `${selected.id}/status/`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            status:
              selected.status === 'maintenance' ? 'available' : 'maintenance',
          }),
        })
        setMessage(
          `Slot ${selected.slot_number} is now ${updated.status.toLowerCase()}.`,
        )
      } else {
        await requestSlots(fetchWithAuth, `${selected.id}/`, {
          method: 'DELETE',
        })
        updated = { ...selected, is_active: false }
        setMessage(
          `Slot ${selected.slot_number} deactivated. Its record has been retained.`,
        )
      }
      setLiveSlots((current) =>
        current.map((slot) => (slot.id === selected.id ? updated : slot)),
      )
    } catch (failure) {
      setError(failure)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bay-facility">
      <div className="bay-page-heading">
        <div>
          <span className="bay-eyebrow">FACILITY OVERVIEW</span>
          <h1>
            Parking, in perspective<span>.</span>
          </h1>
          <p>Manage your parking spaces, floor by floor.</p>
        </div>
        <button
          className="bay-button bay-button-primary"
          onClick={() => setEditor({ slot: null })}
          disabled={demo || loading}
        >
          <BayIcon name="plus" size={18} />
          Add parking bay
        </button>
      </div>
      <div className={`bay-source-bar ${demo ? 'bay-source-demo' : ''}`}>
        <span>
          <i className="bay-live-dot" />
          {demo ? 'DESIGN DEMO' : 'FACILITY DATA'}
          <span className="bay-source-detail">
            {demo
              ? '72 sample bays · read only'
              : loading
                ? 'Fetching your spaces...'
                : loadedAt
                  ? `Snapshot ${loadedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
                  : 'No snapshot available'}
          </span>
        </span>
        <button type="button" onClick={switchData}>
          {demo ? 'Return to facility' : 'Explore design demo'}
          <BayIcon name="arrow" size={15} />
        </button>
      </div>
      {error && !demo && (
        <div className="bay-alert" role="alert">
          {error.message || 'Unable to reach the slot service.'}
          <button type="button" onClick={refresh} disabled={loading}>
            Try again
          </button>
        </div>
      )}
      {message && (
        <div className="bay-success" role="status">
          <BayIcon name="check" size={17} />
          {message}
        </div>
      )}
      <div className="bay-metrics">
        {[
          ['Total spaces', stats.total, 'Across this floor', 'layers'],
          [
            'Available now',
            stats.AVAILABLE,
            'Room for your next arrival',
            'arrow',
          ],
          [
            'Occupied',
            stats.OCCUPIED,
            `${occupiedPercent}% of floor capacity`,
            'car',
          ],
          [
            'Other spaces',
            otherCount,
            `${stats.RESERVED} reserved · ${stats.MAINTENANCE} maintenance · ${stats.INACTIVE} inactive`,
            'cube',
          ],
        ].map(([label, value, note, icon], index) => (
          <div className={`bay-metric bay-metric-${index}`} key={label}>
            <div>
              <span>{label}</span>
              <BayIcon name={icon} size={18} />
            </div>
            <strong>{value.toString().padStart(2, '0')}</strong>
            <p>{note}</p>
          </div>
        ))}
      </div>
      <div className="bay-workspace-grid">
        <section className="bay-map-card" aria-labelledby="floor-map-heading">
          <div className="bay-map-toolbar">
            <div className="bay-floor-switch" aria-label="Select floor">
              {(floors.length ? floors : [0]).map((number) => (
                <button
                  type="button"
                  key={number ?? 'unmapped'}
                  className={activeFloor === number ? 'is-active' : ''}
                  onClick={() => {
                    setFloor(number)
                    setSelectedId(null)
                    setQuery('')
                  }}
                  aria-pressed={activeFloor === number}
                  aria-label={`Show ${floorLabel(number)}`}
                >
                  {floorCode(number)}
                </button>
              ))}
              <span>{floorLabel(activeFloor)}</span>
            </div>
            <div className="bay-segmented" aria-label="Map display">
              {[
                ['3d', '3D view'],
                ['2d', '2D plan'],
                ['list', 'Register'],
              ].map(([value, label]) => (
                <button
                  type="button"
                  key={value}
                  className={mode === value ? 'is-active' : ''}
                  aria-pressed={mode === value}
                  onClick={() => setMode(value)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          <div
            className={`bay-map-stage ${mode !== '3d' || rendererError ? 'bay-map-flat' : ''}`}
          >
            <div className="bay-scene-heading">
              <span className="bay-eyebrow">
                {demo ? 'SAMPLE FLOOR MODEL' : 'SCHEMATIC FLOOR MODEL'}
              </span>
              <h2 id="floor-map-heading">
                {floorCode(activeFloor)}
                <span>
                  {floorLabel(activeFloor)}
                  <small>
                    {layout.bands.length
                      ? `${new Set(floorSlots.map((slot) => slot.zone)).size} zones · ${stats.total} spaces`
                      : 'Your next great space starts here'}
                  </small>
                </span>
              </h2>
            </div>
            {mode === '3d' && !rendererError ? (
              <Suspense
                fallback={
                  <div className="bay-render-loading">
                    Preparing your perspective...
                  </div>
                }
              >
                <ParkingScene
                  layout={layout}
                  selectedId={selectedId}
                  onSelect={setSelectedId}
                  view={view}
                  resetKey={resetKey}
                  onUnavailable={setRendererError}
                />
              </Suspense>
            ) : (
              <div
                className={`bay-flat-plan ${mode === 'list' ? 'bay-register' : ''}`}
              >
                {rendererError && mode === '3d' && (
                  <p className="bay-render-note">{rendererError}</p>
                )}
                {filtered.map((slot) => (
                  <button
                    key={slot.id}
                    type="button"
                    className={`bay-plan-bay bay-plan-${slotState(slot).toLowerCase()} ${selectedId === slot.id ? 'is-selected' : ''}`}
                    aria-label={`Inspect ${slot.slot_number}, ${STATUS[slotState(slot)]?.label}`}
                    aria-pressed={selectedId === slot.id}
                    onClick={() => setSelectedId(slot.id)}
                  >
                    <BayIcon
                      name={
                        slot.status === 'occupied' && slot.is_active
                          ? 'car'
                          : slot.vehicle_type === 'EV Charging'
                            ? 'bolt'
                            : 'map'
                      }
                      size={27}
                    />
                    <strong>{slot.slot_number}</strong>
                    <span>{STATUS[slotState(slot)]?.label}</span>
                    {mode === 'list' && (
                      <small>
                        Zone {slot.zone_name} · {slot.vehicle_type}
                      </small>
                    )}
                  </button>
                ))}
              </div>
            )}
            {floorSlots.length === 0 && !loading && (
              <div className="bay-empty-overlay">
                <BayIcon name="layers" size={30} />
                <strong>A blank canvas for your facility.</strong>
                <p>Add a bay to begin, or explore the design demo above.</p>
              </div>
            )}
            {mode === '3d' && !rendererError && (
              <div className="bay-scene-bottom">
                <span>
                  <BayIcon name="cube" size={15} />
                  Drag to orbit · Scroll to zoom
                </span>
                <div>
                  <button
                    type="button"
                    aria-label={
                      view === 'top'
                        ? 'Switch to perspective view'
                        : 'Switch to top view'
                    }
                    onClick={() =>
                      setView((value) =>
                        value === 'top' ? 'perspective' : 'top',
                      )
                    }
                  >
                    <BayIcon name="layers" size={17} />
                  </button>
                  <button
                    type="button"
                    aria-label="Reset camera"
                    onClick={() => setResetKey((value) => value + 1)}
                  >
                    <BayIcon name="expand" size={17} />
                  </button>
                </div>
              </div>
            )}
          </div>
          <div className="bay-map-footer">
            <div className="bay-map-legend">
              {Object.entries(STATUS).map(([state, info]) => (
                <span key={state}>
                  <i style={{ background: info.color }} />
                  {info.label}
                </span>
              ))}
            </div>
            <span className="bay-model-note">
              Auto-arranged schematic · cars represent occupied bays
            </span>
          </div>
        </section>
        <aside
          className="bay-inspector"
          aria-label="Space inspector"
          aria-live="polite"
        >
          <div className="bay-inspector-top">
            <span className="bay-eyebrow">
              {selected ? 'SPACE INSPECTOR' : 'FLOOR AT A GLANCE'}
            </span>
            <BayIcon name={selected ? 'car' : 'layers'} size={18} />
          </div>
          {selected ? (
            <>
              <div className="bay-selected-title">
                <h2>{selected.slot_number}</h2>
                <StatusBadge slot={selected} />
              </div>
              <div
                className={`bay-space-visual bay-space-${slotState(selected).toLowerCase()}`}
                aria-hidden="true"
              >
                <div className="bay-visual-outline">
                  {selected.is_active && selected.status === 'occupied' ? (
                    <div className="bay-car-silhouette">
                      <i />
                      <i />
                      <b />
                    </div>
                  ) : (
                    <BayIcon
                      name={
                        selected.vehicle_type === 'EV Charging' ? 'bolt' : 'map'
                      }
                      size={52}
                    />
                  )}
                </div>
                <span>{selected.vehicle_type}</span>
              </div>
              <dl className="bay-slot-details">
                <div>
                  <dt>Floor</dt>
                  <dd>{floorLabel(selected.floor)}</dd>
                </div>
                <div>
                  <dt>Zone</dt>
                  <dd>{selected.zone_name}</dd>
                </div>
                <div>
                  <dt>Vehicle class</dt>
                  <dd>{selected.vehicle_type}</dd>
                </div>
                <div>
                  <dt>Bay status</dt>
                  <dd>
                    {selected.is_active
                      ? selected.status.toLowerCase()
                      : 'deactivated'}
                  </dd>
                </div>
              </dl>
              {demo ? (
                <p className="bay-inspector-hint">
                  Design preview. Sample bays cannot be edited.
                </p>
              ) : (
                <div className="bay-inspector-actions">
                  <button
                    className="bay-button bay-button-light"
                    type="button"
                    disabled={saving || loading}
                    onClick={() => setEditor({ slot: selected })}
                  >
                    <BayIcon name="edit" size={16} />
                    Edit specifications
                  </button>
                  {selected.is_active &&
                    ['available', 'maintenance'].includes(selected.status) && (
                      <button
                        className="bay-button bay-button-quiet"
                        type="button"
                        disabled={saving || loading}
                        onClick={() => updateSelected('maintenance')}
                      >
                        {selected.status === 'maintenance'
                          ? 'Finish maintenance'
                          : 'Start maintenance'}
                      </button>
                    )}
                  <button
                    className="bay-text-danger"
                    type="button"
                    disabled={saving || loading || !selected.is_active}
                    onClick={() => updateSelected('deactivate')}
                  >
                    {saving
                      ? 'Deactivating...'
                      : selected.is_active
                        ? 'Deactivate this bay'
                        : 'Record retained'}
                  </button>
                </div>
              )}
              <p className="bay-inspector-footnote">
                Cars indicate occupied bays. Vehicle identity and live tracking
                are not shown.
              </p>
            </>
          ) : (
            <>
              <h2>
                Space to
                <br />
                breathe.
              </h2>
              <div
                className="bay-occupancy-ring"
                style={{ '--occupied': `${occupiedPercent}%` }}
              >
                <div>
                  <strong>{String(stats.AVAILABLE).padStart(2, '0')}</strong>
                  <span>spaces available</span>
                </div>
              </div>
              <div className="bay-floor-ratio">
                <span>Floor occupancy</span>
                <strong>{occupiedPercent}%</strong>
              </div>
              <div className="bay-progress">
                <i style={{ width: `${occupiedPercent}%` }} />
              </div>
              <p className="bay-inspector-hint">
                Select a bay on the map to see its details, type and
                availability.
              </p>
              <div className="bay-inspector-tip">
                <BayIcon name="bolt" size={18} />
                <span>
                  <strong>Built for a clearer view.</strong>
                  <small>
                    Switch floors. Change perspective.
                    <br />
                    Find room for what’s next.
                  </small>
                </span>
              </div>
            </>
          )}
        </aside>
      </div>
      <section className="bay-directory" aria-labelledby="directory-heading">
        <div className="bay-directory-header">
          <div>
            <span className="bay-eyebrow">SPACE DIRECTORY</span>
            <h2 id="directory-heading">
              Find your space<span>.</span>
            </h2>
          </div>
          <div className="bay-directory-controls">
            <label className="bay-search">
              <BayIcon name="search" size={18} />
              <input
                aria-label="Find a slot or zone"
                placeholder="Find a bay, zone or type..."
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </label>
            <button
              className="bay-icon-button"
              type="button"
              aria-label="Refresh facility data"
              disabled={loading || demo}
              onClick={refresh}
            >
              <BayIcon name="refresh" size={18} />
            </button>
          </div>
        </div>
        <div className="bay-quick-grid">
          {filtered
            .slice(0, mode === 'list' || query ? filtered.length : 6)
            .map((slot) => (
              <button
                type="button"
                className={`bay-quick-card ${selectedId === slot.id ? 'is-selected' : ''}`}
                key={slot.id}
                onClick={() => setSelectedId(slot.id)}
                aria-label={`Select bay ${slot.slot_number}`}
                aria-pressed={selectedId === slot.id}
              >
                <span className="bay-quick-icon">
                  <BayIcon
                    name={slot.vehicle_type === 'EV Charging' ? 'bolt' : 'car'}
                    size={24}
                  />
                </span>
                <strong>{slot.slot_number}</strong>
                <small>
                  Zone {slot.zone_name} · {slot.vehicle_type}
                </small>
                <StatusBadge slot={slot} />
              </button>
            ))}
        </div>
        {filtered.length === 0 && (
          <p className="bay-muted">
            {loading
              ? 'Loading your facility...'
              : query
                ? 'No matching bays on this floor.'
                : 'Create a parking bay to get started.'}
          </p>
        )}
        {filtered.length > 6 && mode !== 'list' && !query && (
          <button
            className="bay-directory-more"
            type="button"
            onClick={() => setMode('list')}
          >
            View all {filtered.length} bays
            <BayIcon name="arrow" size={16} />
          </button>
        )}
      </section>
      {editor && !demo && (
        <SlotEditor
          slot={editor.slot}
          onClose={() => setEditor(null)}
          onSaved={savedSlot}
        />
      )}
    </div>
  )
}
