import pytest

#import the necessary classes and functions from the metro package
from metro.network.graph import MetroGraph
from metro.network.loader import load_graph
from metro.network.models import Edge, Line, Node, Station
from metro.routing.cost_models import InterchangePenaltyCost, TimeCost
from metro.routing.dijkstra import dijkstra, trace_path


def make_graph() -> MetroGraph:
    #creates a simple test graph with 5 stations and 3 lines

    stations = [Station(id=s, name=s, lat=0.0, lon=float(i)) for i, s in enumerate("ABCDE")]
    lines = [
        Line(id="RED", name="Red Line", colour="#FF0000"),
        Line(id="BLUE", name="Blue Line", colour="#0000FF"),
        Line(id="GREEN", name="Green Line", colour="#00FF00"),
    ]
    nodes = [
        Node(node_id="A@RED", station_id="A", line_id="RED"),
        Node(node_id="B@RED", station_id="B", line_id="RED"),
        Node(node_id="C@RED", station_id="C", line_id="RED"),
        Node(node_id="A@BLUE", station_id="A", line_id="BLUE"),
        Node(node_id="C@BLUE", station_id="C", line_id="BLUE"),
        Node(node_id="D@BLUE", station_id="D", line_id="BLUE"),
        Node(node_id="E@GREEN", station_id="E", line_id="GREEN"),
    ]
    edges = [
        Edge(edge_id="RED_01", line_id="RED", from_node="A@RED", to_node="B@RED",
             kind="ride", distance_km=1.0, travel_min=2.0),
        Edge(edge_id="RED_02", line_id="RED", from_node="B@RED", to_node="C@RED",
             kind="ride", distance_km=1.0, travel_min=2.0),
        Edge(edge_id="BLUE_01", line_id="BLUE", from_node="A@BLUE", to_node="C@BLUE",
             kind="ride", distance_km=5.0, travel_min=10.0),
        Edge(edge_id="BLUE_02", line_id="BLUE", from_node="C@BLUE", to_node="D@BLUE",
             kind="ride", distance_km=1.5, travel_min=3.0),
        Edge(edge_id="WALK_A", line_id=None, from_node="A@RED", to_node="A@BLUE",
             kind="walk", distance_km=0.0, travel_min=5.0),
        Edge(edge_id="WALK_C", line_id=None, from_node="C@RED", to_node="C@BLUE",
             kind="walk", distance_km=0.0, travel_min=5.0),
    ]
    return MetroGraph(stations=stations, lines=lines, nodes=nodes, edges=edges)


def total_time(graph: MetroGraph, edge_ids: list[str]) -> float: 
    #calculates the total travel time in minutes for a given list of edge ids in the graph
    return sum(graph.edge(edge_id).travel_min for edge_id in edge_ids)


def test_prefers_faster_path_over_fewer_edges():
    assert dijkstra(make_graph(), TimeCost(), "A", "C") == ["RED_01", "RED_02"]


def test_boarding_at_source_is_free():
    # rider starts at A, can board either line for free

    graph = make_graph()
    path = dijkstra(graph, TimeCost(), "A", "B")
    assert path == ["RED_01"]
    assert total_time(graph, path) == 2.0


def test_route_with_interchange_includes_walk_edge():
    #interchange beats direct ride
    graph = make_graph()
    path = dijkstra(graph, TimeCost(), "A", "D")
    assert path == ["RED_01", "RED_02", "WALK_C", "BLUE_02"]
    assert total_time(graph, path) == 12.0


def test_reverse_trip_uses_same_edges_backwards():
    assert dijkstra(make_graph(), TimeCost(), "D", "A") == ["BLUE_02", "WALK_C", "RED_02", "RED_01"]


def test_unreachable_station_returns_none():
    assert dijkstra(make_graph(), TimeCost(), "A", "E") is None


def test_same_station_returns_empty_path():
    assert dijkstra(make_graph(), TimeCost(), "A", "A") == []


def test_unknown_station_raises_key_error():
    with pytest.raises(KeyError):
        dijkstra(make_graph(), TimeCost(), "A", "NOWHERE")
    with pytest.raises(KeyError):
        dijkstra(make_graph(), TimeCost(), "NOWHERE", "A")


def test_trace_path_returns_edges_in_travel_order():
    prev = {"B": ("A", "e1"), "C": ("B", "e2")}
    assert trace_path(prev, "C") == ["e1", "e2"]
    assert trace_path(prev, "A") == []


# --- fewest line changes -----------------------------------------------------

def test_fewest_interchanges_avoids_line_change():
    #blue all the way (13 min, no change) beats red then blue (12 min, 1 change)
    graph = make_graph()
    path = dijkstra(graph, InterchangePenaltyCost(), "A", "D")
    assert path == ["BLUE_01", "BLUE_02"]
    assert total_time(graph, path) == 13.0


def test_fewest_interchanges_still_picks_faster_when_changes_are_equal():
    #both ways need no change, so the faster one wins
    assert dijkstra(make_graph(), InterchangePenaltyCost(), "A", "C") == ["RED_01", "RED_02"]


# --- real data ---------------------------------------------------------------

def test_real_chandni_chowk_to_rajiv_chowk():
    graph = load_graph()
    path = dijkstra(graph, TimeCost(), "CHANDNI_CHOWK", "RAJIV_CHOWK")
    assert len(path) == 3
    assert all(graph.edge(edge_id).line_id == "YELLOW" for edge_id in path)
    assert total_time(graph, path) == 6.0


def test_real_new_delhi_to_ito():
    graph = load_graph()
    path = dijkstra(graph, TimeCost(), "NEW_DELHI", "ITO")
    assert total_time(graph, path) == 17.0
    assert sum(graph.edge(edge_id).kind == "walk" for edge_id in path) == 1


def test_real_new_delhi_to_ito_fewest_interchanges():
    #the fastest route here already has the fewest changes, so both give the same answer
    graph = load_graph()
    path = dijkstra(graph, InterchangePenaltyCost(), "NEW_DELHI", "ITO")
    assert path == dijkstra(graph, TimeCost(), "NEW_DELHI", "ITO")
