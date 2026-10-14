from dataclasses import asdict

from ..network.graph import MetroGraph
from ..routing.planner import Planner


class RouteError(Exception):
    # a request the service refuses. `code` is the short reason the api sends back,
    # "unknown_station" or "same_station"

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class RouteService:
    """Sits between the API and the graph: checks requests and turns graph objects into plain data for the frontend."""

    def __init__(self, graph: MetroGraph, data_version: str = "") -> None:
        self._graph = graph
        self._data_version = data_version  # hash of the CSVs the graph was loaded from
        self._planner = Planner(graph)
        self._station_ids = {station.id for station in graph.stations}

    def find_routes(self, source: str, destination: str) -> dict:
        # {"status": "ok", "routes": [...]} or {"status": "no_path", "routes": []}
        # raises RouteError for a request that can't be answered
        if source not in self._station_ids or destination not in self._station_ids:
            raise RouteError("unknown_station")
        if source == destination:
            raise RouteError("same_station")

        routes = self._planner.plan(source, destination)
        if not routes:
            return {"status": "no_path", "routes": []}
        # asdict turns each RouteResult into a plain dictionary; its tuples become JSON arrays
        return {"status": "ok", "routes": [asdict(route) for route in routes]}

    def network_view(self) -> dict:
        """Everything the frontend needs to draw the map.

        Only ride edges are included, with node ids swapped for station ids,
        because walk edges stay inside one station and have nothing to draw.
        """
        graph = self._graph
        stations = [
            {
                "id": s.id,
                "name": s.name,
                "lat": s.lat,
                "lon": s.lon,
                "lines": list(graph.lines_at(s.id)),
            }
            for s in sorted(graph.stations, key=lambda s: s.name.casefold())
        ]
        lines = [
            {"id": line.id, "name": line.name, "colour": line.colour, "avg_speed_kmh": line.avg_speed_kmh}
            for line in graph.lines
        ]
        edges = [
            {
                "edge_id": e.edge_id,
                "line_id": e.line_id,
                "from_id": graph.node(e.from_node).station_id,
                "to_id": graph.node(e.to_node).station_id,
            }
            for e in graph.edges
            if e.kind == "ride"
        ]
        return {"data_version": self._data_version, "stations": stations, "lines": lines, "edges": edges}
