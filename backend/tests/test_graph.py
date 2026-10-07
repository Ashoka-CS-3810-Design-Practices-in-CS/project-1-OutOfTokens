import pytest

from metro.network.graph import GraphError, MetroGraph
from metro.network.models import Edge, Line, Node, Station


# Small hand-built network:
#
#   A@RED --ride-- B@RED
#                   |
#                  walk
#                   |
#                 B@BLUE --ride-- C@BLUE

def make_stations() -> list[Station]:
    return [
        Station(id="A", name="Alpha", lat=0.0, lon=0.0),
        Station(id="B", name="Bravo Junction", lat=0.0, lon=1.0),
        Station(id="C", name="Charlie", lat=0.0, lon=2.0),
    ]


def make_lines() -> list[Line]:
    return [
        Line(id="RED", name="Red Line", colour="#FF0000"),
        Line(id="BLUE", name="Blue Line", colour="#0000FF"),
    ]


def make_nodes() -> list[Node]:
    return [
        Node(node_id="A@RED", station_id="A", line_id="RED"),
        Node(node_id="B@RED", station_id="B", line_id="RED"),
        Node(node_id="B@BLUE", station_id="B", line_id="BLUE"),
        Node(node_id="C@BLUE", station_id="C", line_id="BLUE"),
    ]


def make_edges() -> list[Edge]:
    return [
        Edge(edge_id="RED_01", line_id="RED", from_node="A@RED", to_node="B@RED",
             kind="ride", distance_km=1.0, travel_min=2.0),
        Edge(edge_id="WALK_B", line_id=None, from_node="B@RED", to_node="B@BLUE",
             kind="walk", distance_km=0.0, travel_min=5.0),
        Edge(edge_id="BLUE_01", line_id="BLUE", from_node="B@BLUE", to_node="C@BLUE",
             kind="ride", distance_km=1.5, travel_min=3.0),
    ]


def make_graph(**overrides) -> MetroGraph:
    parts = {
        "stations": make_stations(),
        "lines": make_lines(),
        "nodes": make_nodes(),
        "edges": make_edges(),
    }
    parts.update(overrides)
    return MetroGraph(**parts)


def test_neighbours_include_both_directions():
    graph = make_graph()

    forward = graph.neighbours("A@RED")
    assert [(e.edge_id, e.to_node) for e in forward] == [("RED_01", "B@RED")]

    backward = {(e.edge_id, e.to_node) for e in graph.neighbours("B@RED")}
    assert backward == {("RED_01", "A@RED"), ("WALK_B", "B@BLUE")}


def test_reverse_edge_keeps_attributes():
    graph = make_graph()
    (reverse,) = [e for e in graph.neighbours("C@BLUE") if e.edge_id == "BLUE_01"]
    assert reverse.from_node == "C@BLUE"
    assert reverse.to_node == "B@BLUE"
    assert reverse.travel_min == 3.0
    assert reverse.line_id == "BLUE"
    # _edges still holds the original direction only
    assert graph.edge("BLUE_01").from_node == "B@BLUE"


def test_nodes_for_station_returns_one_node_per_line():
    graph = make_graph()
    assert set(graph.nodes_for_station("B")) == {"B@RED", "B@BLUE"}
    assert graph.nodes_for_station("A") == ("A@RED",)


def test_lookups_and_listing():
    graph = make_graph()
    assert graph.station("A").name == "Alpha"
    assert graph.line("BLUE").colour == "#0000FF"
    assert graph.node("C@BLUE").station_id == "C"
    assert len(graph.stations) == 3
    assert len(graph.lines) == 2
    assert "B@BLUE" in graph
    assert "B@GREEN" not in graph
    assert repr(graph) == "MetroGraph(stations=3, lines=2, nodes=4, edges=3)"


def test_find_station_by_name_is_case_insensitive():
    graph = make_graph()
    assert graph.find_station_by_name("  bravo JUNCTION ").id == "B"
    assert graph.find_station_by_name("Nowhere") is None


def test_unknown_ids_raise_key_error():
    graph = make_graph()
    with pytest.raises(KeyError, match="Unknown station id"):
        graph.station("Z")
    with pytest.raises(KeyError, match="Unknown node id"):
        graph.neighbours("Z@RED")


def test_duplicate_station_id_raises():
    stations = make_stations() + [Station(id="A", name="Another A", lat=0.0, lon=0.0)]
    with pytest.raises(GraphError, match="Duplicate station id"):
        make_graph(stations=stations)


def test_edge_to_missing_node_raises():
    edges = make_edges() + [
        Edge(edge_id="RED_02", line_id="RED", from_node="B@RED", to_node="MISSING@RED",
             kind="ride", distance_km=1.0, travel_min=2.0),
    ]
    with pytest.raises(GraphError, match="unknown nodes"):
        make_graph(edges=edges)


def test_walk_edge_with_line_id_raises():
    edges = make_edges() + [
        Edge(edge_id="WALK_BAD", line_id="RED", from_node="B@BLUE", to_node="B@RED",
             kind="walk", distance_km=0.0, travel_min=5.0),
    ]
    with pytest.raises(GraphError, match="must have no line_id"):
        make_graph(edges=edges)
