import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, fetchNetwork, fetchRoutes } from './apiClient'

// fetch is replaced with a stand-in, so every kind of reply (or none) can be tried

function reply(status: number, body: unknown): Response {
  return new Response(typeof body === 'string' ? body : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

// a fetch that never answers on its own, only fails when the request is cancelled
function hangingFetch() {
  return vi.fn(
    (_url: string, init?: RequestInit) =>
      new Promise<Response>((_resolve, reject) => {
        init?.signal?.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')))
      }),
  )
}

async function codeOf(promise: Promise<unknown>): Promise<string> {
  try {
    await promise
  } catch (error) {
    expect(error).toBeInstanceOf(ApiError)
    return (error as ApiError).code
  }
  throw new Error('expected the request to fail')
}

afterEach(() => {
  vi.unstubAllGlobals()
  vi.useRealTimers()
})

describe('apiClient', () => {
  it('fetches the network from GET /api/network', async () => {
    const fetchMock = vi.fn().mockResolvedValue(reply(200, { stations: [] }))
    vi.stubGlobal('fetch', fetchMock)
    await expect(fetchNetwork()).resolves.toEqual({ stations: [] })
    expect(fetchMock.mock.calls[0][0]).toMatch(/\/api\/network$/)
  })

  it('sends the two station codes as JSON to POST /api/route', async () => {
    const fetchMock = vi.fn().mockResolvedValue(reply(200, { status: 'ok', routes: [] }))
    vi.stubGlobal('fetch', fetchMock)
    await fetchRoutes('NEW_DELHI', 'ITO')
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toMatch(/\/api\/route$/)
    expect(init.method).toBe('POST')
    expect(init.headers).toEqual({ 'Content-Type': 'application/json' })
    expect(JSON.parse(init.body)).toEqual({ source: 'NEW_DELHI', destination: 'ITO' })
  })

  it("passes on the backend's own reason for refusing a request", async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reply(400, { error: 'same_station', message: '...' })))
    expect(await codeOf(fetchRoutes('ITO', 'ITO'))).toBe('same_station')
  })

  it('calls a refusal with no reason a bad request', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reply(422, 'not json')))
    expect(await codeOf(fetchRoutes('A', 'B'))).toBe('bad_request')
  })

  it('reports a server failure', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reply(503, {})))
    expect(await codeOf(fetchNetwork())).toBe('server_error')
  })

  it('reports an unreachable server', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    expect(await codeOf(fetchNetwork())).toBe('unreachable')
  })

  it('gives up after 5 seconds', async () => {
    vi.useFakeTimers()
    vi.stubGlobal('fetch', hangingFetch())
    const pending = codeOf(fetchNetwork())
    await vi.advanceTimersByTimeAsync(4999)
    let settled = false
    pending.then(() => (settled = true))
    await Promise.resolve()
    expect(settled).toBe(false)
    await vi.advanceTimersByTimeAsync(1)
    expect(await pending).toBe('timeout')
  })

  it('can be cancelled by the caller', async () => {
    vi.stubGlobal('fetch', hangingFetch())
    const controller = new AbortController()
    const pending = codeOf(fetchRoutes('A', 'B', controller.signal))
    controller.abort()
    expect(await pending).toBe('cancelled')
  })
})
