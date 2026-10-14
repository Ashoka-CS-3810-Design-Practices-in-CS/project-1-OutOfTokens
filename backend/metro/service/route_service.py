from ..network.graph import MetroGraph


class RouteService:
    """Sits between the API and the graph: turns graph objects into plain data for the frontend."""

    def __init__(self, graph: MetroGraph) -> None:
        self._graph = graph

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
        lines = [{"id": line.id, "name": line.name, "colour": line.colour} for line in graph.lines]
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
        return {"stations": stations, "lines": lines, "edges": edges}
