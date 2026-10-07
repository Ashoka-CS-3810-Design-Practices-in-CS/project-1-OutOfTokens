import csv
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TypeVar

from .graph import GraphError, MetroGraph
from .models import Edge, Line, Node, Station

# backend/data, worked out from this file's location so it doesn't depend on
# the current working directory.
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"

T = TypeVar("T")


def load_graph(data_dir: str | Path = DEFAULT_DATA_DIR) -> MetroGraph:
    """Read the four CSVs in `data_dir` and build a MetroGraph.

    Files are read in dependency order (lines, stations, nodes, edges).
    MetroGraph checks duplicate ids and dangling references as it builds, so
    this module only parses the files and converts the types.
    """
    data_dir = Path(data_dir)
    lines = _read(data_dir / "lines.csv", {"id", "name", "colour"}, _parse_line)
    stations = _read(data_dir / "stations.csv", {"id", "name", "lat", "lon"}, _parse_station)
    nodes = _read(data_dir / "nodes.csv", {"node_id", "station_id", "line_id"}, _parse_node)
    edges = _read(
        data_dir / "edges.csv",
        {"edge_id", "from_node", "to_node", "kind", "line_id", "distance_km", "travel_min"},
        _parse_edge,
    )
    return MetroGraph(stations=stations, lines=lines, nodes=nodes, edges=edges)


def _read(path: Path, required: set[str], parse: Callable[[dict[str, str]], T]) -> list[T]:
    """Parse every row of `path`, adding the file and line number to any error."""
    if not path.is_file():
        raise GraphError(f"Missing data file: {path}")
    # utf-8-sig drops the BOM Excel adds; newline="" is what the csv module expects.
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise GraphError(f"{path.name}: missing column(s) {sorted(missing)}")
        items = []
        for row in _rows(reader):
            try:
                items.append(parse(row))
            except (ValueError, TypeError) as exc:
                raise GraphError(f"{path.name} line {reader.line_num}: {exc}") from exc
        return items


def _rows(reader: csv.DictReader) -> Iterator[dict[str, str]]:
    # Strip stray spaces around values and skip completely blank lines.
    for row in reader:
        cleaned = {k: (v or "").strip() for k, v in row.items() if k is not None}
        if any(cleaned.values()):
            yield cleaned


def _parse_line(row: dict[str, str]) -> Line:
    return Line(id=_required(row, "id"), name=_required(row, "name"), colour=_required(row, "colour"))


def _parse_station(row: dict[str, str]) -> Station:
    # stations.csv also has a `code` column, which Station doesn't use.
    return Station(
        id=_required(row, "id"),
        name=_required(row, "name"),
        lat=_float(row, "lat"),
        lon=_float(row, "lon"),
    )


def _parse_node(row: dict[str, str]) -> Node:
    return Node(
        node_id=_required(row, "node_id"),
        station_id=_required(row, "station_id"),
        line_id=_required(row, "line_id"),
    )


def _parse_edge(row: dict[str, str]) -> Edge:
    kind = _required(row, "kind")
    # Literal["ride", "walk"] is only checked by type checkers, so check it at runtime here.
    if kind not in ("ride", "walk"):
        raise ValueError(f"kind must be 'ride' or 'walk', got {kind!r}")
    return Edge(
        edge_id=_required(row, "edge_id"),
        line_id=row["line_id"] or None,  # walk edges leave this column empty
        from_node=_required(row, "from_node"),
        to_node=_required(row, "to_node"),
        kind=kind,
        distance_km=_float(row, "distance_km"),
        travel_min=_float(row, "travel_min"),
    )


def _required(row: dict[str, str], column: str) -> str:
    value = row[column]
    if not value:
        raise ValueError(f"{column!r} is empty")
    return value


def _float(row: dict[str, str], column: str) -> float:
    value = _required(row, column)
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"{column!r} is not a number: {value!r}") from None
