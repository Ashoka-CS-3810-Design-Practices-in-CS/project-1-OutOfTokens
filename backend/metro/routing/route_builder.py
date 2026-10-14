from ..network.graph import MetroGraph
from ..network.models import Edge, RouteResult


def build_route(graph: MetroGraph, criteria: tuple[str, ...], source_station: str, edge_ids: list[str]) -> RouteResult:
    # turns the list of edge ids from a search into a route a rider can read

    stations: list[str] = [source_station]   # station ids in travel order, starting at the source
    lines: list[str] = []                     # line ids in the order they are used
    interchanges: list[str] = []              # station ids where the rider changes line
    total_time = 0.0                          # minutes
    total_distance = 0.0                      # kilometres

    current_node = start_node(graph, source_station, edge_ids) # the node the rider is standing on

    for edge_id in edge_ids:
        edge = graph.edge(edge_id)
        here = graph.node(current_node)                    # node the rider is on before this edge
        there = graph.node(other_end(edge, current_node))  # node the rider is on after this edge

        if edge.kind == "ride":
            stations.append(there.station_id)
            if edge.line_id not in lines:
                lines.append(edge.line_id)

        if edge.kind == "walk":
            interchanges.append(here.station_id)

        total_time += edge.travel_min
        total_distance += edge.distance_km

        current_node = there.node_id # the rider is now standing on the far end

    return RouteResult(
        stations=tuple(stations),
        criteria=criteria,
        edge_ids=tuple(edge_ids),
        lines=tuple(lines),
        interchanges=tuple(interchanges),
        total_time_min=total_time,
        total_distance_km=total_distance,
    )


def start_node(graph: MetroGraph, source_station: str, edge_ids: list[str]) -> str | None:
    # the node the rider starts on: whichever end of the first edge is at the source station
    if not edge_ids:
        return None
    first = graph.edge(edge_ids[0])
    if graph.node(first.from_node).station_id == source_station:
        return first.from_node
    if graph.node(first.to_node).station_id == source_station:
        return first.to_node
    raise ValueError(f"Edge {first.edge_id} does not start at station {source_station}")


def other_end(edge: Edge, node_id: str) -> str:
    # graph.edge() gives the edge as written in the csv, which may point against the direction
    # of travel, so work out the far end from the node the rider is standing on
    if node_id == edge.from_node:
        return edge.to_node
    if node_id == edge.to_node:
        return edge.from_node
    raise ValueError(f"Edge {edge.edge_id} does not touch node {node_id}")
