from itertools import combinations

from hypothesis import given, settings
from hypothesis import strategies as st

from metro.network.graph import MetroGraph
from metro.network.models import Edge, Line, Node, Station
from metro.routing.cost_models import InterchangePenaltyCost, TimeCost
from metro.routing.dijkstra import dijkstra
from metro.routing.route_builder import build_route
from metro.routing.zero_one_bfs import zero_one_bfs

# Random small maps: each search must match the best route found by trying every route.
# Only routes that never revisit a platform are tried; with no negative times, revisiting can't help.


@st.composite
def metro_maps(draw):
    # same rules as the real map: one node per station and line, walk edges between every pair of lines
    station_ids = [f"S{i}" for i in range(draw(st.integers(2, 6)))]
    line_count = draw(st.integers(1, 3))
    minutes = st.integers(1, 9).map(float)

    lines, nodes, edges = [], [], []
    for n in range(line_count):
        line_id = f"L{n}"
        stops = draw(st.lists(st.sampled_from(station_ids), min_size=2, max_size=len(station_ids), unique=True))
        lines.append(Line(id=line_id, name=line_id, colour="#000000"))
        for station_id in stops:
            nodes.append(Node(node_id=f"{station_id}@{line_id}", station_id=station_id, line_id=line_id))
        for i, (a, b) in enumerate(zip(stops, stops[1:])):
            edges.append(Edge(edge_id=f"{line_id}_{i}", line_id=line_id, from_node=f"{a}@{line_id}",
                              to_node=f"{b}@{line_id}", kind="ride",
                              distance_km=draw(minutes) / 2, travel_min=draw(minutes)))

    for station_id in station_ids:
        here = [node.node_id for node in nodes if node.station_id == station_id]
        for a, b in combinations(here, 2):
            edges.append(Edge(edge_id=f"WALK_{a}_{b}", line_id=None, from_node=a, to_node=b,
                              kind="walk", distance_km=0.0, travel_min=draw(minutes)))

    stations = [Station(id=s, name=s, lat=0.0, lon=0.0) for s in station_ids]
    graph = MetroGraph(stations=stations, lines=lines, nodes=nodes, edges=edges)
    source = draw(st.sampled_from(station_ids))
    destination = draw(st.sampled_from(station_ids))
    return graph, source, destination


def every_route(graph: MetroGraph, source: str, destination: str) -> list[list[str]]:
    # every route between the two stations that never revisits a platform, as lists of edge ids
    dest_nodes = set(graph.nodes_for_station(destination))
    found: list[list[str]] = []

    def walk_on(node_id: str, visited: set[str], path: list[str]) -> None:
        if node_id in dest_nodes:
            found.append(list(path))
            return
        for edge in graph.neighbours(node_id):
            if edge.to_node not in visited:
                visited.add(edge.to_node)
                path.append(edge.edge_id)
                walk_on(edge.to_node, visited, path)
                path.pop()
                visited.remove(edge.to_node)

    for start in graph.nodes_for_station(source):
        walk_on(start, {start}, [])
    return found


def minutes(graph: MetroGraph, edge_ids: list[str]) -> float:
    return sum(graph.edge(e).travel_min for e in edge_ids)


def changes(graph: MetroGraph, edge_ids: list[str]) -> int:
    return sum(graph.edge(e).kind == "walk" for e in edge_ids)


def rides(graph: MetroGraph, edge_ids: list[str]) -> int:
    return sum(graph.edge(e).kind == "ride" for e in edge_ids)


@settings(max_examples=400, deadline=None)
@given(metro_maps())
def test_searches_match_brute_force(case):
    graph, source, destination = case
    candidates = every_route(graph, source, destination)

    fastest = dijkstra(graph, TimeCost(), source, destination)
    fewest_changes = dijkstra(graph, InterchangePenaltyCost(), source, destination)
    fewest_stations = zero_one_bfs(graph, source, destination)

    if not candidates:
        # no route, and every search must say so
        assert fastest is None and fewest_changes is None and fewest_stations is None
        return

    # fastest: least total time
    assert minutes(graph, fastest) == min(minutes(graph, c) for c in candidates)
    # fewest interchanges: fewest changes, then least time
    assert (changes(graph, fewest_changes), minutes(graph, fewest_changes)) == min(
        (changes(graph, c), minutes(graph, c)) for c in candidates
    )
    # fewest stations: fewest rides
    assert rides(graph, fewest_stations) == min(rides(graph, c) for c in candidates)

    # each answer is a joined-up route and the route builder agrees with its totals
    for criterion, edge_ids in [("fastest", fastest), ("fewest_interchanges", fewest_changes),
                                ("fewest_stations", fewest_stations)]:
        route = build_route(graph, (criterion,), source, edge_ids)
        assert route.stations[0] == source
        assert route.stations[-1] == destination
        assert route.total_time_min == minutes(graph, edge_ids)
        assert len(route.interchanges) == changes(graph, edge_ids)
        assert len(route.stations) - 1 == rides(graph, edge_ids)
