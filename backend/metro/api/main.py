import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..network.loader import data_version, load_graph
from ..network.validator import validate
from ..service.route_service import RouteError, RouteService
from .schemas import ErrorOut, NetworkOut, RouteRequest, RouteResponse

# Load and check the graph once when the server starts. If the CSVs are broken,
# load_graph or validate raises and the server refuses to start.
graph = load_graph()
validate(graph)
service = RouteService(graph, data_version())

app = FastAPI(title="Delhi Metro Route Planner")

# The frontend runs on a different origin, so the browser needs CORS to call us.
# FRONTEND_ORIGINS is a comma-separated list; the default is the Vite dev server.
FRONTEND_ORIGINS = os.environ.get("FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in FRONTEND_ORIGINS.split(",") if origin.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# what the rider sees for each RouteError code
ERROR_MESSAGES = {
    "unknown_station": "One of the stations wasn't recognised. Please pick it from the list.",
    "same_station": "The start and destination are the same station. Please pick two different stations.",
}


@app.exception_handler(RouteError)
def route_error(_: Request, exc: RouteError) -> JSONResponse:
    # a bad request the rider can fix, e.g. the same station twice
    message = ERROR_MESSAGES.get(exc.code, "That route request couldn't be answered.")
    return JSONResponse(status_code=400, content={"error": exc.code, "message": message})


@app.get("/api/network", response_model=NetworkOut)
def get_network() -> dict:
    """Stations with their coordinates and lines, the lines, and the ride edges between stations."""
    return service.network_view()


@app.post("/api/route", response_model=RouteResponse, responses={400: {"model": ErrorOut}})
def post_route(request: RouteRequest) -> dict:
    """The fastest, fewest-interchanges and fewest-stations routes. Identical routes come back once with every label."""
    return service.find_routes(request.source, request.destination)
