from fastapi.testclient import TestClient

from metro.api.main import app

client = TestClient(app)


def test_network_returns_every_station_line_and_ride_edge():
    response = client.get("/api/network")
    assert response.status_code == 200
    body = response.json()
    assert len(body["stations"]) == 257
    assert len(body["lines"]) == 13
    assert len(body["edges"]) == 272  # rides only, the 29 walks are left out


def test_station_has_coordinates_and_its_lines():
    body = client.get("/api/network").json()
    rajiv = next(s for s in body["stations"] if s["id"] == "RAJIV_CHOWK")
    assert rajiv["name"] == "Rajiv Chowk"
    assert 28 < rajiv["lat"] < 29 and 76 < rajiv["lon"] < 78
    assert sorted(rajiv["lines"]) == ["BLUE", "YELLOW"]


def test_edges_use_station_ids_that_exist():
    body = client.get("/api/network").json()
    station_ids = {s["id"] for s in body["stations"]}
    line_ids = {line["id"] for line in body["lines"]}
    for edge in body["edges"]:
        assert edge["from_id"] in station_ids
        assert edge["to_id"] in station_ids
        assert edge["line_id"] in line_ids


def test_cors_allows_the_vite_dev_server():
    response = client.get("/api/network", headers={"Origin": "http://localhost:5173"})
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
