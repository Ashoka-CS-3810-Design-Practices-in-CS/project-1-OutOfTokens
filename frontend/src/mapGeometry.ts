import type { LonLat } from './types'

// size of the SVG drawing area; the browser scales it to fit the screen
export const MAP_WIDTH = 800
export const MAP_HEIGHT = 600

// the part of the world the map shows: every station fits inside with some margin
const BOUNDS = { latMin: 28.3, latMax: 28.8, lonMin: 76.85, lonMax: 77.58 }

// one degree of longitude is shorter than one of latitude this far north,
// so longitudes are squeezed by cos(latitude) to keep shapes undistorted
const LON_FACTOR = Math.cos((((BOUNDS.latMin + BOUNDS.latMax) / 2) * Math.PI) / 180)

const spanX = (BOUNDS.lonMax - BOUNDS.lonMin) * LON_FACTOR
const spanY = BOUNDS.latMax - BOUNDS.latMin
const SCALE = Math.min(MAP_WIDTH / spanX, MAP_HEIGHT / spanY)

// centre the area, since its shape doesn't exactly match 800x600
const OFFSET_X = (MAP_WIDTH - spanX * SCALE) / 2
const OFFSET_Y = (MAP_HEIGHT - spanY * SCALE) / 2

export interface Point {
  x: number
  y: number
}

// lat/lon -> SVG coordinates, north up
export function project(lat: number, lon: number): Point {
  return {
    x: OFFSET_X + (lon - BOUNDS.lonMin) * LON_FACTOR * SCALE,
    y: OFFSET_Y + (BOUNDS.latMax - lat) * SCALE,
  }
}

// a list of [lon, lat] points -> an SVG path string; closed shapes end with Z
export function toPath(points: LonLat[], closed: boolean): string {
  const parts = points.map(([lon, lat], i) => {
    const { x, y } = project(lat, lon)
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`
  })
  return parts.join('') + (closed ? 'Z' : '')
}
