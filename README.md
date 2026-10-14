# Delhi Metro Route Planner

A web app for Delhi Metro riders. Pick a start and a destination station and it shows up to three routes on an interactive map: the **fastest**, the one with the **fewest interchanges**, and the one with the **fewest stations**. A route that wins more than one of these is shown once with every label.

Course project for Design Practices in CS (CS-3810), Ashoka University. Team "Out of tokens": Parth Agarwal, Sehraj Magu.

## Layout

```
backend/    Python 3.12 + FastAPI: the graph, the search algorithms and the HTTP API
  data/     the network as four CSV files (the single source of truth)
  metro/    network/ -> routing/ -> service/ -> api/  (each layer only imports the ones before it)
  tests/
frontend/   React + TypeScript + Vite: station search, route panel and the SVG map
```

## Running it

You need [uv](https://docs.astral.sh/uv/) for the backend and Node.js 20+ for the frontend. Start the backend first, then the frontend, each in its own terminal.

```bash
# backend, from backend/
uv sync
uv run uvicorn metro.api.main:app --reload   # http://localhost:8000, API docs at /docs

# frontend, from frontend/
npm install
npm run dev                                   # http://localhost:5173
```

Open http://localhost:5173, choose two stations and press **Find route**.

### Configuration

| Variable | Where | Default | What it does |
|---|---|---|---|
| `VITE_API_URL` | `frontend/.env.local` | `http://localhost:8000` | Where the frontend sends API requests. See `frontend/.env.example`. |
| `FRONTEND_ORIGINS` | backend environment | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated origins allowed by CORS. Set it to the deployed frontend's origin. |

### Tests

```bash
cd backend && uv run pytest
cd frontend && npm run lint && npx tsc -b
```

## API

| Endpoint | Returns |
|---|---|
| `GET /api/network` | `data_version`, every station (id, name, lat, lon, lines), every line (id, name, colour, average speed) and every ride edge (id, line, from station, to station). |
| `POST /api/route` with `{"source": "NEW_DELHI", "destination": "ITO"}` | `status` (`ok` or `no_path`) and the distinct routes. Each route has its criteria, stations, lines, interchanges, edge ids, total time and total distance. Unknown or identical stations give HTTP 400 with an error code; a malformed body gives 422. |

`data_version` is a hash of the four CSV files, so the frontend can tell which data the backend is serving.

## Data

The network lives in `backend/data/` and is read once when the server starts. Adding a station, line or transfer means editing these files, not the code.

| File | Rows | Columns |
|---|---|---|
| `lines.csv` | 13 | `id, name, colour, avg_speed_kmh` |
| `stations.csv` | 257 | `id, name, code, lat, lon` |
| `nodes.csv` | 285 | `node_id, station_id, line_id` (one node per station and line, e.g. `RAJIV_CHOWK@BLUE`) |
| `edges.csv` | 301 | `edge_id, from_node, to_node, kind, line_id, distance_km, travel_min` (272 `ride`, 29 `walk`) |

A `ride` edge joins neighbouring stations on one line; a `walk` edge is a line change inside an interchange station. Every edge works in both directions.

Source: a public Delhi Metro dataset, cleaned by hand:

- Branch lines are separate lines (riders change trains at Yamuna Bank and Ashok Park Main).
- Two walkway-linked pairs are merged into one station each: Dhaula Kuan / Durgabai Deshmukh South Campus and Noida Sector 52 / Noida Sector 51.
- 40 broken coordinates were re-estimated along their line, and the Rapid Metro coordinates are schematic.

**Placeholders still in the data:**

- Every ride takes 2 minutes and every line change 5 minutes, whatever the distance. Real ride times (distance ÷ line speed + dwell time) and DMRC transfer times are still to come.
- `avg_speed_kmh` is 35 for every line, the agreed starting value.
- The `code` column is empty, so stations are searched by name only.

The background map in `frontend/src/data/delhiBasemap.json` is © OpenStreetMap contributors (ODbL); `frontend/scripts/build_basemap.py` rebuilds it.
