import { Button } from '@heroui/react'
import { useEffect } from 'react'
import MetroMap from './components/MetroMap'
import RouteDetails from './components/RouteDetails'
import RouteModeTabs from './components/RouteModeTabs'
import StationSearch from './components/StationSearch'
import { MESSAGES } from './messages'
import type { RouteErrorCode } from './routeStore'
import { useRouteStore } from './useRouteStore'

// what the panel says for each reason a route request gave no routes
const ROUTE_ERRORS: Record<RouteErrorCode, string> = {
  no_route: MESSAGES.noRoute, // ER5
  route_failed: MESSAGES.routeFailed, // ER6
  same_station: MESSAGES.sameStation, // ER3
  unexpected: MESSAGES.unexpected, // ER7
}

export default function App() {
  const network = useRouteStore((s) => s.network)
  const lines = useRouteStore((s) => s.linesById)
  const networkStatus = useRouteStore((s) => s.networkStatus)
  const source = useRouteStore((s) => s.source)
  const destination = useRouteStore((s) => s.destination)
  const mode = useRouteStore((s) => s.mode)
  const routes = useRouteStore((s) => s.routes)
  const status = useRouteStore((s) => s.status)
  const errorCode = useRouteStore((s) => s.errorCode)
  const drawIncomplete = useRouteStore((s) => s.drawIncomplete)
  const loadNetwork = useRouteStore((s) => s.loadNetwork)
  const setSource = useRouteStore((s) => s.setSource)
  const setDestination = useRouteStore((s) => s.setDestination)
  const setMode = useRouteStore((s) => s.setMode)
  const findRoute = useRouteStore((s) => s.findRoute)
  const reset = useRouteStore((s) => s.reset)

  // the network is fetched once; the map and the station search are both built from it
  useEffect(() => {
    loadNetwork()
  }, [loadNetwork])

  const bothChosen = source !== null && destination !== null
  const finding = status === 'loading'
  const selectedRoute = routes.find((route) => route.criteria.includes(mode))

  return (
    <div className="app">
      <aside className="panel">
        <h1>Delhi Metro Route Planner</h1>

        {networkStatus === 'loading' && <p className="status-message">Loading stations…</p>}
        {networkStatus === 'error' && (
          <div className="status-message status-error" role="alert">
            <p>{MESSAGES.networkFailed}</p>
            <Button size="sm" onPress={loadNetwork}>
              Reload
            </Button>
          </div>
        )}

        <div className="station-fields">
          <StationSearch
            label="From"
            placeholder="Choose start station"
            value={source}
            onChange={setSource}
            otherId={destination}
          />
          <StationSearch
            label="To"
            placeholder="Choose destination station"
            value={destination}
            onChange={setDestination}
            otherId={source}
          />
        </div>

        <Button className="find-route" fullWidth isDisabled={!bothChosen || finding} onPress={findRoute}>
          {finding ? 'Finding route…' : 'Find route'}
        </Button>
        {!bothChosen && networkStatus === 'ready' && <p className="status-message">{MESSAGES.selectBoth}</p>}
        <Button className="reset-route" fullWidth onPress={reset}>
          Reset
        </Button>

        {status === 'error' && errorCode && (
          <div className="status-message status-error" role="alert">
            <p>{ROUTE_ERRORS[errorCode]}</p>
            {errorCode === 'route_failed' && (
              <Button size="sm" onPress={findRoute}>
                Retry
              </Button>
            )}
          </div>
        )}

        <RouteModeTabs value={mode} onChange={setMode} />

        {drawIncomplete && (
          <p className="status-message status-error" role="alert">
            {MESSAGES.drawIncomplete}
          </p>
        )}
        {selectedRoute && network && (
          <RouteDetails route={selectedRoute} mode={mode} network={network} lines={lines} />
        )}
      </aside>
      <main className="map-area">
        <MetroMap />
        <p className="map-credit">Map data © OpenStreetMap contributors</p>
      </main>
    </div>
  )
}
