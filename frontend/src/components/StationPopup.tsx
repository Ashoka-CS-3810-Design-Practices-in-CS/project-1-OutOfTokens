import { useEffect, useRef } from 'react'
import type { KeyboardEvent } from 'react'
import { useRouteStore } from '../useRouteStore'

// details of the station clicked on the map: its name, its lines and whether it is an interchange.
// Everything comes from the station index already in memory; nothing is fetched.
export default function StationPopup() {
  const stationId = useRouteStore((s) => s.popupStationId)
  const index = useRouteStore((s) => s.index)
  const lines = useRouteStore((s) => s.linesById)
  const closeStation = useRouteStore((s) => s.closeStation)
  const closeRef = useRef<HTMLButtonElement>(null)

  const station = stationId ? index?.get(stationId) : undefined

  // move keyboard focus into the popup when it opens or shows another station
  useEffect(() => {
    if (station) closeRef.current?.focus()
  }, [station])

  if (!station) return null
  const interchange = station.lines.length > 1

  function onKeyDown(event: KeyboardEvent) {
    if (event.key === 'Escape') closeStation()
  }

  return (
    <section className="station-popup" role="dialog" aria-labelledby="station-popup-title" onKeyDown={onKeyDown}>
      <header className="station-popup-header">
        <h2 id="station-popup-title">{station.name}</h2>
        <button
          ref={closeRef}
          type="button"
          className="station-popup-close"
          aria-label="Close station details"
          onClick={closeStation}
        >
          ×
        </button>
      </header>
      <p className="station-popup-kind">{interchange ? 'Interchange station' : 'Not an interchange'}</p>
      <ul className="station-popup-lines" aria-label="Lines at this station">
        {station.lines.map((id) => {
          const line = lines.get(id)
          return (
            <li key={id}>
              <span className="line-dot" style={{ background: line?.colour ?? '#888' }} aria-hidden="true" />
              {line?.name ?? id}
            </li>
          )
        })}
      </ul>
    </section>
  )
}
