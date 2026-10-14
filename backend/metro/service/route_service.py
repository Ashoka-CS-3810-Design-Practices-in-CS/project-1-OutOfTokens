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
    # checks requests and shapes the answers; the api layer only passes them through

    def __init__(self, graph: MetroGraph) -> None:
        self.graph = graph
        self.planner = Planner(graph)
        self.station_ids = {station.id for station in graph.stations}

    def find_routes(self, source: str, destination: str) -> dict:
        # {"status": "ok", "routes": [...]} or {"status": "no_path", "routes": []}
        # raises RouteError for a request that can't be answered
        if source not in self.station_ids or destination not in self.station_ids:
            raise RouteError("unknown_station")
        if source == destination:
            raise RouteError("same_station")

        routes = self.planner.plan(source, destination)
        if not routes:
            return {"status": "no_path", "routes": []}
        # asdict turns each RouteResult into a plain dictionary; its tuples become JSON arrays
        return {"status": "ok", "routes": [asdict(route) for route in routes]}

    def network_view(self) -> dict:
        # everything the frontend needs to draw the map
        return {
            "stations": [
                {
                    "id": station.id,
                    "name": station.name,
                    "lat": station.lat,
                    "lon": station.lon,
                    "lines": [self.graph.node(n).line_id for n in self.graph.nodes_for_station(station.id)],
                }
                for station in self.graph.stations
            ],
            "lines": [
                {"id": line.id, "name": line.name, "colour": line.colour}
                for line in self.graph.lines
            ],
            # ride edges only (line changes are not drawn), with node ids turned into station ids
            "edges": [
                {
                    "edge_id": edge.edge_id,
                    "line_id": edge.line_id,
                    "from_id": self.graph.node(edge.from_node).station_id,
                    "to_id": self.graph.node(edge.to_node).station_id,
                }
                for edge in self.graph.edges
                if edge.kind == "ride"
            ],
        }
