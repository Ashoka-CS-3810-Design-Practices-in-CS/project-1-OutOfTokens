export interface Line {
  id: string
  name: string
  colour: string
}

export interface Station {
  id: string
  name: string
  lat: number
  lon: number
  lines: string[] // line IDs, e.g. ["YELLOW", "BLUE"] for Rajiv Chowk
}

// what GET /api/network will return (the ride edges get added once the map draws lines)
export interface Network {
  stations: Station[]
  lines: Line[]
}

// a point as [longitude, latitude], the order GeoJSON uses
export type LonLat = [number, number]

export interface BasemapRegion {
  name: string
  rings: LonLat[][]
}

export interface BasemapRiver {
  name: string
  lines: LonLat[][]
}

// shape of src/data/delhiBasemap.json
export interface Basemap {
  source: string
  delhi: BasemapRegion
  neighbours: BasemapRegion[]
  rivers: BasemapRiver[]
}

// which route the planner looks for; names match the backend routes
export type RouteMode = 'fastest' | 'fewest-changes'
