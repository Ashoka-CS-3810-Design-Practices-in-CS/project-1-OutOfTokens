import { memo } from 'react'
import basemapJson from '../data/delhiBasemap.json'
import { project, toPath } from '../mapGeometry'
import type { Basemap, BasemapRegion } from '../types'

const basemap = basemapJson as Basemap

// where each name is written, chosen by hand so labels sit clear of the metro lines
const LABELS: { text: string; lat: number; lon: number; kind: 'state' | 'city' | 'river' }[] = [
  { text: 'DELHI', lat: 28.775, lon: 76.99, kind: 'state' },
  { text: 'Gurugram', lat: 28.37, lon: 76.93, kind: 'city' },
  { text: 'Faridabad', lat: 28.34, lon: 77.37, kind: 'city' },
  { text: 'Noida', lat: 28.5, lon: 77.48, kind: 'city' },
  { text: 'Ghaziabad', lat: 28.75, lon: 77.47, kind: 'city' },
  { text: 'Yamuna', lat: 28.735, lon: 77.205, kind: 'river' },
  { text: 'Hindon', lat: 28.6, lon: 77.462, kind: 'river' },
]

function regionPath(region: BasemapRegion): string {
  return region.rings.map((ring) => toPath(ring, true)).join('')
}

// the static background: Delhi, the neighbouring cities and the rivers.
// It never changes, so memo stops it re-rendering when routes change.
function BaseMap() {
  return (
    <g className="basemap" aria-hidden="true">
      {basemap.neighbours.map((region) => (
        <path key={region.name} className="basemap-neighbour" d={regionPath(region)} />
      ))}
      <path className="basemap-delhi" d={regionPath(basemap.delhi)} />
      {basemap.rivers.map((river) =>
        river.lines.map((line, i) => (
          <path key={`${river.name}-${i}`} className="basemap-river" d={toPath(line, false)} />
        )),
      )}
      {LABELS.map((label) => {
        const { x, y } = project(label.lat, label.lon)
        return (
          <text key={label.text} x={x} y={y} className={`basemap-label basemap-label-${label.kind}`}>
            {label.text}
          </text>
        )
      })}
    </g>
  )
}

export default memo(BaseMap)
