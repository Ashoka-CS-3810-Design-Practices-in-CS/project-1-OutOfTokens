import type { Station } from './types'

// plain TypeScript: no React and no D3 (enforced in eslint.config.js)

export const MAX_QUERY_LENGTH = 100
export const MAX_SUGGESTIONS = 8

export interface StationIndex {
  // up to 8 stations matching the query: names that start with it first, then names that contain it
  search(query: string): Station[]
  // the full record for a station id, for the popup and the route panel
  get(id: string): Station | undefined
}

// lower-case, trimmed, accents removed, so "rajiv " finds "Rajiv Chowk"
function normalise(text: string): string {
  return text.trim().toLowerCase().normalize('NFD').replace(/\p{Diacritic}/gu, '')
}

// built once, when the network has loaded
export function buildStationIndex(stations: Station[]): StationIndex {
  const entries = stations.map((station) => ({ station, name: normalise(station.name) }))
  const byId = new Map(stations.map((station) => [station.id, station]))

  return {
    search(query) {
      const wanted = normalise(query.slice(0, MAX_QUERY_LENGTH))
      if (!wanted) return []
      const startsWith: Station[] = []
      const contains: Station[] = []
      for (const { station, name } of entries) {
        if (name.startsWith(wanted)) startsWith.push(station)
        else if (name.includes(wanted)) contains.push(station)
      }
      return [...startsWith, ...contains].slice(0, MAX_SUGGESTIONS)
    },
    get(id) {
      return byId.get(id)
    },
  }
}
