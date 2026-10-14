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
