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


def test_route_new_delhi_to_ito_gives_two_routes():
    response = client.post("/api/route", json={"source": "NEW_DELHI", "destination": "ITO"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    by_criteria = {tuple(r["criteria"]): r for r in body["routes"]}
    assert set(by_criteria) == {("fastest", "fewest_interchanges"), ("fewest_stations",)}
    fastest = by_criteria[("fastest", "fewest_interchanges")]
    assert fastest["total_time_min"] == 17.0
    assert fastest["interchanges"] == ["CENTRAL_SECRETARIAT"]
    assert fastest["stations"][0] == "NEW_DELHI" and fastest["stations"][-1] == "ITO"


def test_route_unknown_station_is_a_400_with_a_plain_message():
    response = client.post("/api/route", json={"source": "NOWHERE", "destination": "ITO"})
    assert response.status_code == 400
    assert response.json()["error"] == "unknown_station"
    assert "recognised" in response.json()["message"]


def test_route_same_station_is_a_400():
    response = client.post("/api/route", json={"source": "ITO", "destination": "ITO"})
    assert response.status_code == 400
    assert response.json()["error"] == "same_station"


def test_route_missing_field_is_a_422():
    response = client.post("/api/route", json={"source": "ITO"})
    assert response.status_code == 422


def test_network_has_a_data_version_and_line_speeds():
    body = client.get("/api/network").json()
    assert len(body["data_version"]) == 16
    assert all(line["avg_speed_kmh"] > 0 for line in body["lines"])
