import { select } from 'd3-selection'
import { zoom, zoomIdentity } from 'd3-zoom'
import type { ZoomBehavior } from 'd3-zoom'
import { useEffect, useMemo, useRef, useState } from 'react'
import type { CSSProperties, KeyboardEvent } from 'react'
import { MAP_HEIGHT, MAP_WIDTH, project, viewAround } from '../mapGeometry'
import type { Edge } from '../types'
import { useRouteStore } from '../useRouteStore'
import BaseMap from './BaseMap'
import StationPopup from './StationPopup'

// how far in and out the map can zoom, as the width of the visible area in SVG units
const MIN_VIEW_WIDTH = 80
const MAX_VIEW_WIDTH = MAP_WIDTH * 1.5
// how much closer the starting view is than one that fits every station
const HOME_ZOOM = 1.25

// the map: Delhi in the background, then every metro line, then the stations on top.
// d3-zoom pans and zooms it (drag, wheel, pinch, buttons) by moving one <g>, so React never re-renders for it.
export default function MetroMap() {
  const network = useRouteStore((s) => s.network)
  const lines = useRouteStore((s) => s.linesById)
  const source = useRouteStore((s) => s.source)
  const destination = useRouteStore((s) => s.destination)
  const routes = useRouteStore((s) => s.routes)
  const mode = useRouteStore((s) => s.mode)
  const openStation = useRouteStore((s) => s.openStation)

  const points = useMemo(
    () => new Map((network?.stations ?? []).map((s) => [s.id, project(s.lat, s.lon)])),
    [network],
  )
  const edgesById = useMemo(
    () => new Map((network?.edges ?? []).map((edge) => [edge.edge_id, edge])),
    [network],
  )
  // the starting view: the middle of the metro network, slightly cropped so the dense centre is easier to read
  const homeView = useMemo(() => {
    const fit = viewAround([...points.values()])
    const width = fit.width / HOME_ZOOM
    const height = fit.height / HOME_ZOOM
    return { x: fit.x + (fit.width - width) / 2, y: fit.y + (fit.height - height) / 2, width, height }
  }, [points])
  // multiplies SVG units into "full map" units, so labels and hit areas keep the same size on screen
  const baseScale = MAP_WIDTH / homeView.width

  // one route can answer several tabs, so "selected" is whichever route lists the tab's criterion.
  // Each edge is drawn once, in the most prominent style it qualifies for: selected, then other
  // routes (faded), then the rest of the network (grey once routes are shown).
  const selectedRoute = routes.find((route) => route.criteria.includes(mode))
  const selectedIds = new Set(selectedRoute?.edge_ids)
  const otherIds = new Set(
    routes
      .filter((route) => route !== selectedRoute)
      .flatMap((route) => route.edge_ids)
      .filter((id) => !selectedIds.has(id)),
  )
  const hasRoutes = routes.length > 0

  const [hoveredId, setHoveredId] = useState<string | null>(null)
  const hoveredStation = network?.stations.find((s) => s.id === hoveredId)
  const hovered = hoveredStation && { name: hoveredStation.name, ...points.get(hoveredStation.id)! }

  // the selected route's start, end and interchanges are always named; the hovered station already has its own label
  const routeStart = selectedRoute?.stations[0]
  const routeEnd = selectedRoute?.stations[selectedRoute.stations.length - 1]
  const routeStops = selectedRoute ? [routeStart, ...selectedRoute.interchanges, routeEnd] : []
  const routeLabels = [...new Set(routeStops)]
    .filter((id) => id !== hoveredId)
    .flatMap((id) => {
      const station = network?.stations.find((s) => s.id === id)
      const point = id ? points.get(id) : undefined
      if (!station || !point) return []
      return [{ id: station.id, name: station.name, end: id === routeStart || id === routeEnd, ...point }]
    })

  const svgRef = useRef<SVGSVGElement>(null)
  const layerRef = useRef<SVGGElement>(null)
  const zoomRef = useRef<ZoomBehavior<SVGSVGElement, unknown> | null>(null)
  const [moved, setMoved] = useState(false)

  useEffect(() => {
    const svg = svgRef.current
    const layer = layerRef.current
    if (!svg || !layer) return
    const behaviour = zoom<SVGSVGElement, unknown>()
      .scaleExtent([homeView.width / MAX_VIEW_WIDTH, homeView.width / MIN_VIEW_WIDTH])
      // the map can't be dragged further than one map-width off any side
      .translateExtent([
        [-MAP_WIDTH, -MAP_HEIGHT],
        [MAP_WIDTH * 2, MAP_HEIGHT * 2],
      ])
      .on('zoom', (event) => {
        const { k, x, y } = event.transform
        layer.setAttribute('transform', event.transform.toString())
        layer.style.setProperty('--zoom', String(k * baseScale))
        setMoved(k !== 1 || x !== 0 || y !== 0)
      })
    zoomRef.current = behaviour
    const selection = select(svg)
    selection.call(behaviour).call(behaviour.transform, zoomIdentity)
    return () => {
      selection.on('.zoom', null)
    }
  }, [homeView, baseScale])

  function zoomBy(factor: number) {
    if (svgRef.current && zoomRef.current) select(svgRef.current).call(zoomRef.current.scaleBy, factor)
  }

  function resetView() {
    if (svgRef.current && zoomRef.current) select(svgRef.current).call(zoomRef.current.transform, zoomIdentity)
  }

  function onStationKey(event: KeyboardEvent, id: string) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      openStation(id)
    }
  }

  function drawEdge(edge: Edge, className?: string) {
    const from = points.get(edge.from_id)
    const to = points.get(edge.to_id)
    if (!from || !to) return null
    return (
      <line
        key={edge.edge_id}
        className={className}
        x1={from.x}
        y1={from.y}
        x2={to.x}
        y2={to.y}
        stroke={lines.get(edge.line_id)?.colour ?? '#888'}
      />
    )
  }

  // ride edges by id; a route's walk edges stay inside a station and aren't in edgesById
  function drawEdges(ids: Iterable<string>, className: string) {
    return [...ids].map((id) => {
      const edge = edgesById.get(id)
      return edge ? drawEdge(edge, className) : null
    })
  }

  return (
    <div className="metro-map-wrap">
      <svg
        ref={svgRef}
        className="metro-map"
        viewBox={`${homeView.x} ${homeView.y} ${homeView.width} ${homeView.height}`}
        role="group"
        aria-label="Map of the Delhi Metro. Tab to a station and press Enter for its details."
      >
        <g ref={layerRef} style={{ '--zoom': baseScale } as CSSProperties}>
          {/* reaches well past the map so moving it never shows a blank edge */}
          <rect
            className="map-water"
            x={-MAP_WIDTH}
            y={-MAP_HEIGHT}
            width={MAP_WIDTH * 3}
            height={MAP_HEIGHT * 3}
          />
          <BaseMap />

          {/* the whole network in line colours; once there are routes, the lines no route uses turn thin and grey */}
          <g className={hasRoutes ? 'metro-edges metro-edges-unused' : 'metro-edges'}>
            {network?.edges
              .filter((edge) => !selectedIds.has(edge.edge_id) && !otherIds.has(edge.edge_id))
              .map((edge) => drawEdge(edge))}
          </g>

          {/* the other tabs' routes faded, then the selected route bright on top; both the same width */}
          <g className="route-edges">
            {drawEdges(otherIds, 'route-edge route-edge-faded')}
            {drawEdges(selectedIds, 'route-edge')}
          </g>

          <g className="metro-stations">
            {network?.stations.map((station) => {
              const { x, y } = points.get(station.id)!
              const interchange = station.lines.length > 1
              const chosen = station.id === source || station.id === destination
              const classes = ['station', interchange && 'station-interchange', chosen && 'station-chosen']
              return (
                <g
                  key={station.id}
                  className="station-node"
                  role="button"
                  tabIndex={0}
                  aria-label={station.name}
                  onClick={() => openStation(station.id)}
                  onKeyDown={(event) => onStationKey(event, station.id)}
                  onPointerEnter={() => setHoveredId(station.id)}
                  onPointerLeave={() => setHoveredId((id) => (id === station.id ? null : id))}
                  onFocus={() => setHoveredId(station.id)}
                  onBlur={() => setHoveredId((id) => (id === station.id ? null : id))}
                >
                  <circle
                    className={classes.filter(Boolean).join(' ')}
                    cx={x}
                    cy={y}
                    r={chosen ? 6 : interchange ? 3.5 : 2.2}
                  />
                  {/* invisible, bigger target so the small dots are easy to hover and click */}
                  <circle className="station-hit" cx={x} cy={y} r={7 / baseScale} />
                </g>
              )
            })}
          </g>

          <g className="route-labels">
            {routeLabels.map((label) => (
              <text
                key={label.id}
                className={label.end ? 'station-label' : 'station-label station-label-interchange'}
                x={label.x}
                y={label.y}
              >
                {label.name}
              </text>
            ))}
          </g>

          {hovered && (
            <text className="station-label" x={hovered.x} y={hovered.y}>
              {hovered.name}
            </text>
          )}
        </g>
      </svg>

      <div className="map-controls">
        <button type="button" className="map-button" aria-label="Zoom in" onClick={() => zoomBy(1.5)}>
          +
        </button>
        <button type="button" className="map-button" aria-label="Zoom out" onClick={() => zoomBy(1 / 1.5)}>
          −
        </button>
        {moved && (
          <button type="button" className="map-button" onClick={resetView}>
            Reset view
          </button>
        )}
      </div>

      <StationPopup />
    </div>
  )
}
