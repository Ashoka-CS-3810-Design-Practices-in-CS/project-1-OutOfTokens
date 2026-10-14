import { createStore } from 'zustand/vanilla'
import { ApiError, fetchNetwork, fetchRoutes } from './apiClient'
import { buildStationIndex } from './stationIndex'
import type { StationIndex } from './stationIndex'
import type { Line, Network, Route, RouteMode } from './types'

// plain TypeScript: no React and no D3 (enforced in eslint.config.js). Components read it through useRouteStore.

export type NetworkStatus = 'loading' | 'ready' | 'error'
export type RouteStatus = 'idle' | 'loading' | 'success' | 'error'
// why the last route request didn't give routes; the panel turns each into a message
export type RouteErrorCode = 'no_route' | 'route_failed' | 'same_station' | 'unexpected'

export interface RouteState {
  network: Network | null
  index: StationIndex | null
  linesById: Map<string, Line>
  networkStatus: NetworkStatus

  source: string | null // station ids, only ever set from a chosen suggestion
  destination: string | null
  mode: RouteMode // which route is selected
  routes: Route[]
  status: RouteStatus
  errorCode: RouteErrorCode | null
  drawIncomplete: boolean // some of a route's stations or edges aren't on the map
  requestSeq: number // bumped by every request and every change; a reply with an older number is ignored
  popupStationId: string | null

  loadNetwork: () => Promise<void>
  setSource: (id: string | null) => void
  setDestination: (id: string | null) => void
  setMode: (mode: RouteMode) => void
  findRoute: () => Promise<void>
  reset: () => void
  openStation: (id: string) => void
  closeStation: () => void
}

// the route request in flight, so Reset or a station change can cancel it
let inFlight: AbortController | null = null
// the network request in flight, so calling loadNetwork twice (StrictMode) fetches once
let networkRequest: Promise<void> | null = null

const cleared = {
  routes: [] as Route[],
  status: 'idle' as RouteStatus,
  errorCode: null,
  drawIncomplete: false,
}

export const routeStore = createStore<RouteState>()((set, get) => {
  // forget the routes on screen and make any pending reply stale
  function invalidate() {
    inFlight?.abort()
    inFlight = null
    set((state) => ({ ...cleared, requestSeq: state.requestSeq + 1 }))
  }

  return {
    network: null,
    index: null,
    linesById: new Map(),
    networkStatus: 'loading',
    source: null,
    destination: null,
    mode: 'fastest',
    ...cleared,
    requestSeq: 0,
    popupStationId: null,

    loadNetwork() {
      if (networkRequest) return networkRequest
      set({ networkStatus: 'loading' })
      networkRequest = fetchNetwork()
        .then((network) => {
          set({
            network,
            index: buildStationIndex(network.stations),
            linesById: new Map(network.lines.map((line) => [line.id, line])),
            networkStatus: 'ready',
          })
        })
        .catch(() => set({ networkStatus: 'error' }))
        .finally(() => {
          networkRequest = null
        })
      return networkRequest
    },

    setSource(id) {
      if (id !== null && id === get().destination) return
      set({ source: id })
      invalidate()
    },

    setDestination(id) {
      if (id !== null && id === get().source) return
      set({ destination: id })
      invalidate()
    },

    // only changes which stored route is selected; no new request
    setMode(mode) {
      set({ mode })
    },

    async findRoute() {
      const { source, destination } = get()
      if (!source || !destination || source === destination) return
      invalidate()
      const seq = get().requestSeq
      const controller = new AbortController()
      inFlight = controller
      set({ status: 'loading' })

      try {
        const response = await fetchRoutes(source, destination, controller.signal)
        if (seq !== get().requestSeq) return
        if (response.status === 'no_path' || response.routes.length === 0) {
          set({ status: 'error', errorCode: 'no_route' })
          return
        }
        set({
          routes: response.routes,
          status: 'success',
          mode: 'fastest', // the fastest route is selected after every search
          drawIncomplete: !canDrawAll(get().network, response.routes),
        })
      } catch (error) {
        if (seq !== get().requestSeq) return
        set({ status: 'error', errorCode: toErrorCode(error) })
      } finally {
        if (inFlight === controller) inFlight = null
      }
    },

    reset() {
      set({ source: null, destination: null, mode: 'fastest', popupStationId: null })
      invalidate()
    },

    openStation(id) {
      set({ popupStationId: id })
    },

    closeStation() {
      set({ popupStationId: null })
    },
  }
})

function toErrorCode(error: unknown): RouteErrorCode {
  const code = error instanceof ApiError ? error.code : null
  if (code === 'same_station') return 'same_station'
  if (code === 'timeout' || code === 'unreachable' || code === 'server_error') return 'route_failed'
  return 'unexpected'
}

// every station of every route is on the map, and every ride between them has a drawn edge.
// A route with n stations has n - 1 rides; its walk edges stay inside a station and are never drawn.
function canDrawAll(network: Network | null, routes: Route[]): boolean {
  if (!network) return false
  const stationIds = new Set(network.stations.map((s) => s.id))
  const edgeIds = new Set(network.edges.map((e) => e.edge_id))
  for (const route of routes) {
    const missingStations = route.stations.filter((id) => !stationIds.has(id))
    const rides = route.edge_ids.filter((id) => edgeIds.has(id)).length
    if (missingStations.length > 0 || rides !== route.stations.length - 1) {
      console.error('Route not fully on the map', { route, missingStations })
      return false
    }
  }
  return true
}
