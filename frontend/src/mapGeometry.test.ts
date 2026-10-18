import { describe, expect, it } from 'vitest'
import { FULL_VIEW, MAP_HEIGHT, MAP_WIDTH, project, toPath, viewAround } from './mapGeometry'

describe('placing stations on the map', () => {
  it('puts north at the top', () => {
    // Kashmere Gate is north of Central Secretariat
    expect(project(28.6675, 77.2282).y).toBeLessThan(project(28.6149, 77.2119).y)
  })

  it('puts east on the right', () => {
    expect(project(28.6, 77.3).x).toBeGreaterThan(project(28.6, 77.1).x)
  })

  it('keeps the far corners of the metro network inside the drawing area', () => {
    // roughly Najafgarh (south-west), Shaheed Sthal (north-east), Raja Nahar Singh (south)
    for (const [lat, lon] of [
      [28.61, 76.98],
      [28.67, 77.42],
      [28.34, 77.33],
    ]) {
      const { x, y } = project(lat, lon)
      expect(x).toBeGreaterThan(0)
      expect(x).toBeLessThan(MAP_WIDTH)
      expect(y).toBeGreaterThan(0)
      expect(y).toBeLessThan(MAP_HEIGHT)
    }
  })

  it('turns a list of points into an SVG path, closed with Z only when asked', () => {
    const points: [number, number][] = [
      [77.1, 28.6],
      [77.2, 28.7],
    ]
    expect(toPath(points, false)).toMatch(/^M[\d.]+,[\d.]+L[\d.]+,[\d.]+$/)
    expect(toPath(points, true).endsWith('Z')).toBe(true)
  })
})

describe('the starting view', () => {
  it('shows the whole drawing when there are no stations', () => {
    expect(viewAround([])).toEqual(FULL_VIEW)
  })

  it('keeps the 4:3 shape of the map', () => {
    const view = viewAround([
      { x: 100, y: 100 },
      { x: 500, y: 120 },
    ])
    expect(view.width / view.height).toBeCloseTo(MAP_WIDTH / MAP_HEIGHT)
  })

  it('fits every station with a margin around them', () => {
    const points = [
      { x: 100, y: 100 },
      { x: 300, y: 450 },
      { x: 250, y: 200 },
    ]
    const view = viewAround(points, 30)
    for (const p of points) {
      expect(p.x).toBeGreaterThanOrEqual(view.x + 30 - 1e-9)
      expect(p.x).toBeLessThanOrEqual(view.x + view.width - 30 + 1e-9)
      expect(p.y).toBeGreaterThanOrEqual(view.y + 30 - 1e-9)
      expect(p.y).toBeLessThanOrEqual(view.y + view.height - 30 + 1e-9)
    }
  })
})
