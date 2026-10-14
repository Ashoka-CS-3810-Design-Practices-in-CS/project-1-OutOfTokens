"""Turn the downloaded OpenStreetMap shapes into a small basemap JSON for the frontend.

Usage: python scripts/build_basemap.py <geo_dir> src/data/delhiBasemap.json

<geo_dir> holds the raw shapes, downloaded from Nominatim
(https://nominatim.openstreetmap.org/search?q=<place>&polygon_geojson=1&format=json&polygon_threshold=0.0003):
  DelhiIndia.json                 q="Delhi, India"
  GurugramHaryana.json            q="Gurugram, Haryana"
  Faridabaddistrict.json          q="Faridabad district"
  GautamBuddhaNagardistrict.json  q="Gautam Buddha Nagar district"
  Ghaziabaddistrict.json          q="Ghaziabad district"
  yamuna_geo.json                 the "geojson" field of OSM relation 326077 (q="Yamuna")
  hindon_geo.json                 the "geojson" field of the first result for q="Hindon River"

Only needed if the background map has to be rebuilt; the app reads the output JSON.
"""
import json
import sys
from pathlib import Path

geo = Path(sys.argv[1])
out = Path(sys.argv[2])

# Area the map shows (a little bigger than the stations' extent).
LAT_MIN, LAT_MAX = 28.20, 28.95
LON_MIN, LON_MAX = 76.75, 77.70
TOLERANCE = 0.0006  # degrees, ~60 m


def load_nominatim(name, want):
    for item in json.load(open(geo / name, encoding="utf8")):
        if want(item):
            return item["geojson"]
    raise SystemExit(f"nothing matched in {name}")


def simplify(points, tol):
    """Douglas-Peucker line simplification."""
    if len(points) < 3:
        return points
    (x1, y1), (x2, y2) = points[0], points[-1]
    dx, dy = x2 - x1, y2 - y1
    norm = (dx * dx + dy * dy) ** 0.5
    best, idx = 0.0, 0
    for i in range(1, len(points) - 1):
        px, py = points[i]
        if norm == 0:
            d = ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        else:
            d = abs(dy * px - dx * py + x2 * y1 - y2 * x1) / norm
        if d > best:
            best, idx = d, i
    if best <= tol:
        return [points[0], points[-1]]
    return simplify(points[: idx + 1], tol)[:-1] + simplify(points[idx:], tol)


def inside(p, pad=0.05):
    lon, lat = p
    return LON_MIN - pad <= lon <= LON_MAX + pad and LAT_MIN - pad <= lat <= LAT_MAX + pad


def clip_line(points):
    """Split a line into the runs of points that fall inside the map area."""
    runs, current = [], []
    for p in points:
        if inside(p):
            current.append(p)
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    return [r for r in runs if len(r) > 1]


def rnd(points):
    return [[round(lon, 4), round(lat, 4)] for lon, lat in points]


def outer_rings(geometry):
    if geometry["type"] == "Polygon":
        return [geometry["coordinates"][0]]
    return [poly[0] for poly in geometry["coordinates"]]


def lines(geometry):
    if geometry["type"] == "LineString":
        return [geometry["coordinates"]]
    return geometry["coordinates"]


def region(name, file, want):
    g = load_nominatim(file, want)
    rings = [rnd(simplify(r, TOLERANCE)) for r in outer_rings(g)]
    return {"name": name, "rings": [r for r in rings if len(r) > 3]}


def river(name, file):
    g = json.load(open(geo / file, encoding="utf8"))
    parts = []
    for line in lines(g):
        for run in clip_line(line):
            parts.append(rnd(simplify(run, TOLERANCE / 2)))
    return {"name": name, "lines": parts}


basemap = {
    "source": "© OpenStreetMap contributors (ODbL)",
    "delhi": region("Delhi", "DelhiIndia.json", lambda x: x["addresstype"] == "state"),
    "neighbours": [
        region("Gurugram", "GurugramHaryana.json", lambda x: x["geojson"]["type"] != "Point"),
        region("Faridabad", "Faridabaddistrict.json", lambda x: True),
        region("Noida", "GautamBuddhaNagardistrict.json", lambda x: True),
        region("Ghaziabad", "Ghaziabaddistrict.json", lambda x: x["boundingbox"][0].startswith("28")),
    ],
    "rivers": [river("Yamuna", "yamuna_geo.json"), river("Hindon", "hindon_geo.json")],
}

out.write_text(json.dumps(basemap, separators=(",", ":")), encoding="utf8")
points = sum(len(r) for x in [basemap["delhi"], *basemap["neighbours"]] for r in x["rings"])
points += sum(len(l) for r in basemap["rivers"] for l in r["lines"])
print(f"wrote {out} ({out.stat().st_size // 1024} KB, {points} points)")
