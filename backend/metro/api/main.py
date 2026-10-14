from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..network.loader import load_graph
from ..service.route_service import RouteService
from .schemas import NetworkOut

# Load the graph once when the server starts. If the CSVs are broken,
# load_graph raises and the server refuses to start.
service = RouteService(load_graph())

app = FastAPI(title="Delhi Metro Route Planner")

# The Vite dev server runs on a different port, so the browser needs CORS to call us.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/network", response_model=NetworkOut)
def get_network() -> dict:
    """Stations with their coordinates and lines, the lines, and the ride edges between stations."""
    return service.network_view()
