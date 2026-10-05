# Delhi Metro Route Planner — Project Context

Read this file first. It explains what the project is, how the code is designed, what exists, and what to do next.

## 1. What the app does

A web app for Delhi Metro riders. The user picks a **source** and **destination** station. The app shows up to three routes on an interactive map plus a side panel:

- **Fastest** (least total time)
- **Fewest interchanges** (fewest line changes)
- **Fewest stations** (fewest stops)

If two criteria produce the identical route, it is shown once with both labels.

For each route the panel shows: ordered stations, lines used, interchange stations, total time (min), total distance (km, for the fare), number of changes.

Course: Design Practices in CS (CS-3810), Ashoka University. Team "Out of tokens" (Parth Agarwal, Sehraj Magu).
Deadlines: Assignment 3 (Testing, UX, Development Plan) 12 Oct 2026; final project 16 Oct 2026.

## 2. Architecture (must be kept)

Client–server, layered. The backend holds the graph and algorithms; the frontend only draws results.

```
frontend (React + TypeScript, Vite)          backend (Python 3.12, FastAPI)
  components  -> routeStore -> apiClient  ==HTTP/JSON==>  api -> service -> routing -> network -> data/*.csv
```

Layer rules (do not break):
- `metro/routing` imports only `metro/network`. Never HTTP, JSON or UI code.
- `metro/network` imports nothing else from the project.
- Only `frontend/src/apiClient.ts` makes network calls.
- React components contain no routing logic.
- Network data lives in CSV files, never hard-coded.

## 3. The graph model (core idea)

- Every **station** gets one **node per line** that serves it. Node ID format: `STATION_ID@LINE_ID`.
  - Chandni Chowk (1 line) → `CHANDNI_CHOWK@YELLOW`
  - Rajiv Chowk (2 lines) → `RAJIV_CHOWK@YELLOW`, `RAJIV_CHOWK@BLUE`
- Two edge kinds, all undirected:

| kind | joins | distance_km | travel_min (the weight) |
|------|-------|-------------|--------------------------|
| `ride` | neighbouring stations on the same line | real track distance | 2 |
| `walk` | two line-nodes inside one interchange | 0 | transfer time (placeholder 5) |

- Every pair of lines at an interchange has a walk edge (Kashmere Gate has 3 lines → 3 walk edges).
- The search weight is always `travel_min`. `distance_km` is summed separately for the fare.
- A search starts from **all** nodes of the source station at cost 0 (boarding is free) and stops at the first node of the destination station it finalises.

## 4. Data files (`backend/data/`)

Source: public Delhi Metro dataset (285 rows, 13 lines), cleaned.

| File | Rows | Columns |
|------|------|---------|
| `lines.csv` | 13 | `id,name,colour` |
| `stations.csv` | 257 | `id,name,code,lat,lon,coord_source` |
| `nodes.csv` | 285 | `node_id,station_id,line_id` |
| `edges.csv` | 301 (272 ride + 29 walk) | `edge_id,from_node,to_node,kind,line_id,distance_km,travel_min` |

Line IDs: `RED, YELLOW, BLUE, BLUE_BRANCH, GREEN, GREEN_BRANCH, VIOLET, MAGENTA, PINK, AQUA, GRAY, ORANGE, RAPID`.
Edge IDs: rides `YELLOW_15`; walks `WALK_KASHMERE_GATE_RED_YELLOW`. Walk edges have an empty `line_id`.

Cleaning decisions:
- Branch lines are separate lines (riders change trains at Yamuna Bank and Ashok Park Main).
- Two walkway-linked pairs are merged into one station each: "Dhaula Kuan / Durgabai Deshmukh South Campus", "Noida Sector 52 / Noida Sector 51".
- 40 broken coordinates were re-estimated along their line; `coord_source` is `dataset`, `interpolated`, `extrapolated` or `schematic` (Rapid Metro is schematic).

**Placeholders still to replace:** all 29 walk `travel_min` = 5 (need DMRC values); `code` column is empty (dataset has no codes).

## 5. Backend files and what each does

```
backend/
  pyproject.toml          # uv project; [tool.pytest.ini_options] pythonpath = ["."]
  data/*.csv
  metro/
    network/  models.py graph.py loader.py validator.py
    routing/  cost_models.py dijkstra.py zero_one_bfs.py route_builder.py planner.py
    service/  route_service.py
    api/      schemas.py main.py
  tests/test_routing.py
```

**network/models.py** — frozen dataclasses: `Station(id,name,code,lat,lon)`, `Line(id,name,colour)`, `Node(id,station_id,line_id)`, `Edge(edge_id,from_node,to_node,kind,line_id,distance_km,time_min)`, `RouteResult(criteria,edge_ids,stations,lines,interchanges,total_time_min,total_distance_km)`. RouteResult sequences are tuples (immutable by design; JSON turns them into arrays).

**network/graph.py** — `MetroGraph` with dicts `stations`, `lines`, `nodes`, `nodes_of_station` (station → its node IDs), `edges_by_id`, `adjacency` (node → edges; every edge stored in both directions with the same edge_id). Helpers: `edges_of(node)`, `lines_at(station)`, `is_interchange(station)`.

**network/loader.py** — `load_graph(data_dir)` reads the 4 CSVs into models and returns a `MetroGraph`.

**network/validator.py** — `validate(graph)` raises `DataError` listing all problems: unknown station/line/node refs, negative time or distance, ride must stay on one line, walk must stay in one station with distance 0, every pair of lines at an interchange needs a walk edge, all nodes connected (BFS). Server refuses to start if this fails.

**routing/cost_models.py** — `CostModel` protocol with `edge_cost(edge)`. `TimeCost` = `edge.time_min`. `InterchangePenaltyCost` = time + 10,000 on walk edges.

**routing/dijkstra.py** — `dijkstra(graph, cost, source_station, dest_station)` → list of edge IDs or `None`. Binary heap (`heapq`) with a counter tie-breaker and lazy deletion (skip visited). `trace_path(prev, end)` rebuilds the edge list from `prev[node] = (previous_node, edge_id)`.

**routing/zero_one_bfs.py** — fewest stations: ride = 1, walk = 0; deque, 0-cost to front, 1-cost to back.

**routing/route_builder.py** — `build_route(graph, criteria, source, edge_ids)` walks the edges in order: walk edge → record interchange at current station; ride edge → append next station and its line (if new). Sums real `time_min` and `distance_km` (so the 10,000 penalty never reaches the user).

**routing/planner.py** — `Planner.plan(source, dest)` runs fastest, fewest_interchanges, fewest_stations; groups identical edge lists; returns `list[RouteResult]` (empty if no path).

**service/route_service.py** — `RouteService.find_routes` validates (unknown station → `RouteError("unknown_station")`, same station → `RouteError("same_station")`), calls Planner, returns `{"status": "ok"|"no_path", "routes": [...]}`. `network_view()` returns stations (with their lines), lines, and **ride edges only** with `from_id`/`to_id` translated to station IDs (for drawing).

**api/schemas.py** — Pydantic `RouteRequest(source, destination)`, each 1–100 chars.

**api/main.py** — loads + validates graph once at start-up; FastAPI app; CORS allows `http://localhost:5173`.
- `GET /api/network` → network view
- `POST /api/route` body `{"source": "NEW_DELHI", "destination": "ITO"}` → routes; `RouteError` → HTTP 400 with the code; bad body → 422.

## 6. Frontend files (`frontend/src/`)

- `types.ts` — TS interfaces mirroring the API JSON (`Station`, `Line`, `Edge`, `Network`, `Route`, `RouteResponse`).
- `apiClient.ts` — `fetchNetwork()`, `fetchRoutes()` with 5 s timeout via `AbortController`. Base URL `http://localhost:8000`.
- `routeStore.ts` — Zustand store: network, source, destination, routes, selected, status, message, `requestSeq`. Every request and every reset bumps `requestSeq`; stale responses are ignored.
- `stationIndex.ts` — `searchStations()`: case-insensitive substring match on name, exact match on code, prefix matches first, max 8.
- `mapGeometry.ts` — projects lat/lon into an 800×600 SVG (north up).
- `components/StationSearch.tsx` — search box; a station can only be chosen from suggestions.
- `components/RoutePanel.tsx` — one button per route; shows time, km, changes, lines, station list.
- `components/MetroMap.tsx` — SVG: one `<line>` per ride edge in line colour; selected route's edges thicker, others faded; source/destination and interchanges marked.
- `App.tsx` — layout, Find Route (disabled until both chosen), Reset. `index.css` — two columns, stacks under 700 px.

## 7. How to run and test

```bash
# backend (from backend/)
uv sync
uv run pytest                                   # expect 5 passed
uv run uvicorn metro.api.main:app --reload      # http://localhost:8000/docs

# frontend (from frontend/)
npm install
npm run dev                                     # http://localhost:5173
```

Known-good results (current data): New Delhi → ITO gives two routes —
fastest + fewest_interchanges: via Central Secretariat, 17.0 min, 6.8 km, 1 change;
fewest_stations: via Rajiv Chowk and Mandi House, 18.0 min, 3.6 km, 2 changes.
Chandni Chowk → Rajiv Chowk: 4 stations, 0 changes, 6.0 min, 2.9 km.

## 8. Current status

- The full design above was built and tested in a reference copy: the validator passes, 5 pytest tests pass, the API works, and the frontend compiles.
- In the team repo the code is being added step by step. **Check which files exist before assuming.** If a file is missing, create it to match section 5/6.
- `routing/state_space.py` and `transfers.csv` belong to an older design and must NOT exist.

## 9. Next tasks (in order)

1. Replace the 5-minute placeholder walk times with DMRC transfer times; add station codes; review the 40 estimated coordinates.
2. Add a duplicate-ID check in the loader.
3. Fare calculation from `total_distance_km` (DMRC fare slabs) and show it in RoutePanel.
4. Tests: reach 30 hand-verified station pairs; add `pytest-cov` (target ≥80% on network + routing); `hypothesis` random-graph test comparing Dijkstra with brute force.
5. Pan/zoom with `d3-zoom` + Reset View button (must not re-render the map or touch route state).
6. Station details popup on click.
7. Security: rate limit 60/min (`slowapi`), 1 KB body limit, error handlers 400/413/429/503.
8. `apiClient`: one automatic retry + manual Retry button.
9. Data version hash sent with `/api/network` to detect frontend/backend mismatch.
10. GitHub Actions CI: lint, type-check, layer-import rules, all tests.

## 10. Rules for any agent working on this

- Keep the graph model in section 3 and the layer rules in section 2. Ask before changing either.
- The user is learning: make small changes, explain each one in plain language, and run `uv run pytest` after backend changes.
- User-facing error messages must be plain, non-technical sentences.
- Commit after each working step with a clear message; work on feature branches and open pull requests for the teammate to review.