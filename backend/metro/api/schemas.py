from pydantic import BaseModel


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


class EdgeOut(BaseModel):
    edge_id: str
    line_id: str
    from_id: str  # station id
    to_id: str    # station id


class NetworkOut(BaseModel):
    stations: list[StationOut]
    lines: list[LineOut]
    edges: list[EdgeOut]  # ride edges only, for drawing the lines on the map
