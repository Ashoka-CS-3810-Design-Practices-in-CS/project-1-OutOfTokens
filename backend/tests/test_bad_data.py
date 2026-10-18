import shutil
from pathlib import Path

import pytest

from metro.network.graph import GraphError
from metro.network.loader import DEFAULT_DATA_DIR, load_graph
from metro.network.models import Edge, Line, Node
from test_graph import make_edges, make_graph, make_lines, make_nodes

# Uses the small hand-built network from test_graph.py.


def ride(edge_id: str, line_id: str | None, a: str, b: str, minutes: float = 2.0, km: float = 1.0) -> Edge:
    return Edge(edge_id=edge_id, line_id=line_id, from_node=a, to_node=b,
                kind="ride", distance_km=km, travel_min=minutes)


def walk(edge_id: str, a: str, b: str) -> Edge:
    return Edge(edge_id=edge_id, line_id=None, from_node=a, to_node=b,
                kind="walk", distance_km=0.0, travel_min=5.0)


# --- the network refuses inconsistent data -----------------------------------

def test_duplicate_line_id_raises():
    lines = make_lines() + [Line(id="RED", name="Another Red", colour="#AA0000")]
    with pytest.raises(GraphError, match="Duplicate line id: RED"):
        make_graph(lines=lines)


def test_duplicate_node_id_raises():
    nodes = make_nodes() + [Node(node_id="A@RED", station_id="A", line_id="RED")]
    with pytest.raises(GraphError, match="Duplicate node id: A@RED"):
        make_graph(nodes=nodes)


def test_node_at_unknown_station_raises():
    nodes = make_nodes() + [Node(node_id="Z@RED", station_id="Z", line_id="RED")]
    with pytest.raises(GraphError, match="unknown station id: Z"):
        make_graph(nodes=nodes)


def test_node_on_unknown_line_raises():
    nodes = make_nodes() + [Node(node_id="A@PINK", station_id="A", line_id="PINK")]
    with pytest.raises(GraphError, match="unknown line id: PINK"):
        make_graph(nodes=nodes)


def test_duplicate_edge_id_raises():
    edges = make_edges() + [ride("RED_01", "RED", "A@RED", "B@RED")]
    with pytest.raises(GraphError, match="Duplicate edge id: RED_01"):
        make_graph(edges=edges)


def test_ride_without_line_raises():
    edges = make_edges() + [ride("RED_09", None, "A@RED", "B@RED")]
    with pytest.raises(GraphError, match="must have a line_id"):
        make_graph(edges=edges)


def test_ride_joining_two_lines_raises():
    # changing line needs a walk edge, not a ride
    edges = make_edges() + [ride("RED_09", "RED", "A@RED", "B@BLUE")]
    with pytest.raises(GraphError, match="connects nodes on different lines"):
        make_graph(edges=edges)


def test_walk_between_two_stations_raises():
    # a line change stays inside one station
    edges = make_edges() + [walk("WALK_X", "A@RED", "C@BLUE")]
    with pytest.raises(GraphError, match="connects nodes at different stations"):
        make_graph(edges=edges)


@pytest.mark.parametrize(
    "minutes, km",
    [(0.0, 1.0), (-2.0, 1.0), (2.0, -0.5)],
    ids=["zero minutes", "negative minutes", "negative distance"],
)
def test_impossible_time_or_distance_raises(minutes: float, km: float):
    edges = make_edges() + [ride("RED_09", "RED", "A@RED", "B@RED", minutes=minutes, km=km)]
    with pytest.raises(GraphError, match="invalid travel time or distance"):
        make_graph(edges=edges)


# --- looking up an id that doesn't exist -------------------------------------

def test_unknown_line_lookup_raises():
    with pytest.raises(KeyError, match="Unknown line id: PINK"):
        make_graph().line("PINK")


def test_unknown_node_lookup_raises():
    with pytest.raises(KeyError, match="Unknown node id: Z@RED"):
        make_graph().node("Z@RED")


def test_unknown_edge_lookup_raises():
    with pytest.raises(KeyError, match="Unknown edge id: NOPE"):
        make_graph().edge("NOPE")


# --- the loader refuses an empty required value ------------------------------

def test_empty_station_name_reports_file_and_line(tmp_path: Path):
    for f in DEFAULT_DATA_DIR.glob("*.csv"):
        shutil.copy(f, tmp_path / f.name)
    path = tmp_path / "stations.csv"
    rows = path.read_text(encoding="utf-8").splitlines()
    station_id, _name, *rest = rows[1].split(",")
    rows[1] = ",".join([station_id, "", *rest])
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    with pytest.raises(GraphError, match=r"stations\.csv line 2: 'name' is empty"):
        load_graph(tmp_path)
