from typing import Protocol

from ..network.models import Edge


class CostModel(Protocol):
    #assigns a cost to each edge in the graph

    def edge_cost(self, edge: Edge) -> float: ...


class TimeCost:
    #fastest route, cost is travel time in minutes

    def edge_cost(self, edge: Edge) -> float:
        return edge.travel_min
