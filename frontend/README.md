# Frontend

React + TypeScript + Vite app: station search, route panel and an SVG map of the network. See the [project README](../README.md) for the full picture.

## Run

```bash
npm install
npm run dev      # http://localhost:5173 (the backend must be running on :8000)
npm run lint
npm run build
```

Copy `.env.example` to `.env.local` to point the app at a different backend (`VITE_API_URL`).

## Structure

| File | Does |
|---|---|
| `src/apiClient.ts` | The only module that makes network requests. 5 s timeout, cancellable, and failures come back as short error codes. |
| `src/routeStore.ts` | Zustand store (plain TypeScript, no React): network, chosen stations, routes, selected route, request status. Stale replies are ignored. |
| `src/stationIndex.ts` | Station search (plain TypeScript): names starting with the query first, then names containing it, at most 8. |
| `src/mapGeometry.ts` | Projects lat/lon into SVG coordinates (plain TypeScript). |
| `src/messages.ts` | Every user-facing error message (ER1–ER9). |
| `src/components/` | `StationSearch`, `RouteModeTabs`, `RouteDetails`, `MetroMap` (pan/zoom with d3-zoom), `StationPopup`, `BaseMap`. |

ESLint enforces that `routeStore`, `stationIndex` and `mapGeometry` import no React (and the first two no D3), and that only `apiClient` calls `fetch`.
