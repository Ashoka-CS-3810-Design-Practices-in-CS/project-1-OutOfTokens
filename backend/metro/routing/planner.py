from ..network.graph import MetroGraph
from ..network.models import RouteResult
from .cost_models import InterchangePenaltyCost, TimeCost
from .dijkstra import dijkstra
from .route_builder import build_route
from .zero_one_bfs import zero_one_bfs


class Planner:
    # runs all three searches and gives back each different route once

    def __init__(self, graph: MetroGraph) -> None:
        self.graph = graph

    def plan(self, source_station: str, dest_station: str) -> list[RouteResult]:
        # returns the routes from source to destination, an empty list if there is no route

        # step 1: one search per criterion. each gives a list of edge ids, or None if there is no route
        found: dict[str, list[str] | None] = {
            "fastest": dijkstra(self.graph, TimeCost(), source_station, dest_station),
            "fewest_interchanges": dijkstra(self.graph, InterchangePenaltyCost(), source_station, dest_station),
            "fewest_stations": zero_one_bfs(self.graph, source_station, dest_station),
        }

        # step 2: put identical routes together
        groups: dict[tuple[str, ...], list[str]] = {}   # edge ids of a route -> the criteria that found it

        for criterion, edge_ids in found.items():
            if edge_ids == None:
                continue
            
        for criterion, edge_ids in found.items():
            if edge_ids is None: # no route for this criterion
                continue
            key = tuple(edge_ids) 
            if key not in groups:
                groups[key] = [criterion] # first search to find this route
            else:
                groups[key].append(criterion) # same route as an earlier search, add the label

        # step 3: build one readable route for each group
        return [
            build_route(self.graph, tuple(criteria), source_station, list(key))
            for key, criteria in groups.items()
        ]
