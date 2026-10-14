export interface Line {
  id: string
  name: string
  colour: string
  avg_speed_kmh: number | null // placeholder 35 km/h for every line for now
}

export interface Station {
  id: string
  name: string
  lat: number
  lon: number
  lines: string[] // line IDs, e.g. ["YELLOW", "BLUE"] for Rajiv Chowk
}

// a train connection between two neighbouring stations on one line
export interface Edge {
  edge_id: string
  line_id: string
  from_id: string // station ID
  to_id: string // station ID
}

// what GET /api/network returns
export interface Network {
  data_version: string // hash of the backend's data files
  stations: Station[]
  lines: Line[]
  edges: Edge[] // ride edges only; changing lines inside a station has nothing to draw
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

// which route the planner looks for; the same names the backend puts in Route.criteria
export type RouteMode = 'fastest' | 'fewest_stations' | 'fewest_interchanges'

// one route from POST /api/route
export interface Route {
  criteria: RouteMode[] // every search that found this route, e.g. ["fastest", "fewest_interchanges"]
  stations: string[] // station IDs in travel order
  lines: string[] // line IDs in the order they are used
  interchanges: string[] // station IDs where the rider changes line
  edge_ids: string[] // ride and walk edges in travel order; only ride edges are on the map
  total_time_min: number
  total_distance_km: number
}

// what POST /api/route returns
export interface RouteResponse {
  status: 'ok' | 'no_path'
  routes: Route[]
}
