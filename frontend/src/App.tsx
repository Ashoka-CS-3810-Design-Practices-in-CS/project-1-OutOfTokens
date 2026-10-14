import { useState } from 'react'
import MetroMap from './components/MetroMap'
import StationSearch from './components/StationSearch'
// temporary: made from backend/data until GET /api/network exists, then fetched through apiClient
import sampleNetwork from './data/sampleNetwork.json'
import type { Line, Network } from './types'

const network = sampleNetwork as Network
const linesById = new Map<string, Line>(network.lines.map((line) => [line.id, line]))

export default function App() {
  const [source, setSource] = useState<string | null>(null)
  const [destination, setDestination] = useState<string | null>(null)

  return (
    <div className="app">
      <aside className="panel">
        <h1>Delhi Metro Route Planner</h1>
        <div className="station-fields">
          <StationSearch
            label="From"
            placeholder="Choose start station"
            stations={network.stations}
            lines={linesById}
            value={source}
            onChange={setSource}
            excludeId={destination}
          />
          <StationSearch
            label="To"
            placeholder="Choose destination station"
            stations={network.stations}
            lines={linesById}
            value={destination}
            onChange={setDestination}
            excludeId={source}
          />
        </div>
      </aside>
      <main className="map-area">
        <MetroMap />
        <p className="map-credit">Map data © OpenStreetMap contributors</p>
      </main>
    </div>
  )
}
