import pytest

from metro.network.graph import MetroGraph
from metro.network.loader import load_graph
from metro.network.models import Edge, Line, Node, Station
from metro.routing.planner import Planner


def make_graph() -> MetroGraph:
    #same small map as in test_dijkstra.py (minutes on each edge):
    #
    #   A@RED --2-- B@RED --2-- C@RED
    #     |                       |
    #   walk 5                  walk 5
    #     |                       |
    #   A@BLUE -------10------- C@BLUE --3-- D@BLUE        E@GREEN (no edges)
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


def test_all_three_find_the_same_route():
    #only one sensible way from A to B, so one route with all three labels
    routes = Planner(make_graph()).plan("A", "B")
    assert len(routes) == 1
    assert routes[0].criteria == ("fastest", "fewest_interchanges", "fewest_stations")
    assert routes[0].edge_ids == ("RED_01",)


def test_two_routes_when_one_search_disagrees():
    #A to C: red is fastest and has no change, blue passes through fewer stations
    routes = Planner(make_graph()).plan("A", "C")
    assert len(routes) == 2
    assert routes[0].criteria == ("fastest", "fewest_interchanges")
    assert routes[0].edge_ids == ("RED_01", "RED_02")
    assert routes[1].criteria == ("fewest_stations",)
    assert routes[1].edge_ids == ("BLUE_01",)


def test_fastest_route_differs_from_the_other_two():
    #A to D: changing at C is fastest (12 min); blue all the way has no change and fewer stations
    routes = Planner(make_graph()).plan("A", "D")
    assert len(routes) == 2
    assert routes[0].criteria == ("fastest",)
    assert routes[0].total_time_min == 12.0
    assert routes[0].interchanges == ("C",)
    assert routes[1].criteria == ("fewest_interchanges", "fewest_stations")
    assert routes[1].stations == ("A", "C", "D")
    assert routes[1].total_time_min == 13.0


def test_no_route_gives_empty_list():
    assert Planner(make_graph()).plan("A", "E") == []


def test_same_station_gives_one_empty_route():
    #the service layer will refuse this before it gets here, but the planner should not break
    routes = Planner(make_graph()).plan("A", "A")
    assert len(routes) == 1
    assert routes[0].stations == ("A",)
    assert routes[0].criteria == ("fastest", "fewest_interchanges", "fewest_stations")


def test_unknown_station_raises_key_error():
    with pytest.raises(KeyError):
        Planner(make_graph()).plan("A", "NOWHERE")


# --- real data ---------------------------------------------------------------

def test_real_new_delhi_to_ito():
    routes = Planner(load_graph()).plan("NEW_DELHI", "ITO")
    assert len(routes) == 2

    fastest = routes[0]
    assert fastest.criteria == ("fastest", "fewest_interchanges")
    assert fastest.interchanges == ("CENTRAL_SECRETARIAT",)
    assert fastest.total_time_min == 17.0
    assert fastest.total_distance_km == pytest.approx(6.8)

    fewest_stations = routes[1]
    assert fewest_stations.criteria == ("fewest_stations",)
    assert fewest_stations.interchanges == ("RAJIV_CHOWK", "MANDI_HOUSE")
    assert fewest_stations.total_time_min == 18.0
    assert fewest_stations.total_distance_km == pytest.approx(3.6)


def test_real_chandni_chowk_to_rajiv_chowk():
    #straight down the yellow line: all three agree
    routes = Planner(load_graph()).plan("CHANDNI_CHOWK", "RAJIV_CHOWK")
    assert len(routes) == 1
    assert routes[0].criteria == ("fastest", "fewest_interchanges", "fewest_stations")
    assert len(routes[0].stations) == 4
    assert routes[0].total_time_min == 6.0
