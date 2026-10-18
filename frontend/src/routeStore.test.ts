import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Network, Route, RouteResponse } from './types'

// the backend calls are stand-ins, so each test decides what the backend says
vi.mock('./apiClient', async (importOriginal) => ({
  ...(await importOriginal<typeof import('./apiClient')>()),
  fetchNetwork: vi.fn(),
  fetchRoutes: vi.fn(),
}))

const NETWORK: Network = {
  data_version: 'test',
  stations: [
    { id: 'NEW_DELHI', name: 'New Delhi', lat: 28.64, lon: 77.22, lines: ['YELLOW'] },
    { id: 'RAJIV_CHOWK', name: 'Rajiv Chowk', lat: 28.63, lon: 77.22, lines: ['YELLOW', 'BLUE'] },
    { id: 'MANDI_HOUSE', name: 'Mandi House', lat: 28.62, lon: 77.23, lines: ['BLUE'] },
  ],
  lines: [
    { id: 'YELLOW', name: 'Yellow Line', colour: '#FFD700', avg_speed_kmh: 35 },
    { id: 'BLUE', name: 'Blue Line', colour: '#0000FF', avg_speed_kmh: 35 },
  ],
  edges: [
    { edge_id: 'Y1', line_id: 'YELLOW', from_id: 'NEW_DELHI', to_id: 'RAJIV_CHOWK' },
    { edge_id: 'B1', line_id: 'BLUE', from_id: 'RAJIV_CHOWK', to_id: 'MANDI_HOUSE' },
  ],
}

const ROUTE: Route = {
  criteria: ['fastest', 'fewest_interchanges', 'fewest_stations'],
  stations: ['NEW_DELHI', 'RAJIV_CHOWK', 'MANDI_HOUSE'],
  lines: ['YELLOW', 'BLUE'],
  interchanges: ['RAJIV_CHOWK'],
  edge_ids: ['Y1', 'WALK_RAJIV_CHOWK', 'B1'],
  total_time_min: 9,
  total_distance_km: 2.1,
}

// a fresh store for every test, since the store keeps state between calls
async function fresh() {
  vi.resetAllMocks() // forget earlier tests' calls and answers
  vi.resetModules()
  const api = await import('./apiClient')
  const { routeStore } = await import('./routeStore')
  vi.mocked(api.fetchNetwork).mockResolvedValue(NETWORK)
  return { api, store: routeStore }
}

async function readyWithBothStations() {
  const setup = await fresh()
  await setup.store.getState().loadNetwork()
  setup.store.getState().setSource('NEW_DELHI')
  setup.store.getState().setDestination('MANDI_HOUSE')
  return setup
}

afterEach(() => {
  vi.restoreAllMocks() // undo the console.error silencing
})

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((r) => (resolve = r))
  return { promise, resolve }
}

describe('loading the network', () => {
  it('builds the station search and the line colours once the network arrives', async () => {
    const { store } = await fresh()
    expect(store.getState().networkStatus).toBe('loading')
    await store.getState().loadNetwork()
    const state = store.getState()
    expect(state.networkStatus).toBe('ready')
    expect(state.index?.search('rajiv').map((s) => s.id)).toEqual(['RAJIV_CHOWK'])
    expect(state.linesById.get('BLUE')?.colour).toBe('#0000FF')
  })

  it('shows the error state if the network cannot be loaded', async () => {
    const { api, store } = await fresh()
    vi.mocked(api.fetchNetwork).mockRejectedValue(new api.ApiError('unreachable'))
    await store.getState().loadNetwork()
    expect(store.getState().networkStatus).toBe('error')
    expect(store.getState().index).toBeNull()
  })

  it('asks the backend only once when loading is started twice at the same time', async () => {
    const { api, store } = await fresh()
    await Promise.all([store.getState().loadNetwork(), store.getState().loadNetwork()])
    expect(api.fetchNetwork).toHaveBeenCalledTimes(1)
  })
})

describe('choosing stations', () => {
  it('refuses the same station in both fields', async () => {
    const { store } = await fresh()
    store.getState().setSource('NEW_DELHI')
    store.getState().setDestination('NEW_DELHI')
    expect(store.getState().destination).toBeNull()
  })

  it('does not ask for a route until both stations are chosen', async () => {
    const { api, store } = await fresh()
    store.getState().setSource('NEW_DELHI')
    await store.getState().findRoute()
    expect(api.fetchRoutes).not.toHaveBeenCalled()
  })

  it('clears the routes on screen when a station changes', async () => {
    const { api, store } = await readyWithBothStations()
    vi.mocked(api.fetchRoutes).mockResolvedValue({ status: 'ok', routes: [ROUTE] })
    await store.getState().findRoute()
    store.getState().setDestination('RAJIV_CHOWK')
    expect(store.getState().routes).toEqual([])
    expect(store.getState().status).toBe('idle')
  })
})

describe('finding a route', () => {
  it('shows the routes and selects the fastest', async () => {
    const { api, store } = await readyWithBothStations()
    store.getState().setMode('fewest_stations')
    vi.mocked(api.fetchRoutes).mockResolvedValue({ status: 'ok', routes: [ROUTE] })
    await store.getState().findRoute()
    const state = store.getState()
    expect(api.fetchRoutes).toHaveBeenCalledWith('NEW_DELHI', 'MANDI_HOUSE', expect.any(AbortSignal))
    expect(state.status).toBe('success')
    expect(state.routes).toEqual([ROUTE])
    expect(state.mode).toBe('fastest')
    expect(state.drawIncomplete).toBe(false)
  })

  it('says there is no route when the backend finds none', async () => {
    const { api, store } = await readyWithBothStations()
    vi.mocked(api.fetchRoutes).mockResolvedValue({ status: 'no_path', routes: [] })
    await store.getState().findRoute()
    expect(store.getState().status).toBe('error')
    expect(store.getState().errorCode).toBe('no_route')
  })

  it.each([
    ['same_station', 'same_station'],
    ['timeout', 'route_failed'],
    ['unreachable', 'route_failed'],
    ['server_error', 'route_failed'],
    ['bad_request', 'unexpected'],
  ])('turns the failure "%s" into the message "%s"', async (code, expected) => {
    const { api, store } = await readyWithBothStations()
    vi.mocked(api.fetchRoutes).mockRejectedValue(new api.ApiError(code))
    await store.getState().findRoute()
    expect(store.getState().errorCode).toBe(expected)
  })

  it('ignores a late answer that arrives after Reset', async () => {
    const { api, store } = await readyWithBothStations()
    const late = deferred<RouteResponse>()
    vi.mocked(api.fetchRoutes).mockReturnValue(late.promise)
    const finding = store.getState().findRoute()
    expect(store.getState().status).toBe('loading')
    store.getState().reset()
    late.resolve({ status: 'ok', routes: [ROUTE] })
    await finding
    expect(store.getState().routes).toEqual([])
    expect(store.getState().status).toBe('idle')
    expect(store.getState().source).toBeNull()
  })

  it('cancels the request in flight on Reset', async () => {
    const { api, store } = await readyWithBothStations()
    vi.mocked(api.fetchRoutes).mockReturnValue(deferred<RouteResponse>().promise)
    void store.getState().findRoute()
    const signal = vi.mocked(api.fetchRoutes).mock.calls[0][2] as AbortSignal
    store.getState().reset()
    expect(signal.aborted).toBe(true)
  })

  it('warns when a route has a station the map does not know', async () => {
    const { api, store } = await readyWithBothStations()
    const strange = { ...ROUTE, stations: ['NEW_DELHI', 'NOWHERE', 'MANDI_HOUSE'] }
    vi.mocked(api.fetchRoutes).mockResolvedValue({ status: 'ok', routes: [strange] })
    vi.spyOn(console, 'error').mockImplementation(() => {})
    await store.getState().findRoute()
    expect(store.getState().drawIncomplete).toBe(true)
  })

  it('switching tabs only changes the selection, it does not ask the backend again', async () => {
    const { api, store } = await readyWithBothStations()
    vi.mocked(api.fetchRoutes).mockResolvedValue({ status: 'ok', routes: [ROUTE] })
    await store.getState().findRoute()
    store.getState().setMode('fewest_interchanges')
    expect(store.getState().mode).toBe('fewest_interchanges')
    expect(api.fetchRoutes).toHaveBeenCalledTimes(1)
  })
})
