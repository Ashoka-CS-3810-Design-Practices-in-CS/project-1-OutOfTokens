from typing import Literal

from pydantic import BaseModel, Field


class StationOut(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    lines: list[str]  # line ids, e.g. ["YELLOW", "BLUE"] for Rajiv Chowk


class LineOut(BaseModel):
    id: str
    name: str
    colour: str
    avg_speed_kmh: float | None  # placeholder 35 km/h for every line until real values are agreed


class EdgeOut(BaseModel):
    edge_id: str
    line_id: str
    from_id: str  # station id
    to_id: str    # station id


class NetworkOut(BaseModel):
    data_version: str  # hash of the data files; changes whenever the network data changes
    stations: list[StationOut]
    lines: list[LineOut]
    edges: list[EdgeOut]  # ride edges only, for drawing the lines on the map


class RouteRequest(BaseModel):
    source: str = Field(min_length=1, max_length=100)       # station id, e.g. "NEW_DELHI"
    destination: str = Field(min_length=1, max_length=100)


class RouteOut(BaseModel):
    criteria: list[str]      # which searches found this route, e.g. ["fastest", "fewest_interchanges"]
    stations: list[str]      # station ids in travel order
    lines: list[str]         # line ids in the order they are used
    interchanges: list[str]  # station ids where the rider changes line
    edge_ids: list[str]      # ride and walk edges, in travel order
    total_time_min: float
    total_distance_km: float


class RouteResponse(BaseModel):
    status: Literal["ok", "no_path"]
    routes: list[RouteOut]


class ErrorOut(BaseModel):
    error: str    # machine-readable code, e.g. "unknown_station"
    message: str  # plain sentence to show the user
