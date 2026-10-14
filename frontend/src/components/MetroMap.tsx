import { MAP_HEIGHT, MAP_WIDTH } from '../mapGeometry'
import BaseMap from './BaseMap'

// the map: Delhi in the background; metro lines and the selected route go on top later
export default function MetroMap() {
  return (
    <svg
      className="metro-map"
      viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`}
      role="img"
      aria-label="Map of the Delhi Metro"
    >
      <rect className="map-water" width={MAP_WIDTH} height={MAP_HEIGHT} />
      <BaseMap />
    </svg>
  )
}
