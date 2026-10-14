import json

import pytest

from metro.network.graph import MetroGraph
from metro.network.loader import load_graph
from metro.network.models import Edge, Line, Node, Station
from metro.service.route_service import RouteError, RouteService


@pytest.fixture(scope="module")
def service() -> RouteService:
    #one service on the real data, shared by the tests in this file
    return RouteService(load_graph())


def make_split_graph() -> MetroGraph:
    #two lines that never meet, so there is no route from A to C
    #   A@RED ---- B@RED        C@BLUE ---- D@BLUE
    stations = [Station(id=s, name=s, lat=0.0, lon=float(i)) for i, s in enumerate("ABCD")]
    lines = [
        Line(id="RED", name="Red Line", colour="#FF0000"),
        Line(id="BLUE", name="Blue Line", colour="#0000FF"),
    ]
    nodes = [
        Node(node_id="A@RED", station_id="A", line_id="RED"),
        Node(node_id="B@RED", station_id="B", line_id="RED"),
        Node(node_id="C@BLUE", station_id="C", line_id="BLUE"),
        Node(node_id="D@BLUE", station_id="D", line_id="BLUE"),
    ]
    edges = [
        Edge(edge_id="RED_01", line_id="RED", from_node="A@RED", to_node="B@RED",
             kind="ride", distance_km=1.0, travel_min=2.0),
        Edge(edge_id="BLUE_01", line_id="BLUE", from_node="C@BLUE", to_node="D@BLUE",
             kind="ride", distance_km=1.0, travel_min=2.0),
    ]
    return MetroGraph(stations=stations, lines=lines, nodes=nodes, edges=edges)


# --- find_routes -------------------------------------------------------------

def test_new_delhi_to_ito(service: RouteService):
    result = service.find_routes("NEW_DELHI", "ITO")
    assert result["status"] == "ok"
    assert len(result["routes"]) == 2
    fastest = result["routes"][0]
    assert list(fastest["criteria"]) == ["fastest", "fewest_interchanges"]
    assert fastest["total_time_min"] == 17.0
    assert list(fastest["interchanges"]) == ["CENTRAL_SECRETARIAT"]


def test_routes_have_every_field_the_panel_needs(service: RouteService):
    route = service.find_routes("NEW_DELHI", "ITO")["routes"][0]
    assert set(route) == {
        "stations", "criteria", "edge_ids", "lines", "interchanges",
        "total_time_min", "total_distance_km",
    }


def test_answer_can_be_turned_into_json(service: RouteService):
    #the api sends this straight back to the browser
    text = json.dumps(service.find_routes("NEW_DELHI", "ITO"))
    assert json.loads(text)["routes"][0]["stations"][0] == "NEW_DELHI"


def test_unknown_source_is_refused(service: RouteService):
    with pytest.raises(RouteError) as error:
        service.find_routes("NOWHERE", "ITO")
    assert error.value.code == "unknown_station"


def test_unknown_destination_is_refused(service: RouteService):
    with pytest.raises(RouteError) as error:
        service.find_routes("ITO", "NOWHERE")
    assert error.value.code == "unknown_station"


def test_station_names_are_not_ids(service: RouteService):
    #the frontend must send ids like "NEW_DELHI", not names like "New Delhi"
    with pytest.raises(RouteError) as error:
        service.find_routes("New Delhi", "ITO")
    assert error.value.code == "unknown_station"


def test_same_station_is_refused(service: RouteService):
    with pytest.raises(RouteError) as error:
        service.find_routes("ITO", "ITO")
    assert error.value.code == "same_station"


def test_unknown_is_reported_before_same(service: RouteService):
    with pytest.raises(RouteError) as error:
        service.find_routes("NOWHERE", "NOWHERE")
    assert error.value.code == "unknown_station"


def test_no_route_gives_no_path():
    result = RouteService(make_split_graph()).find_routes("A", "C")
    assert result == {"status": "no_path", "routes": []}


# --- network_view ------------------------------------------------------------

def test_network_view_counts(service: RouteService):
    view = service.network_view()
    assert len(view["stations"]) == 257
    assert len(view["lines"]) == 13
    assert len(view["edges"]) == 272   # ride edges only, the 29 line changes are left out


def test_network_view_edges_use_station_ids(service: RouteService):
    view = service.network_view()
    station_ids = {station["id"] for station in view["stations"]}
    for edge in view["edges"]:
        assert edge["from_id"] in station_ids
        assert edge["to_id"] in station_ids
        assert edge["line_id"] is not None


def test_network_view_lists_lines_at_each_station(service: RouteService):
    stations = {station["id"]: station for station in service.network_view()["stations"]}
    assert set(stations["RAJIV_CHOWK"]["lines"]) == {"YELLOW", "BLUE"}
    assert set(stations["KASHMERE_GATE"]["lines"]) == {"RED", "YELLOW", "VIOLET"}
    assert stations["ITO"]["lines"] == ["VIOLET"]


def test_network_view_can_be_turned_into_json(service: RouteService):
    json.dumps(service.network_view())
