
from collections import defaultdict
from dataclasses import replace
from collections.abc import Iterable
from .models import Station, Line, Node, Edge


class GraphError(ValueError):
    """Raised when the graph data is inconsistent (duplicate ids, edges pointing at missing nodes, etc.)."""
    pass

class MetroGraph:
   
    def __init__(self, stations: Iterable[Station], lines: Iterable[Line], nodes: Iterable[Node], edges: Iterable[Edge]) -> None:
        self._stations: dict[str, Station] = {}   # "RAJIV_CHOWK"        -> Station(...)
        self._lines: dict[str, Line] = {}         # "BLUE"               -> Line(...)
        self._nodes: dict[str, Node] = {}         # "RAJIV_CHOWK@BLUE"   -> Node(...)
        self._edges: dict[str, Edge] = {}         # "BLUE_12"            -> Edge(...) exactly as in the CSV

        self._adjacency: dict[str, list[Edge]] = defaultdict(list)

        self._station_nodes: dict[str, list[str]] = defaultdict(list)

        # a) stations -> self._stations
        for station in stations:
            if station.id in self._stations:
                raise GraphError(f"Duplicate station id: {station.id}")
            self._stations[station.id] = station

        # b) lines -> self._lines
        for line in lines:
            if line.id in self._lines:
                raise GraphError(f"Duplicate line id: {line.id}")
            self._lines[line.id] = line

        # c) nodes -> self._nodes
        for node in nodes:
            if node.node_id in self._nodes:
                raise GraphError(f"Duplicate node id: {node.node_id}")
            if node.station_id not in self._stations:
                raise GraphError(f"Node {node.node_id} references unknown station id: {node.station_id}")
            if node.line_id not in self._lines:
                raise GraphError(f"Node {node.node_id} references unknown line id: {node.line_id}")
            self._nodes[node.node_id] = node
            self._station_nodes[node.station_id].append(node.node_id)

        # d) edges -> self._edges and _add_edge
        for edge in edges:
            if edge.edge_id in self._edges:
                raise GraphError(f"Duplicate edge id: {edge.edge_id}")
            if edge.from_node not in self._nodes or edge.to_node not in self._nodes:
                raise GraphError(f"Edge {edge.edge_id} references unknown nodes: {edge.from_node}, {edge.to_node}")
            if edge.kind == "ride" and edge.line_id is None:
                raise GraphError(f"Ride edge {edge.edge_id} must have a line_id")
            if edge.kind == "walk" and edge.line_id is not None:
                raise GraphError(f"Walk edge {edge.edge_id} must have no line_id")
            from_node = self._nodes[edge.from_node]
            to_node = self._nodes[edge.to_node]
            if edge.kind == "ride" and (from_node.line_id != edge.line_id or to_node.line_id != edge.line_id):
                raise GraphError(f"Ride edge {edge.edge_id} connects nodes on different lines")
            if edge.kind == "walk" and from_node.station_id != to_node.station_id:
                raise GraphError(f"Walk edge {edge.edge_id} connects nodes at different stations")
            if edge.travel_min <= 0 or edge.distance_km < 0:
                raise GraphError(f"Edge {edge.edge_id} has invalid travel time or distance")
            # All checks passed, so store it and wire it into the graph.
            self._edges[edge.edge_id] = edge
            self._add_edge(edge)

    def _add_edge(self, edge: Edge) -> None:
        # The CSV lists each connection once, but trains and interchange walks
        # go both ways, so store it under both endpoints.
        self._adjacency[edge.from_node].append(edge)
        reverse = replace(edge, from_node=edge.to_node, to_node=edge.from_node)
        self._adjacency[reverse.from_node].append(reverse)
        # `reverse` keeps the same edge_id, so it is NOT added to self._edges:
        # that would overwrite the original. _edges has one entry per
        # physical connection.

    # --- Lookups by id -------------------------------------------------------

    def station(self, station_id: str) -> Station:
        try:
            return self._stations[station_id]
        except KeyError:
            raise KeyError(f"Unknown station id: {station_id}") from None

    def line(self, line_id: str) -> Line:
        try:
            return self._lines[line_id]
        except KeyError:
            raise KeyError(f"Unknown line id: {line_id}") from None

    def node(self, node_id: str) -> Node:
        try:
            return self._nodes[node_id]
        except KeyError:
            raise KeyError(f"Unknown node id: {node_id}") from None

    def edge(self, edge_id: str) -> Edge:
        try:
            return self._edges[edge_id]
        except KeyError:
            raise KeyError(f"Unknown edge id: {edge_id}") from None

    # --- Traversal (used by metro/routing) -----------------------------------

    def neighbours(self, node_id: str) -> tuple[Edge, ...]:
        """Edges leaving `node_id`, in both directions of travel."""
        if node_id not in self._nodes:
            raise KeyError(f"Unknown node id: {node_id}")
        # .get() rather than [] so looking up a node with no edges doesn't add
        # an empty entry to the defaultdict. The tuple stops callers from
        # mutating the graph's internal list.
        return tuple(self._adjacency.get(node_id, ()))

    def nodes_for_station(self, station_id: str) -> tuple[str, ...]:
        """All node ids at a station (one per line), for station-to-station routing."""
        if station_id not in self._stations:
            raise KeyError(f"Unknown station id: {station_id}")
        return tuple(self._station_nodes.get(station_id, ()))

    # --- Listing and search --------------------------------------------------

    @property
    def stations(self) -> tuple[Station, ...]:
        return tuple(self._stations.values())

    @property
    def lines(self) -> tuple[Line, ...]:
        return tuple(self._lines.values())

    @property
    def edges(self) -> tuple[Edge, ...]:
        # one entry per connection, in the direction written in the CSV
        return tuple(self._edges.values())

    def find_station_by_name(self, name: str) -> Station | None:
        """Case-insensitive exact match on the station name, e.g. "rajiv chowk"."""
        wanted = name.strip().casefold()
        for station in self._stations.values():
            if station.name.casefold() == wanted:
                return station
        return None

    # --- Dunder methods ------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"MetroGraph(stations={len(self._stations)}, lines={len(self._lines)}, "
            f"nodes={len(self._nodes)}, edges={len(self._edges)})"
        )

    def __contains__(self, node_id: object) -> bool:
        return node_id in self._nodes
