from dataclasses import dataclass

@dataclass(frozen=True)
class Station:
    id:str
    name:str
    code:str
    lat:float
    lon:float

@dataclass(frozen=True)
class Line:
    id:str
    name:str
    color:str

@dataclass(frozen=True)
class Edge:
    id:str
    line:Line
    station1:Station
    station2:Station
    distance:float

@dataclass(frozen=True)
class RouteResult:
    criteria: tuple[str,...]
    edge_ids: list[str]
    lines: list[Line]
    interchanges: list[Station]
    total_time: float
    total_distance: float

    