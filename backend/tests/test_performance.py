import random
import time

from metro.network.loader import load_graph
from metro.routing.planner import Planner

# Measured 18 Oct 2026: about 0.12 ms per request (three searches).
# The limits are deliberately loose, so the test only fails if something is badly wrong.

REQUEST_LIMIT_MS = 5.0
LOAD_LIMIT_MS = 200.0


def test_loading_the_network_is_quick():
    start = time.perf_counter()
    load_graph()
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < LOAD_LIMIT_MS


def test_route_requests_are_quick():
    graph = load_graph()
    planner = Planner(graph)
    station_ids = [station.id for station in graph.stations]
    pairs = [tuple(random.Random(seed).sample(station_ids, 2)) for seed in range(500)]

    start = time.perf_counter()
    for source, destination in pairs:
        assert planner.plan(source, destination)  # the network is connected, so every pair has a route
    average_ms = (time.perf_counter() - start) * 1000 / len(pairs)

    assert average_ms < REQUEST_LIMIT_MS
