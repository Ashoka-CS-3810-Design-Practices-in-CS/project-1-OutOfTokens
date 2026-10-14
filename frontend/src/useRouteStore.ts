import { useStore } from 'zustand'
import { routeStore } from './routeStore'
import type { RouteState } from './routeStore'

// how components read the store; pick one value per call so a component only re-renders when that value changes
export function useRouteStore<T>(selector: (state: RouteState) => T): T {
  return useStore(routeStore, selector)
}
