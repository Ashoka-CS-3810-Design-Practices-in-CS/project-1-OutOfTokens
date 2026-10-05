# Next Steps — Building the Backend from Where We Are

A step-by-step guide for continuing the Delhi Metro Route Planner. Read `project context.md` first for the full design; this file says what to build next, in what order, and how to check each step.

## Where you are

| Part | State |
|---|---|
| `data/*.csv` | Present, and the row counts match (257 stations, 285 nodes, 301 edges: 272 ride + 29 walk) |
| `metro/network/models.py` | Written, but it doesn't match the design (see Step 1) |
| `graph.py`, `loader.py`, `validator.py`, all of `routing/`, `service/`, `api/`, `tests/` | Not written yet |
| `frontend/` | Not created yet |
| Git | No commits on `main` |

### Two problems in the data and setup

1. **`stations.csv` lost a column.** The last column header is `s` when it should be `coord_source`, and that column is empty in all 257 rows. Get the cleaned file back from wherever you made it, or fix the header and fill the column back in. You'll need it for the task of reviewing the 40 estimated coordinates.
2. **`src/backend/` was left behind by `uv init`.** It isn't part of the design. You can delete it, and delete the `[project.scripts]` section in `pyproject.toml` that points to it.

## Step 0: Make your first commit

Commit what you have on `main` now so you have a base to branch from. After that, start a new branch for each step below (`git switch -c network-layer`), and open a pull request when the step works.

## Step 1: Fix `models.py` to match the graph model

Your models describe a simpler graph where an edge joins two stations. The design (section 3 of the context file) says an edge joins two **nodes**, meaning a station on a particular line. Change these:

- **Add a `Node` class** with three string fields: `id`, `station_id`, `line_id`. The model has no class for nodes at the moment.
- **Change `Edge`** so it stores IDs (plain strings) instead of whole objects. Its fields should be `edge_id`, `from_node`, `to_node`, `kind` (`"ride"` or `"walk"`), `line_id` (can be `None`, because walk edges have no line), `distance_km`, `time_min`.
  - *Why IDs and not objects?* The graph keeps one dictionary of every node and looks things up by ID. If each edge carried its own copy of a Station, a station's data would be stored in many places at once.
  - *Why `kind`?* Without it you can't tell a ride from a walk. Fewest-interchanges, fewest-stations and the route builder all rely on that.
  - *Why `time_min`?* Every search uses it as the edge weight.
- **Change `RouteResult`**:
  - Add a `stations` field. The panel needs the ordered list of stations.
  - Make every list a `tuple[...]`. The class is frozen, but a list inside it can still be changed.
  - Store `lines` and `interchanges` as IDs (`tuple[str, ...]`), not objects. The JSON then stays simple.
  - Rename the totals to `total_time_min` and `total_distance_km` so the units are in the names.
- **`Line.color` vs. `colour`:** either spelling works, but the CSV uses `colour`. Choose one, and handle the difference in the loader if you keep `color`.

**Check:** open `uv run python` and create one of each class by hand. Then try to change a field. You should get a `FrozenInstanceError`.

## Step 2: `graph.py`, the container

Write a `MetroGraph` class that holds six dictionaries: `stations`, `lines`, `nodes`, `nodes_of_station`, `edges_by_id`, `adjacency`. Give it one method that adds an edge, and make that method do two things:

- store the edge in `edges_by_id`
- append it to the adjacency list of **both** `from_node` and `to_node`

That second point is what makes the graph undirected. Then add the three helpers:

- `edges_of(node_id)` returns `adjacency.get(node_id, [])`
- `lines_at(station_id)` gets each node of the station and collects its line
- `is_interchange(station_id)` returns whether the station has more than one node

**Watch out:** if you store the same Edge object in both directions, a search that reaches a node from `to_node` has to work out the far end itself: "the other end is `from_node` if I'm at `to_node`, otherwise `to_node`". Write a small helper for this, such as `other_end(edge, node_id)`. Getting this wrong is the most common bug in this kind of graph.

## Step 3: `loader.py`, CSV to graph

`load_graph(data_dir)` should:

1. Read the four files with `csv.DictReader`. Each row comes back as a dict keyed by the header names.
2. Read them in this order: lines, stations, nodes, edges. Each file refers to things defined in the earlier ones.
3. Convert the types yourself: `float(row["lat"])`, `float(row["distance_km"])`. An empty `line_id` becomes `None`.
4. Use `pathlib.Path` for paths so the code works on both Windows and Linux.

Next task #2, the duplicate-ID check, belongs here too. Before you insert anything, check whether the ID is already in the dict, and raise an error if it is.

**Check:** load the graph and print `len(graph.nodes)` (should be 285) and `len(graph.edges_by_id)` (should be 301). Also print `graph.lines_at("RAJIV_CHOWK")`, which should give Yellow and Blue.

## Step 4: `validator.py`

Write a `DataError` exception class. In `validate(graph)`, collect every problem in a list and raise **once** at the end, with all of them. That way one run shows you every problem at once. Go through the checks in the order section 5 of the context file gives them. For the connectivity check, start a BFS from any node and confirm it reaches all 285.

**Check:** the real data should pass. Then copy the data to a temp folder, break one row, and confirm the validator reports it.

## Step 5: Your first tests, then commit

Create `tests/test_routing.py`, starting with network tests only: the node and edge counts are right, the real data validates, and a broken edge raises `DataError`. Run `uv run pytest`. When it passes, commit, push, and open a pull request.

## Step 6: Routing, one file at a time

1. **`cost_models.py`**: a `Protocol` with `edge_cost(edge) -> float`, plus the two classes. `InterchangePenaltyCost` adds a big constant on walk edges. That constant makes the search avoid line changes before anything else, and uses time only to break ties.
2. **`dijkstra.py`**: put **every** node of the source station into the heap at cost 0. Push `(cost, counter, node)` onto the heap. The counter decides ties, so Python never has to compare two node strings. When you pop a node, skip it if it's already visited. Stop as soon as you pop a node whose `station_id` is the destination station. Save `prev[node] = (previous_node, edge_id)`, and write `trace_path` to follow `prev` back to the start and reverse the result.
   - **Check:** for Chandni Chowk → Rajiv Chowk you should get 3 ride edges.
3. **`zero_one_bfs.py`**: the same idea, but with a `collections.deque`. A walk costs 0 and goes to the front with `appendleft`. A ride costs 1 and goes to the back with `append`. A node can be reached more than once here, so skip it only when the new distance is no better than the one you already have.
4. **`route_builder.py`**: walk through the edge IDs in order while tracking your current node. Use the real `time_min`, not the cost model's number. That's how the 10,000 penalty stays out of what the user sees.
5. **`planner.py`**: run all three searches. Then group the results with a dict keyed by `tuple(edge_ids)`. Two criteria with the same key are the same route, so you show it once with both labels.

**Check after this step:** the known-good results in section 7 of the context file are now your tests:

- New Delhi → ITO gives 2 routes: 17.0 min / 6.8 km / 1 change (fastest + fewest interchanges), and 18.0 min / 3.6 km / 2 changes (fewest stations).
- Chandni Chowk → Rajiv Chowk: 4 stations, 0 changes, 6.0 min, 2.9 km.

Write each one as a test.

## Step 7: Service and API

- **`route_service.py`**: put input checks and the shape of the response here, not in the API file. The API layer only translates the request and response.
- **`schemas.py` and `main.py`**: load and validate the graph **once**, when the server starts. Turn `RouteError` into a 400 with an `HTTPException`.
- Add `httpx` as a dev dependency (`uv add --dev httpx`) so you can use FastAPI's `TestClient` in your tests.
- **Check:** run `uv run uvicorn metro.api.main:app --reload` and try both endpoints at `http://localhost:8000/docs`.

## Step 8: Frontend

Run `npm create vite@latest frontend -- --template react-ts`, then `npm install zustand`. Build in the order section 6 of the context file lists: `types.ts` → `apiClient.ts` → `routeStore.ts` → the components. Write `types.ts` by copying the actual JSON your API returns from `/docs`.

## Habits to keep

- Make one small change, then test it (`uv run pytest`), then commit. Don't start the next layer until the current one passes.
- Before every commit, check the import rules: nothing in `network/` imports from `routing/`, and nothing in `routing/` imports FastAPI.
- Work through the numbered tasks in section 9 of the context file only after Step 7 works end to end. Task #2 (duplicate IDs) is the exception: build it into Step 3.
