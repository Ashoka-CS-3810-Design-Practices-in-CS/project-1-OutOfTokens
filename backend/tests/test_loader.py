import shutil
from pathlib import Path

import pytest

from metro.network.graph import GraphError
from metro.network.loader import DEFAULT_DATA_DIR, load_graph


@pytest.fixture
def data_copy(tmp_path: Path) -> Path:
    """A throwaway copy of the real data that a test can break."""
    for f in DEFAULT_DATA_DIR.glob("*.csv"):
        shutil.copy(f, tmp_path / f.name)
    return tmp_path


def _append(path: Path, line: str) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text + line + "\n", encoding="utf-8")


def test_real_data_loads_with_expected_counts():
    graph = load_graph()
    assert repr(graph) == "MetroGraph(stations=257, lines=13, nodes=285, edges=301)"


def test_interchange_has_one_node_per_line():
    graph = load_graph()
    lines = {graph.node(n).line_id for n in graph.nodes_for_station("RAJIV_CHOWK")}
    assert lines == {"YELLOW", "BLUE"}


def test_walk_edges_have_no_line_id():
    graph = load_graph()
    walk = [e for n in graph.nodes_for_station("RAJIV_CHOWK") for e in graph.neighbours(n) if e.kind == "walk"]
    assert walk
    assert all(e.line_id is None for e in walk)


def test_accepts_string_path():
    assert repr(load_graph(str(DEFAULT_DATA_DIR))) == repr(load_graph())


def test_duplicate_station_id_raises(data_copy: Path):
    _append(data_copy / "stations.csv", "RAJIV_CHOWK,Rajiv Chowk Again,,28.6,77.2")
    with pytest.raises(GraphError, match="Duplicate station id: RAJIV_CHOWK"):
        load_graph(data_copy)


def test_bad_number_reports_file_and_line(data_copy: Path):
    path = data_copy / "edges.csv"
    lines = path.read_text(encoding="utf-8").splitlines()
    lines[1] = lines[1].replace(",1,2", ",abc,2", 1)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(GraphError, match=r"edges\.csv line 2: 'distance_km' is not a number"):
        load_graph(data_copy)


def test_unknown_edge_kind_raises(data_copy: Path):
    _append(data_copy / "edges.csv", "BAD_01,A@RED,B@RED,teleport,RED,1,2")
    with pytest.raises(GraphError, match="kind must be 'ride' or 'walk'"):
        load_graph(data_copy)


def test_missing_file_raises(data_copy: Path):
    (data_copy / "nodes.csv").unlink()
    with pytest.raises(GraphError, match="Missing data file"):
        load_graph(data_copy)


def test_missing_column_raises(data_copy: Path):
    path = data_copy / "lines.csv"
    text = path.read_text(encoding="utf-8").replace("colour", "color", 1)
    path.write_text(text, encoding="utf-8")
    with pytest.raises(GraphError, match=r"lines\.csv: missing column\(s\) \['colour'\]"):
        load_graph(data_copy)
