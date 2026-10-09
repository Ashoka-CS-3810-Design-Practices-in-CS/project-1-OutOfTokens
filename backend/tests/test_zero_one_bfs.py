import pytest

from metro.network.graph import MetroGraph
from metro.network.loader import load_graph
from metro.network.models import Edge, Line, Node, Station
from metro.routing.zero_one_bfs import zero_one_bfs


def build(*edge_specs: tuple[str, str, str]) -> MetroGraph:
    #builds a small test map from (edge id, from node, to node), where a node is written "STATION@LINE"
    #two nodes at the same station are joined by a line change, anything else is a train ride

    node_ids = sorted({node_id for _, a, b in edge_specs for node_id in (a, b)})
    nodes = [Node(node_id=n, station_id=n.split("@")[0], line_id=n.split("@")[1]) for n in node_ids]
    stations = [Station(id=s, name=s, lat=0.0, lon=0.0) for s in sorted({n.station_id for n in nodes})]
    lines = [Line(id=l, name=l, colour="#000000") for l in sorted({n.line_id for n in nodes})]

    edges = []
    for edge_id, a, b in edge_specs:
        if a.split("@")[0] == b.split("@")[0]:
            edges.append(Edge(edge_id=edge_id, line_id=None, from_node=a, to_node=b,
                              kind="walk", distance_km=0.0, travel_min=5.0))
        else:
            edges.append(Edge(edge_id=edge_id, line_id=a.split("@")[1], from_node=a, to_node=b,
                              kind="ride", distance_km=1.0, travel_min=2.0))
    return MetroGraph(stations=stations, lines=lines, nodes=nodes, edges=edges)


def make_graph() -> MetroGraph:
    #   A@RED ------ B@RED ------ C@RED
    #     |                         |
    #   change                    change
    #     |                         |
    #   A@BLUE ----------------- C@BLUE ------ D@BLUE        E@GREEN ------ F@GREEN
    return build(
        ("RED_01", "A@RED", "B@RED"),
        ("RED_02", "B@RED", "C@RED"),
        ("BLUE_01", "A@BLUE", "C@BLUE"),
        ("BLUE_02", "C@BLUE", "D@BLUE"),
        ("WALK_A", "A@RED", "A@BLUE"),
        ("WALK_C", "C@RED", "C@BLUE"),
        ("GREEN_01", "E@GREEN", "F@GREEN"),
    )


def rides(graph: MetroGraph, edge_ids: list[str]) -> int:
    #counts the train rides in a route
    return sum(graph.edge(edge_id).kind == "ride" for edge_id in edge_ids)


def test_picks_route_with_fewest_rides():
    #one ride on blue beats two rides on red
    assert zero_one_bfs(make_graph(), "A", "C") == ["BLUE_01"]


def test_two_rides_on_one_line():
    assert zero_one_bfs(make_graph(), "A", "D") == ["BLUE_01", "BLUE_02"]


def test_route_with_line_change():
    #B to D needs a change at C; going back through A would take one more ride
    assert zero_one_bfs(make_graph(), "B", "D") == ["RED_02", "WALK_C", "BLUE_02"]


def test_reverse_trip_uses_same_edges_backwards():
    assert zero_one_bfs(make_graph(), "D", "B") == ["BLUE_02", "WALK_C", "RED_02"]


def test_line_changes_do_not_count_as_stations():
    #top route: 2 rides and 2 line changes. bottom route: 3 rides and no change.
    #the top route passes through fewer stations, so it must win even though it has more steps.
    #
    #   S@R ---- X@R ~change~ X@B ~change~ X@G ---- T@G
    #   S@P ---- Y@P ---------- Z@P --------------- T@P
    graph = build(
        ("P_01", "S@P", "Y@P"),
        ("P_02", "Y@P", "Z@P"),
        ("P_03", "Z@P", "T@P"),
        ("R_01", "S@R", "X@R"),
        ("WALK_X_RB", "X@R", "X@B"),
        ("WALK_X_BG", "X@B", "X@G"),
        ("G_01", "X@G", "T@G"),
    )
    assert zero_one_bfs(graph, "S", "T") == ["R_01", "WALK_X_RB", "WALK_X_BG", "G_01"]


def test_unreachable_station_returns_none():
    assert zero_one_bfs(make_graph(), "A", "E") is None


def test_same_station_returns_empty_path():
    assert zero_one_bfs(make_graph(), "A", "A") == []


def test_unknown_station_raises_key_error():
    with pytest.raises(KeyError):
        zero_one_bfs(make_graph(), "A", "NOWHERE")
    with pytest.raises(KeyError):
        zero_one_bfs(make_graph(), "NOWHERE", "A")


# --- real data ---------------------------------------------------------------

def test_real_chandni_chowk_to_rajiv_chowk():
    graph = load_graph()
    path = zero_one_bfs(graph, "CHANDNI_CHOWK", "RAJIV_CHOWK")
    assert rides(graph, path) == 3
    assert len(path) == 3


def test_real_new_delhi_to_ito():
    #via rajiv chowk and mandi house: 4 rides and 2 line changes, 18 minutes
    #(the fastest route takes 17 minutes but has 6 rides)
    graph = load_graph()
    path = zero_one_bfs(graph, "NEW_DELHI", "ITO")
    assert rides(graph, path) == 4
    assert len(path) - rides(graph, path) == 2
    assert sum(graph.edge(edge_id).travel_min for edge_id in path) == 18.0
