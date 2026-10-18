import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from metro.network.loader import DEFAULT_DATA_DIR, load_graph
from metro.network.models import Edge, Line, Node, Station
from metro.network.validator import DataError, validate
from test_graph import make_edges, make_graph, make_lines, make_nodes, make_stations


def without(edges: list[Edge], edge_id: str) -> list[Edge]:
    return [edge for edge in edges if edge.edge_id != edge_id]


def problems(graph) -> list[str]:
    with pytest.raises(DataError) as error:
        validate(graph)
    return error.value.problems


def test_real_data_passes():
    validate(load_graph())


def test_small_network_passes():
    validate(make_graph())


def test_walk_edge_with_distance_is_reported():
    edges = [replace(e, distance_km=0.3) if e.edge_id == "WALK_B" else e for e in make_edges()]
    assert problems(make_graph(edges=edges)) == [
        "Walk edge WALK_B has distance 0.3 km; a line change must be 0 km"
    ]


def test_missing_walk_edge_is_reported():
    # B has a red and a blue platform but nothing joins them, which also cuts off B@BLUE and C
    found = problems(make_graph(edges=without(make_edges(), "WALK_B")))
    assert "Station B has no walk edge between B@RED and B@BLUE" in found


def test_every_problem_is_reported_at_once():
    found = problems(make_graph(edges=without(make_edges(), "WALK_B")))
    assert len(found) == 2
    assert found[1] == "2 node(s) can't be reached from A@RED: B@BLUE, C@BLUE"


def test_separate_line_is_reported():
    # D-E on a green line that never meets the rest
    stations = make_stations() + [Station(id=s, name=s, lat=0.0, lon=0.0) for s in "DE"]
    lines = make_lines() + [Line(id="GREEN", name="Green Line", colour="#00FF00")]
    nodes = make_nodes() + [Node(node_id=f"{s}@GREEN", station_id=s, line_id="GREEN") for s in "DE"]
    edges = make_edges() + [Edge(edge_id="GREEN_01", line_id="GREEN", from_node="D@GREEN", to_node="E@GREEN",
                                 kind="ride", distance_km=1.0, travel_min=2.0)]
    graph = make_graph(stations=stations, lines=lines, nodes=nodes, edges=edges)
    assert problems(graph) == ["2 node(s) can't be reached from A@RED: D@GREEN, E@GREEN"]


def test_real_interchange_missing_one_walk_is_reported(tmp_path: Path):
    # Kashmere Gate stays connected through its other two walk edges, so only the missing pair is reported
    for f in DEFAULT_DATA_DIR.glob("*.csv"):
        shutil.copy(f, tmp_path / f.name)
    path = tmp_path / "edges.csv"
    rows = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(r for r in rows if not r.startswith("WALK_KASHMERE_GATE_RED_VIOLET,")) + "\n",
                    encoding="utf-8")
    assert problems(load_graph(tmp_path)) == [
        "Station KASHMERE_GATE has no walk edge between KASHMERE_GATE@RED and KASHMERE_GATE@VIOLET"
    ]


def test_error_message_lists_every_problem():
    with pytest.raises(DataError, match=r"(?s)Network data has problems:\n- Station B .*\n- 2 node\(s\)"):
        validate(make_graph(edges=without(make_edges(), "WALK_B")))
