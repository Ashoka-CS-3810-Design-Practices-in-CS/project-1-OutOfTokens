# Backend

FastAPI service that loads the Delhi Metro network from `data/*.csv` and finds routes. See the [project README](../README.md) for the full picture.

## Run

```bash
uv sync
uv run uvicorn metro.api.main:app --reload   # http://localhost:8000, docs at /docs
uv run pytest                                # all tests
```

Set `FRONTEND_ORIGINS` (comma-separated) to change which origins CORS allows; the default is the Vite dev server on port 5173.

## Layers

Each package only imports the ones above it in this list:

| Package | Does |
|---|---|
| `metro/network` | Data models, CSV loader (`load_graph`, `data_version`) and `MetroGraph`. Bad data stops start-up with a message naming the file and line. |
| `metro/routing` | `dijkstra` with a cost model (fastest, fewest interchanges), `zero_one_bfs` (fewest stations), `build_route` and the `Planner` that runs all three and merges identical routes. No HTTP or JSON here. |
| `metro/service` | `RouteService`: checks station ids, calls the planner, and builds the network view for the frontend. |
| `metro/api` | FastAPI app, Pydantic schemas, CORS. `GET /api/network`, `POST /api/route`. |
