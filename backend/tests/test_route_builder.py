import pytest

from metro.network.graph import MetroGraph
from metro.network.loader import load_graph
from metro.network.models import Edge, Line, Node, Station
from metro.routing.cost_models import TimeCost
from metro.routing.dijkstra import dijkstra
from metro.routing.route_builder import build_route
from metro.routing.zero_one_bfs import zero_one_bfs


def make_graph() -> MetroGraph:
    #same small map as in test_dijkstra.py (minutes / km on each edge):
    #
    #   A@RED --2 min, 1 km-- B@RED --2 min, 1 km-- C@RED
    #     |                                           |
    #   change 5 min                             change 5 min
    #     |                                           |
    #   A@BLUE -----------10 min, 5 km----------- C@BLUE --3 min, 1.5 km-- D@BLUE
    stations = [Station(id=s, name=s, lat=0.0, lon=float(i)) for i, s in enumerate("ABCD")]
    lines = [
        Line(id="RED", name="Red Line", colour="#FF0000"),
        Line(id="BLUE", name="Blue Line", colour="#0000FF"),
    ]
    nodes = [
        Node(node_id="A@RED", station_id="A", line_id="RED"),
        Node(node_id="B@RED", station_id="B", line_id="RED"),
        Node(node_id="C@RED", station_id="C", line_id="RED"),
        Node(node_id="A@BLUE", station_id="A", line_id="BLUE"),
        Node(node_id="C@BLUE", station_id="C", line_id="BLUE"),
        Node(node_id="D@BLUE", station_id="D", line_id="BLUE"),
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


def test_route_on_one_line():
    route = build_route(make_graph(), ("fastest",), "A", ["RED_01", "RED_02"])
    assert route.stations == ("A", "B", "C")
    assert route.lines == ("RED",)
    assert route.interchanges == ()
    assert route.total_time_min == 4.0
    assert route.total_distance_km == 2.0


def test_route_with_line_change():
    route = build_route(make_graph(), ("fastest",), "A", ["RED_01", "RED_02", "WALK_C", "BLUE_02"])
    assert route.stations == ("A", "B", "C", "D")  # C appears once, the change does not add a station
    assert route.lines == ("RED", "BLUE")
    assert route.interchanges == ("C",)
    assert route.total_time_min == 12.0            # 2 + 2 + 5 + 3, the change counts its minutes
    assert route.total_distance_km == 3.5          # 1 + 1 + 0 + 1.5, the change adds no distance


def test_reverse_route_follows_edges_backwards():
    #every edge here is written in the csv pointing the other way
    route = build_route(make_graph(), ("fastest",), "D", ["BLUE_02", "WALK_C", "RED_02", "RED_01"])
    assert route.stations == ("D", "C", "B", "A")
    assert route.lines == ("BLUE", "RED")
    assert route.interchanges == ("C",)


def test_criteria_and_edge_ids_are_kept():
    route = build_route(make_graph(), ("fastest", "fewest_interchanges"), "A", ["BLUE_01"])
    assert route.criteria == ("fastest", "fewest_interchanges")
    assert route.edge_ids == ("BLUE_01",)


def test_empty_route_is_just_the_start_station():
    route = build_route(make_graph(), ("fastest",), "A", [])
    assert route.stations == ("A",)
    assert route.lines == ()
    assert route.interchanges == ()
    assert route.total_time_min == 0.0
    assert route.total_distance_km == 0.0


def test_result_holds_tuples_not_lists():
    #the route is frozen, so its contents must not be changeable either
    route = build_route(make_graph(), ("fastest",), "A", ["RED_01"])
    assert isinstance(route.stations, tuple)
    assert isinstance(route.lines, tuple)
    assert isinstance(route.interchanges, tuple)


def test_first_edge_not_at_source_raises():
    with pytest.raises(ValueError):
        build_route(make_graph(), ("fastest",), "A", ["RED_02"])


def test_edges_that_do_not_join_up_raise():
    with pytest.raises(ValueError):
        build_route(make_graph(), ("fastest",), "A", ["RED_01", "BLUE_02"])


# --- real data ---------------------------------------------------------------

def test_real_new_delhi_to_ito_fastest():
    graph = load_graph()
    route = build_route(graph, ("fastest",), "NEW_DELHI", dijkstra(graph, TimeCost(), "NEW_DELHI", "ITO"))
    assert len(route.stations) == 7
    assert route.stations[0] == "NEW_DELHI"
    assert route.stations[-1] == "ITO"
    assert route.lines == ("YELLOW", "VIOLET")
    assert route.interchanges == ("CENTRAL_SECRETARIAT",)
    assert route.total_time_min == 17.0
    assert route.total_distance_km == pytest.approx(6.8)


def test_real_new_delhi_to_ito_fewest_stations():
    graph = load_graph()
    route = build_route(graph, ("fewest_stations",), "NEW_DELHI", zero_one_bfs(graph, "NEW_DELHI", "ITO"))
    assert len(route.stations) == 5
    assert route.lines == ("YELLOW", "BLUE", "VIOLET")
    assert route.interchanges == ("RAJIV_CHOWK", "MANDI_HOUSE")
    assert route.total_time_min == 18.0
    assert route.total_distance_km == pytest.approx(3.6)


def test_real_chandni_chowk_to_rajiv_chowk():
    graph = load_graph()
    route = build_route(graph, ("fastest",), "CHANDNI_CHOWK",
                        dijkstra(graph, TimeCost(), "CHANDNI_CHOWK", "RAJIV_CHOWK"))
    assert len(route.stations) == 4
    assert route.lines == ("YELLOW",)
    assert route.interchanges == ()
    assert route.total_time_min == 6.0
    assert route.total_distance_km == pytest.approx(2.9)
