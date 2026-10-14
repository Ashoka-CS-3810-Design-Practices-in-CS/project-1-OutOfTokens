from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Station:
    id: str
    name: str
    lat: float
    lon: float

@dataclass(frozen=True)
class Line:
    id: str
    name: str
    colour: str  
    avg_speed_kmh: float | None = None  # from lines.csv; None in hand-built test graphs

@dataclass(frozen=True)
class Node:
    node_id: str  
    station_id: str
    line_id: str

@dataclass(frozen=True)
class Edge:
    edge_id: str
    line_id: str | None 
    from_node: str  
    to_node: str
    kind: Literal["ride", "walk"]  
    distance_km: float 
    travel_min: float  

@dataclass(frozen=True)
class RouteResult:
    stations: tuple[str, ...]  # station ids, in travel order
    criteria: tuple[str, ...]  # PEP 8: `tuple[str, ...]`
    edge_ids: tuple[str, ...]
    lines: tuple[str, ...]  # line ids, in the order they are used
    interchanges: tuple[str, ...]  # station ids where the rider changes line
    total_time_min: float  
    total_distance_km: float  