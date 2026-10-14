import { ArrowRightArrowLeft, Route as RouteIcon, Stopwatch } from '@gravity-ui/icons'
import { Card } from '@heroui/react'
import type { CSSProperties } from 'react'
import type { Line, Network, Route, RouteMode } from '../types'

interface RouteDetailsProps {
  route: Route
  mode: RouteMode
  network: Network
  lines: Map<string, Line>
}

const TITLES: Record<RouteMode, string> = {
  fastest: 'Fastest route',
  fewest_stations: 'Fewest stations',
  fewest_interchanges: 'Fewest interchanges',
}

const ICONS: Record<RouteMode, typeof Stopwatch> = {
  fastest: Stopwatch,
  fewest_stations: RouteIcon,
  fewest_interchanges: ArrowRightArrowLeft,
}

// one stretch of the trip on a single line
interface Leg {
  lineId: string
  stationIds: string[]
}

// the card with the route's totals, then every station on it grouped by line
export default function RouteDetails({ route, mode, network, lines }: RouteDetailsProps) {
  const Icon = ICONS[mode]
  const names = new Map(network.stations.map((s) => [s.id, s.name]))
  const legs = splitIntoLegs(route, network)
  const changes = route.interchanges.length

  return (
    <div className="route-details">
      <Card className="route-card">
        <Icon aria-hidden="true" className="text-accent size-6" />
        <Card.Header>
          <Card.Title>{TITLES[mode]}</Card.Title>
          <Card.Description>
            {names.get(route.stations[0])} to {names.get(route.stations[route.stations.length - 1])}
          </Card.Description>
        </Card.Header>
        <Card.Content>
          <dl className="route-stats">
            <div>
              <dt>Total time</dt>
              <dd>{Math.round(route.total_time_min)} min</dd>
            </div>
            <div>
              <dt>Changes</dt>
              <dd>{changes}</dd>
            </div>
            <div>
              <dt>Distance</dt>
              <dd>{route.total_distance_km.toFixed(1)} km</dd>
            </div>
          </dl>
        </Card.Content>
      </Card>

      <ol className="route-legs" aria-label="Stations on this route">
        {legs.map((leg, i) => (
          <li
            key={i}
            className="route-leg"
            style={{ '--line-colour': lines.get(leg.lineId)?.colour ?? '#888' } as CSSProperties}
            aria-label={lines.get(leg.lineId)?.name}
          >
            <ol>
              {leg.stationIds.map((id) => (
                <li key={id} className="route-stop">
                  <span className="route-stop-dot" aria-hidden="true" />
                  {names.get(id) ?? id}
                </li>
              ))}
            </ol>
          </li>
        ))}
      </ol>
    </div>
  )
}

// cuts the station list wherever the line changes; the interchange station ends one leg and starts the next
function splitIntoLegs(route: Route, network: Network): Leg[] {
  const lineOfEdge = new Map(network.edges.map((e) => [e.edge_id, e.line_id]))
  // ride edges only, in travel order: the i-th one goes from stations[i] to stations[i + 1]
  const rideLines = route.edge_ids.flatMap((id) => {
    const line = lineOfEdge.get(id)
    return line ? [line] : []
  })

  const legs: Leg[] = []
  rideLines.forEach((lineId, i) => {
    const current = legs[legs.length - 1]
    if (current && current.lineId === lineId) {
      current.stationIds.push(route.stations[i + 1])
    } else {
      legs.push({ lineId, stationIds: [route.stations[i], route.stations[i + 1]] })
    }
  })
  return legs
}
