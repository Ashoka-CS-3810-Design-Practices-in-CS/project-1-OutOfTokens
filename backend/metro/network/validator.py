from collections import deque
from itertools import combinations

from .graph import MetroGraph


class DataError(ValueError):
    """Raised when the network breaks a rule that needs the whole graph to check. Lists every problem found."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__("Network data has problems:\n" + "\n".join(f"- {p}" for p in problems))
        self.problems = problems


def validate(graph: MetroGraph) -> None:
    """Check the rules that need the whole network at once, and raise one DataError listing every problem.

    MetroGraph already refuses duplicate ids, unknown references, rides across lines, walks across
    stations and impossible times while it is built, so those checks aren't repeated here.
    """
    problems = [*_walk_distances(graph), *_missing_walks(graph), *_unreachable(graph)]
    if problems:
        raise DataError(problems)


def _walk_distances(graph: MetroGraph) -> list[str]:
    # A line change stays inside one station, so it adds nothing to the distance (or the fare).
    return [
        f"Walk edge {edge.edge_id} has distance {edge.distance_km} km; a line change must be 0 km"
        for edge in graph.edges
        if edge.kind == "walk" and edge.distance_km != 0
    ]


def _missing_walks(graph: MetroGraph) -> list[str]:
    # Every pair of lines at an interchange needs a walk edge, otherwise the search can't change between them there.
    walked = {frozenset((edge.from_node, edge.to_node)) for edge in graph.edges if edge.kind == "walk"}
    return [
        f"Station {station.id} has no walk edge between {a} and {b}"
        for station in graph.stations
        for a, b in combinations(graph.nodes_for_station(station.id), 2)
        if frozenset((a, b)) not in walked
    ]


def _unreachable(graph: MetroGraph) -> list[str]:
    # Breadth-first search from the first node; every other node should be reached.
    all_nodes = [node_id for station in graph.stations for node_id in graph.nodes_for_station(station.id)]
    seen = set(all_nodes[:1])
    queue = deque(all_nodes[:1])
    while queue:
        node_id = queue.popleft()
        for edge in graph.neighbours(node_id):
            if edge.to_node not in seen:
                seen.add(edge.to_node)
                queue.append(edge.to_node)

    cut_off = [node_id for node_id in all_nodes if node_id not in seen]
    if not cut_off:
        return []
    return [f"{len(cut_off)} node(s) can't be reached from {all_nodes[0]}: {', '.join(cut_off)}"]
