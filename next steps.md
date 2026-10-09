# Next Steps — From Here to the Final Submission

The ordered list of everything left to build. Read `project context.md` first for the full design; this file says what to do next, in what order, and how to check each step.

Last updated: 9 Oct 2026. Deadlines: **Assignment 3 (Testing, UX, Development Plan) on 12 Oct**, **final project on 16 Oct**.

## Where we are

| Part | State |
|---|---|
| `data/*.csv` | Present: 13 lines, 257 stations, 285 nodes, 301 edges (272 ride + 29 walk) |
| `network/models.py`, `graph.py`, `loader.py` | Done and tested |
| `routing/cost_models.py` | Done and tested: `TimeCost` (fastest) and `InterchangePenaltyCost` (fewest line changes) |
| `routing/dijkstra.py` | Done and tested; matches the known-good results (New Delhi → ITO 17.0 min, Chandni Chowk → Rajiv Chowk 6.0 min) |
| `network/validator.py` | Not written |
| `routing/zero_one_bfs.py` | Done and tested; fewest stations (New Delhi → ITO: 4 rides, 2 changes, 18.0 min) |
| `routing/route_builder.py`, `planner.py` | Not written |
| `service/`, `api/` | Empty folders |
| `frontend/` | Not created |
| Tests | 41 passing (9 graph, 9 loader, 13 Dijkstra with both cost models, 10 fewest-stations search) |
| Git | Everything above is committed and pushed on `main`; cache files are no longer tracked |

## The order at a glance

| # | Step | Needed for |
|---|---|---|
| 0 | Fix the setup and agree the open decisions | Everything |
| 1 | Route builder | A working route |
| 2 | ~~Fewest-interchanges cost model~~ **Done** | Second criterion |
| 3 | ~~Fewest-stations search (0-1 BFS)~~ **Done** | Third criterion |
| 4 | Planner | Routing layer complete |
| 5 | Validator | Safe start-up |
| 6 | Service layer | API |
| 7 | API | Frontend |
| 8 | Frontend | **A working app, end to end** |
| 9 | Real data values | Correct answers |
| 10 | Fare | Feature in the brief |
| 11 | Deeper testing | Assignment 3 |
| 12 | Map pan/zoom and station popup | UX |
| 13 | Robustness and security | Final |
| 14 | CI | Final |
| 15 | Submission clean-up | Final |

Steps 0–8 give a working app and come first. Steps 9–15 improve it; if time runs short, do them in the order listed and drop from the bottom.

**Working in parallel:** Steps 1–7 are backend and Step 8 is frontend. The JSON the API returns is already fixed in section 5 of the context file, so one of us can start the frontend against that shape while the other finishes routing and the API.

---

## Step 0: Fix the setup and agree the open decisions

### Fix: `uv sync` fails on a fresh clone

`backend/pyproject.toml` still has a `[build-system]` section. It tells uv to package `src/backend/`, which was deleted, so `uv sync` stops with "Expected a Python module at: src/backend/__init__.py".

Delete these three lines:

```toml
[build-system]
requires = ["uv_build>=0.12.23,<0.13.0"]
build-backend = "uv_build"
```

Nothing else needs them: pytest finds the `metro` folder through `pythonpath = ["."]`.

**Check:** `uv sync` finishes, and `uv run pytest` reports 41 passed. Until this is fixed, run tests with `.venv/bin/python -m pytest` from `backend/`.

### Decide together before building further

Each of these changes code that later steps depend on, so settle them first.

1. **What `RouteResult` holds.** The code stores whole `Station` and `Line` objects. The design says IDs (`tuple[str, ...]`), which keeps the JSON simple. Decide before Step 1, because the route builder creates this object.
2. **`coord_source` column.** It was removed from `stations.csv`, so we can no longer tell which 40 coordinates were estimated. Restore it, or drop the "review estimated coordinates" task.
3. **Station codes.** `Station` has no `code` field and the CSV column is empty. The frontend search was designed to match on code as well as name. Add codes (Step 9) or search by name only.

### Already decided

**Ride times will be derived from distance.** Every ride edge has `travel_min = 2` today, whatever its length (0.3 km and 6.4 km both count as 2 minutes), so "fastest" currently means "2 × stops + 5 × changes". This gets fixed in Step 9. Until then, the known-good numbers (17.0, 18.0 and 6.0 minutes) are based on the flat 2 minutes.

### Bring the context file up to date

Section 5 of `project context.md` uses names the code doesn't. Fix them there so nobody builds against the wrong ones:

| Context file says | The code has |
|---|---|
| `Node.id` | `Node.node_id` |
| `Edge.time_min` | `Edge.travel_min` |
| `graph.edges_of(node)` | `graph.neighbours(node_id)` |
| `graph.nodes_of_station[...]` | `graph.nodes_for_station(station_id)` |
| `graph.lines_at()`, `graph.is_interchange()` | Not written yet (Step 1 needs something like them) |
| "expect 5 passed" | 41 passed |

### Working habit from here on

`main` now has real work on it. Start a branch for each step (`git switch -c route-builder`) and open a pull request for the other person to review.

---

## Step 1: `routing/route_builder.py`

Dijkstra returns edge IDs such as `['YELLOW_15', 'YELLOW_16', 'WALK_..._YELLOW_VIOLET', 'VIOLET_07']`. The route builder turns that into something a rider can read.

`build_route(graph, criteria, source, edge_ids)` walks the edges in order while tracking the node you are standing at:

- **Ride edge:** append the next station, and its line if it's a new one.
- **Walk edge:** record the current station as an interchange.
- **Throughout:** add up the real `travel_min` and `distance_km`, read from the edge itself.

**Watch out:** `graph.edge(edge_id)` gives the edge as written in the CSV, which may point against your direction of travel. Work out the far end yourself: "if I'm at `to_node`, the other end is `from_node`, otherwise it's `to_node`". Your starting node is whichever end of the first edge belongs to the source station.

**Check:** New Delhi → ITO gives 7 stations, lines Yellow then Violet, one interchange at Central Secretariat, 17.0 min, 6.8 km. Chandni Chowk → Rajiv Chowk gives 4 stations, 0 changes, 6.0 min, 2.9 km. Write both as tests.

## Step 2: `InterchangePenaltyCost` — done

A second class in `cost_models.py`: it returns `travel_min`, plus 100,000 when `edge.kind == "walk"`. Passing it to the existing `dijkstra` gives the fewest-interchanges route with no change to the algorithm. The penalty is so large that the search avoids line changes first and uses time only to break ties.

Still to remember for Step 1: the route builder must read times from the edges, not from the cost model, so the 100,000 never reaches the user.

**Checked by:** three tests in `tests/test_dijkstra.py`. On the small hand-built graph, a 13-minute route with no change beats a 12-minute route with one.

## Step 3: `routing/zero_one_bfs.py` — done

Fewest stations. Same shape as Dijkstra, but with a `collections.deque` in place of the heap: a ride costs 1 and goes to the back (`append`), a walk costs 0 and goes to the front (`appendleft`). It starts from every node of the source station and stops at the first node of the destination, as Dijkstra does. Call it as `zero_one_bfs(graph, source_station, dest_station)`; it returns edge IDs like `dijkstra` does.

**Checked by:** ten tests in `tests/test_zero_one_bfs.py`. New Delhi → ITO by fewest stations comes out as 4 rides and 2 changes in 18.0 min. The 3.6 km distance and the "via Rajiv Chowk and Mandi House" station list can only be checked once the route builder (Step 1) exists.

## Step 4: `routing/planner.py`

`Planner.plan(source, dest)` runs all three searches, builds a route from each, and groups the results in a dict keyed by `tuple(edge_ids)`. Two criteria with the same key are the same route, shown once with both labels. Return an empty list if there is no path.

**Check:** New Delhi → ITO returns two routes: one labelled fastest + fewest interchanges, one labelled fewest stations. This finishes the routing layer.

## Step 5: `network/validator.py`

`MetroGraph` already rejects most bad data as it builds (duplicate IDs, unknown references, rides crossing lines, walks crossing stations). The validator adds the three checks that are missing:

- every walk edge has distance 0
- every pair of lines at an interchange has a walk edge (Kashmere Gate has 3 lines, so 3 walk edges)
- the whole network is connected: a BFS from any node reaches all 285

Collect every problem in a list and raise one `DataError` at the end, so a single run shows everything that is wrong.

`MetroGraph` has no public way to list all nodes or all edges. Add `nodes` and `edges` properties to `graph.py`; Step 6 needs them too.

**Check:** the real data passes. Then break a copy (remove one walk edge) and confirm it is reported. The `data_copy` fixture in `tests/test_loader.py` does the copying.

## Step 6: `service/route_service.py`

Input checks and the shape of the response live here, not in the API file.

- `find_routes(source, destination)`: unknown station → `RouteError("unknown_station")`; same station → `RouteError("same_station")`; otherwise call the planner and return `{"status": "ok" | "no_path", "routes": [...]}`.
- `network_view()`: stations (with their lines), lines, and ride edges only, with node IDs translated to station IDs so the frontend can draw them.

## Step 7: `api/schemas.py` and `api/main.py`

- Load and validate the graph **once**, when the server starts.
- `GET /api/network` and `POST /api/route`.
- Turn `RouteError` into HTTP 400 with the error code. Allow CORS from `http://localhost:5173`.
- Add `httpx` as a dev dependency (`uv add --dev httpx`) so tests can use FastAPI's `TestClient`.

**Check:** `uv run uvicorn metro.api.main:app --reload`, then try both endpoints at `http://localhost:8000/docs`.

## Step 8: Frontend

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install zustand
```

Build in this order, each file depending only on the ones before it:

1. `types.ts`: copy the shapes from the real JSON at `/docs`.
2. `apiClient.ts`: the only file that makes network calls; 5-second timeout.
3. `routeStore.ts`: Zustand store; ignore stale responses using `requestSeq`.
4. `stationIndex.ts` and `mapGeometry.ts`: station search and lat/lon → SVG projection.
5. `StationSearch.tsx`, then `RoutePanel.tsx`, then `MetroMap.tsx`.
6. `App.tsx` and `index.css`.

**Check:** pick New Delhi and ITO in the browser, press Find Route, and see two routes in the panel with the selected one highlighted on the map. **This is the milestone: the app works end to end.**

---

## Step 9: Real data values

- Replace the 29 placeholder walk times (all 5 minutes) with DMRC transfer times.
- Replace the flat 2-minute ride times with times derived from distance: `time = distance ÷ average speed + dwell time per stop`. Agree the speed and dwell values first (35 km/h and 30 seconds is a starting point) and record them in the context file. This changes `edges.csv` only; the algorithms stay as they are.
- Station codes and the `coord_source` column, depending on the Step 0 decisions.

**Watch out:** changing any time changes the known-good numbers (17.0, 18.0 and 6.0 minutes) in the tests and in the context file. Update them in the same commit.

## Step 10: Fare

Calculate the fare from `total_distance_km` using the DMRC fare slabs, add it to the route response, and show it in `RoutePanel`.

## Step 11: Deeper testing

- 30 hand-verified station pairs as tests.
- `pytest-cov`, aiming for at least 80% on `network` and `routing`.
- A `hypothesis` test that builds random small graphs and compares Dijkstra with a brute-force search.

Assignment 3 covers testing, so the test plan and what is already tested (41 tests) should be written up by 12 Oct even if some of this is still in progress.

## Step 12: Map pan/zoom and station popup

- Pan and zoom with `d3-zoom`, plus a Reset View button. It must not re-render the map or touch the route state.
- A details popup when a station is clicked.

## Step 13: Robustness and security

- Rate limit of 60 requests a minute (`slowapi`), a 1 KB request body limit, and error handlers for 400, 413, 429 and 503.
- `apiClient`: one automatic retry, plus a manual Retry button.
- A data version hash sent with `/api/network`, so a frontend/backend mismatch is detected.
- All error messages the user sees are plain, non-technical sentences.

## Step 14: CI

GitHub Actions on every pull request: lint, type-check, the layer-import rules, and all tests.

## Step 15: Submission clean-up

- `backend/README.md` is empty: add how to install, run and test.
- A fresh clone must work by following the README alone. Test this on a clean folder.
- `project context.md` matches the final code.

---

## Habits to keep

- One small change, then test (`uv run pytest`), then commit. Don't start the next layer until the current one passes.
- Before every commit, check the import rules: nothing in `network/` imports from `routing/`, and nothing in `routing/` imports FastAPI.
- One branch and one pull request per step, reviewed by the other person.
