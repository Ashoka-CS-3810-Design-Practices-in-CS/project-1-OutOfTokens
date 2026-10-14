import type { Network, RouteResponse } from './types'

// the only file that talks to the backend.
// VITE_API_URL is set per environment (see .env.example); the default is the local dev server.
const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const TIMEOUT_MS = 5000

// a failed request, as a short code the store turns into a message:
// 'timeout', 'unreachable', 'cancelled', 'server_error', 'bad_request',
// or the backend's own code for a refused request (e.g. 'same_station')
export class ApiError extends Error {
  readonly code: string

  constructor(code: string) {
    super(code)
    this.code = code
  }
}

async function requestJson<T>(path: string, init: RequestInit = {}, signal?: AbortSignal): Promise<T> {
  const controller = new AbortController()
  let timedOut = false
  const timer = setTimeout(() => {
    timedOut = true
    controller.abort()
  }, TIMEOUT_MS)
  // the caller can cancel too, e.g. Reset while a route request is pending
  const cancel = () => controller.abort()
  signal?.addEventListener('abort', cancel)

  try {
    let response: Response
    try {
      response = await fetch(`${BASE_URL}${path}`, { ...init, signal: controller.signal })
    } catch {
      throw new ApiError(timedOut ? 'timeout' : controller.signal.aborted ? 'cancelled' : 'unreachable')
    }
    if (response.status >= 500) throw new ApiError('server_error')
    if (!response.ok) {
      // the backend sends {"error": "<code>"} for requests it refuses (HTTP 400)
      const body = await response.json().catch(() => null)
      throw new ApiError(typeof body?.error === 'string' ? body.error : 'bad_request')
    }
    return (await response.json()) as T
  } finally {
    clearTimeout(timer)
    signal?.removeEventListener('abort', cancel)
  }
}

export function fetchNetwork(): Promise<Network> {
  return requestJson<Network>('/api/network')
}

export function fetchRoutes(source: string, destination: string, signal?: AbortSignal): Promise<RouteResponse> {
  const init = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source, destination }),
  }
  return requestJson<RouteResponse>('/api/route', init, signal)
}
